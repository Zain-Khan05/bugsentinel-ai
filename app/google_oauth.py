"""Google OAuth helpers. Client secrets never leave the backend."""
import base64
import hashlib
import os
import secrets
import time
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv()
_pending_authorizations: dict[str, tuple[str, float]] = {}


def _configuration() -> tuple[str, str, str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    if not client_id or not client_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth is not configured")
    return client_id, client_secret, redirect_uri, frontend_url.rstrip("/")


def authorization_url() -> str:
    client_id, _, redirect_uri, _ = _configuration()
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    _pending_authorizations.clear()
    _pending_authorizations[state] = (verifier, time.time() + 600)
    query = urlencode({"client_id": client_id, "redirect_uri": redirect_uri, "response_type": "code", "scope": "openid email profile", "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


def authenticate_callback(code: str, state: str) -> tuple[dict, str]:
    pending = _pending_authorizations.pop(state, None)
    if not pending or pending[1] < time.time():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")
    client_id, client_secret, redirect_uri, frontend_url = _configuration()
    token_response = httpx.post("https://oauth2.googleapis.com/token", data={"client_id": client_id, "client_secret": client_secret, "code": code, "redirect_uri": redirect_uri, "grant_type": "authorization_code", "code_verifier": pending[0]}, timeout=10)
    if token_response.status_code != 200 or not token_response.json().get("access_token"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google authorization failed")
    profile_response = httpx.get("https://openidconnect.googleapis.com/v1/userinfo", headers={"Authorization": f"Bearer {token_response.json()['access_token']}"}, timeout=10)
    profile = profile_response.json() if profile_response.status_code == 200 else {}
    if not profile.get("sub") or not profile.get("email") or not profile.get("email_verified"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google did not provide a verified email address")
    return {"google_id": str(profile["sub"]), "email": profile["email"].lower()}, frontend_url
