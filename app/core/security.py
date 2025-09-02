from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID as UUID_TYPE

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User, UserSession
from app.schemas import TokenData
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Ścieżka musi wskazywać na realny endpoint logowania
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(*, subject: str, session_id: UUID_TYPE, expires_minutes: int) -> str:
    """
    Access token:
      - sub: nazwa użytkownika
      - sid: identyfikator sesji (UUID)
      - type: 'access'
      - jti: == sid (dla kompatybilności z get_current_user)
      - exp: czas wygaśnięcia
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "sid": str(session_id),
        "type": "access",
        "jti": str(session_id),  # ważne: jti == sid
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(*, subject: str, session_id: UUID_TYPE, expires_minutes: int) -> str:
    """
    Refresh token:
      - sub: nazwa użytkownika
      - sid: identyfikator sesji (UUID)
      - type: 'refresh'
      - exp: czas wygaśnięcia
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "sid": str(session_id),
        "type": "refresh",
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_user(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Weryfikuje access token:
      - dekoduje JWT
      - pobiera jti==sid i sprawdza aktywność sesji w DB
      - ładuje użytkownika
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        jti: Optional[str] = payload.get("jti")  # dla access tokena == sid
        if username is None or jti is None:
            raise credentials_exception

        session_id = UUID_TYPE(jti)
        db_session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if not db_session or not db_session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session is not active or has been logged out",
            )

        token_data = TokenData(username=username)
    except (JWTError, ValueError):
        raise credentials_exception

    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    # pomocniczo: do /logout sięgamy po jti z payloadu
    user.token_payload = payload  # type: ignore[attr-defined]
    return user


# ---- RBAC helpers ----
def require_roles(*roles: str):
    """Dependency, który zezwala tylko na określone role."""
    def _dep(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user
    return _dep


def require_self_or_admin(user_id: UUID_TYPE, current_user: User = Depends(get_current_user)):
    """Zezwól adminowi lub właścicielowi zasobu (user_id)."""
    if current_user.role == "admin":
        return current_user
    if str(current_user.id) == str(user_id):
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")


def require_org_member_or_admin(organization_id: UUID_TYPE, current_user: User = Depends(get_current_user)):
    """Zezwól adminowi lub członkowi wskazanej organizacji."""
    if current_user.role == "admin":
        return current_user
    if str(getattr(current_user, "organization_id", None)) == str(organization_id):
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
