import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        return False

# Zaktualizowana funkcja, która ZAWSZE dodaje JTI
def _create_token(sub: str, role: str, organization_id: Optional[str], expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "organization_id": organization_id,
        "type": token_type,
        "exp": now + expires_delta,
        "iat": now,
        "jti": str(uuid.uuid4()) # JTI jest teraz dodawany do każdego tokena
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_access_token(sub: str, role: str, organization_id: Optional[str], expires_minutes: int | None = None) -> str:
    minutes = int(expires_minutes or settings.jwt_expires_min)
    return _create_token(sub, role, organization_id, timedelta(minutes=minutes), "access")

def create_refresh_token(sub: str, role: str, organization_id: Optional[str], expires_days: int | None = None) -> str:
    days = int(expires_days or settings.refresh_expires_days)
    return _create_token(sub, role, organization_id, timedelta(days=days), "refresh")

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
