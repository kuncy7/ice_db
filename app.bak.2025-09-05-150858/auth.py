from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.hash import bcrypt
from app.config import get_settings

settings = get_settings()

def hash_password(plain: str) -> str:
    return bcrypt.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.verify(plain, hashed)

def create_access_token(sub: str, role: str, organization_id: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_min)
    payload = {"sub": sub, "role": role, "organization_id": organization_id, "type": "access", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_refresh_token(sub: str, role: str, organization_id: str):
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_expires_days)
    payload = {"sub": sub, "role": role, "organization_id": organization_id, "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
