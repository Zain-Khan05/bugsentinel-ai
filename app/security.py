import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET_KEY = os.getenv("JWT_SECRET", "development-only-secret-change-me")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    return password_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)

def create_access_token(email: str, role: str) -> str:
    return jwt.encode({"sub": email, "role": role, "exp": datetime.now(timezone.utc) + timedelta(minutes=60)}, SECRET_KEY, algorithm="HS256")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:
    denied = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
    try:
        email = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"]).get("sub")
    except JWTError as error:
        raise denied from error
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise denied
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator role required")
    return user
