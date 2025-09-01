from datetime import datetime, timedelta, timezone
from uuid import UUID as UUID_TYPE
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import schemas
from app.core.config import settings
from app.core import security
from app.database import get_db
from app.models import User, UserSession

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = security.get_user(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, jti, exp = security.create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    
    db_session = UserSession(id=jti, user_id=user.id, expires_at=exp)
    db.add(db_session)
    user.last_login = datetime.now(timezone.utc)
    db.add(user)
    db.commit()

    # Na razie zwracamy pusty refresh token
    refresh_token = ""

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/logout")
def logout(
    current_user: User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unieważnia bieżącą sesję użytkownika i zwraca komunikat o sukcesie.
    """
    jti = current_user.token_payload.get("jti")
    if jti:
        session_id = UUID_TYPE(jti)
        db_session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if db_session:
            db_session.is_active = False
            db.add(db_session)
            db.commit()
    
    return {"message": "Successfully logged out"}
