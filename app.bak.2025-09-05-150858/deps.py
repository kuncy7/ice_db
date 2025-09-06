from fastapi import Depends, HTTPException, Header
from typing import Optional
from app.security import decode_token
from app.errors import http_401, http_403

async def get_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        http_401("Missing or invalid Authorization header")
    return authorization.split(" ", 1)[1].strip()

async def get_current_user(token: str = Depends(get_bearer_token)) -> dict:
    try:
        payload = decode_token(token)
    except Exception:
        http_401("Invalid token")
    if payload.get("type") != "access":
        http_401("Access token required")
    return payload

def require_role(*roles: str):
    async def _inner(user: dict = Depends(get_current_user)):
        if user.get("role") not in roles:
            http_403("Insufficient role")
        return user
    return _inner
