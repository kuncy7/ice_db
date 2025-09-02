from datetime import datetime, timedelta, timezone
from uuid import UUID as UUID_TYPE
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app import schemas
from app.core.config import settings
from app.core import security
from app.database import get_db
from app.models import User, UserSession
from app.utils.responses import success_envelope

router = APIRouter()


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = security.get_user(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    now = datetime.now(timezone.utc)

    # Sesja ważna jak refresh token
    refresh_exp = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    session = UserSession(
        id=uuid.uuid4(),
        user_id=user.id,
        expires_at=refresh_exp,
        is_active=True,
    )
    db.add(session)

    user.last_login = now
    db.add(user)
    db.commit()
    db.refresh(session)

    # Generuj oba tokeny
    access_token = security.create_access_token(
        subject=user.username,
        session_id=session.id,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    refresh_token = security.create_refresh_token(
        subject=user.username,
        session_id=session.id,
        expires_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    }


@router.post("/logout")
def logout(
    current_user: User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Unieważnia bieżącą sesję (na podstawie jti==sid z access tokena).
    """
    jti = getattr(current_user, "token_payload", {}).get("jti")  # type: ignore[attr-defined]
    if jti:
        session_id = UUID_TYPE(jti)
        db_session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if db_session:
            db_session.is_active = False
            db.add(db_session)
            db.commit()

    return success_envelope({"message": "Successfully logged out"})


@router.post("/refresh")
def refresh_access_token(
    db: Session = Depends(get_db),
    current_token: str = Depends(security.oauth2_scheme),
):
    """
    Wydaje nowy access token na podstawie **refresh tokena** przesłanego w nagłówku:
      Authorization: Bearer <refresh_token>
    """
    try:
        payload = jwt.decode(current_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        username = payload.get("sub")
        sid = payload.get("sid")
        if not username or not sid:
            raise HTTPException(status_code=401, detail="Invalid token")

        session_id = UUID_TYPE(sid)
        session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if not session or not session.is_active or session.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired or inactive")

        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        access_token = security.create_access_token(
            subject=user.username,
            session_id=session.id,
            expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        return success_envelope(
            {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            }
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
