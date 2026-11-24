import json
import os
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .analyzer import analyze_project
from .database import Base, SessionLocal, engine, get_db
from .models import Scan, User
from .schemas import CurrentUserResponse, LoginRequest, RegisterRequest, ScanRequest, ScanSummary, TokenResponse
from .security import create_access_token, get_current_user, hash_password, require_admin, verify_password

app = FastAPI(title="BugSentinel AI API", version="0.1.0", description="Bug prediction and security code-analysis prototype")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost", "https://localhost", "http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def initialise_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for email, password, role in [("admin@example.com", os.getenv("ADMIN_PASSWORD", "ChangeMe123!"), "admin"), ("developer@example.com", os.getenv("DEVELOPER_PASSWORD", "ChangeMe123!"), "developer")]:
            if not db.query(User).filter(User.email == email).first(): db.add(User(email=email, password_hash=hash_password(password), role=role))
        db.commit()
    finally: db.close()

@app.get("/api/v1/health", tags=["health"])
def health(): return {"status": "healthy", "service": "BugSentinel AI"}

@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["authentication"])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return TokenResponse(access_token=create_access_token(user.email, user.role), email=user.email, role=user.role)

@app.post("/api/v1/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, tags=["authentication"])
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account already exists for this email address")
    user = User(email=email, password_hash=hash_password(payload.password), role="developer")
    db.add(user)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.email, user.role), email=user.email, role=user.role)

@app.get("/api/v1/auth/me", response_model=CurrentUserResponse, tags=["authentication"])
def current_user(user: User = Depends(get_current_user)):
    return CurrentUserResponse(email=user.email, role=user.role)

@app.post("/api/v1/scans", tags=["scans"])
def create_scan(payload: ScanRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = analyze_project([item.model_dump() for item in payload.files])
    scan = Scan(repository_name=payload.repository_name, owner_email=user.email, overall_risk=report["overall_risk_level"], risk_score=report["overall_risk_score"], report_json=json.dumps(report))
    db.add(scan); db.commit(); db.refresh(scan)
    return {"id": scan.id, "repository_name": scan.repository_name, "created_at": scan.created_at, **report}

@app.get("/api/v1/scans", response_model=list[ScanSummary], tags=["scans"])
def list_scans(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Scan) if user.role == "admin" else db.query(Scan).filter(Scan.owner_email == user.email)
    return query.order_by(Scan.created_at.desc()).all()

@app.get("/api/v1/scans/{scan_id}", tags=["scans"])
def scan_detail(scan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if not scan or (user.role != "admin" and scan.owner_email != user.email): raise HTTPException(status_code=404, detail="Scan not found")
    return {"id": scan.id, "repository_name": scan.repository_name, "owner_email": scan.owner_email, "created_at": scan.created_at, **json.loads(scan.report_json)}

@app.get("/api/v1/admin/audit", tags=["administration"])
def audit(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {"total_scans": db.query(Scan).count(), "total_users": db.query(User).count(), "requested_by": user.email}

