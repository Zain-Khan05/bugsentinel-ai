from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class SourceFile(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content: str = Field(max_length=200_000)

class ScanRequest(BaseModel):
    repository_name: str = Field(min_length=1, max_length=255)
    files: list[SourceFile] = Field(min_length=1, max_length=25)

class ScanSummary(BaseModel):
    id: int
    repository_name: str
    overall_risk: str
    risk_score: int
    created_at: datetime
