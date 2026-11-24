from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def enforce_password_strength(cls, password: str) -> str:
        if not any(character.islower() for character in password):
            raise ValueError("Password must contain a lowercase letter")
        if not any(character.isupper() for character in password):
            raise ValueError("Password must contain an uppercase letter")
        if not any(character.isdigit() for character in password):
            raise ValueError("Password must contain a number")
        return password

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: EmailStr
    role: str


class CurrentUserResponse(BaseModel):
    email: EmailStr
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
