import json
import os
import secrets
from urllib.parse import quote
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from .analyzer import analyze_project
from .database import Base, SessionLocal, engine, get_db
from .models import Scan, User
from .google_oauth import authenticate_callback, authorization_url
from .schemas import AuditResponse, CurrentUserResponse, HealthResponse, LoginRequest, RegisterRequest, ScanRequest, ScanSummary, TokenResponse
from .security import create_access_token, get_current_user, hash_password, require_admin, verify_password

app = FastAPI(
    title="BugSentinel AI API",
    version="0.4.0",
    summary="AI-powered software bug prediction and secure code analysis",
    description="Use this REST API to authenticate users, run explainable source-code scans, retrieve scan history, and integrate Google Sign-In.",
    openapi_tags=[
        {"name": "health", "description": "Service health and availability."},
        {"name": "authentication", "description": "Email/password JWT authentication and Google OAuth."},
        {"name": "scans", "description": "JWT-protected source-code analysis and report history."},
        {"name": "administration", "description": "Administrator-only audit information."},
    ],
)
allowed_hosts = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,api").split(",") if host.strip()]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost", "https://localhost", "http://localhost:3000", "http://localhost:8081"], allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])

@app.middleware("http")
async def add_api_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=()"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "no-cache"
    return response

@app.on_event("startup")
def initialise_database():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "google_id" not in {column["name"] for column in inspector.get_columns("users")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)"))
    db = SessionLocal()
    try:
        for email, password, role in [("admin@example.com", os.getenv("ADMIN_PASSWORD", "ChangeMe123!"), "admin"), ("developer@example.com", os.getenv("DEVELOPER_PASSWORD", "ChangeMe123!"), "developer")]:
            if not db.query(User).filter(User.email == email).first(): db.add(User(email=email, password_hash=hash_password(password), role=role))
        db.commit()
    finally: db.close()

@app.get("/api/v1/health", response_model=HealthResponse, tags=["health"], summary="Check API health")
def health(): return {"status": "healthy", "service": "BugSentinel AI"}

@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["authentication"], summary="Sign in with email and password", responses={401: {"description": "Incorrect email or password"}})
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return TokenResponse(access_token=create_access_token(user.email, user.role), email=user.email, role=user.role)

@app.post("/api/v1/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, tags=["authentication"], summary="Create a developer account", responses={409: {"description": "Account already exists"}, 422: {"description": "Password does not meet policy"}})
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account already exists for this email address")
    user = User(email=email, password_hash=hash_password(payload.password), role="developer")
    db.add(user)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.email, user.role), email=user.email, role=user.role)

@app.get("/api/v1/auth/me", response_model=CurrentUserResponse, tags=["authentication"], summary="Get the current JWT user", responses={401: {"description": "JWT is missing, expired, or invalid"}})
def current_user(user: User = Depends(get_current_user)):
    return CurrentUserResponse(email=user.email, role=user.role)

@app.get("/api/v1/auth/google/login", tags=["authentication"], summary="Start Google Sign-In", response_description="Redirects to Google OAuth")
def google_login():
    return RedirectResponse(authorization_url(), status_code=status.HTTP_302_FOUND)

@app.get("/api/v1/auth/google/callback", tags=["authentication"], summary="Complete Google Sign-In", response_description="Redirects to the frontend with an application JWT")
def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    identity, frontend_url = authenticate_callback(code, state)
    user = db.query(User).filter(User.google_id == identity["google_id"]).first()
    if not user:
        user = db.query(User).filter(User.email == identity["email"]).first()
        if user:
            user.google_id = identity["google_id"]
        else:
            user = User(email=identity["email"], google_id=identity["google_id"], password_hash=hash_password(secrets.token_urlsafe(32)), role="developer")
            db.add(user)
        db.commit()
    token = create_access_token(user.email, user.role)
    return RedirectResponse(f"{frontend_url}/oauth/callback?token={quote(token, safe='')}", status_code=status.HTTP_302_FOUND)

@app.post("/api/v1/scans", tags=["scans"], summary="Analyze source files", description="Runs explainable heuristic bug prediction, code-quality checks, and security-pattern detection. Use Swagger Authorize with a Bearer JWT first.", responses={401: {"description": "JWT is missing, expired, or invalid"}})
def create_scan(payload: ScanRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = analyze_project([item.model_dump() for item in payload.files])
    scan = Scan(repository_name=payload.repository_name, owner_email=user.email, overall_risk=report["overall_risk_level"], risk_score=report["overall_risk_score"], report_json=json.dumps(report))
    db.add(scan); db.commit(); db.refresh(scan)
    return {"id": scan.id, "repository_name": scan.repository_name, "created_at": scan.created_at, **report}

@app.get("/api/v1/scans", response_model=list[ScanSummary], tags=["scans"], summary="List scan history", description="Developers see their own scans; administrators see all scans.")
def list_scans(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Scan) if user.role == "admin" else db.query(Scan).filter(Scan.owner_email == user.email)
    return query.order_by(Scan.created_at.desc()).all()

@app.get("/api/v1/scans/{scan_id}", tags=["scans"], summary="Get a detailed scan report", responses={404: {"description": "Scan does not exist or is not accessible"}})
def scan_detail(scan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if not scan or (user.role != "admin" and scan.owner_email != user.email): raise HTTPException(status_code=404, detail="Scan not found")
    return {"id": scan.id, "repository_name": scan.repository_name, "owner_email": scan.owner_email, "created_at": scan.created_at, **json.loads(scan.report_json)}

@app.get("/api/v1/admin/audit", response_model=AuditResponse, tags=["administration"], summary="Get administrator audit totals", responses={403: {"description": "Administrator role required"}})
def audit(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {"total_scans": db.query(Scan).count(), "total_users": db.query(User).count(), "requested_by": user.email}

