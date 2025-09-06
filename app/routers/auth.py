import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Body, HTTPException
from app.deps import (get_user_repo, get_bearer_token, get_session_repo, 
                        get_current_user_payload)
from app.repositories.user import UserRepository
from app.repositories.user_session import UserSessionRepository
from app.security import (verify_password, create_access_token, 
                            create_refresh_token, decode_token)
from app.schemas import LoginRequest, RefreshRequest, TokenResponse, TokenData, UserResponse
from app.errors import http_401

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest = Body(...),
    user_repo: UserRepository = Depends(get_user_repo),
    session_repo: UserSessionRepository = Depends(get_session_repo)
):
    user = await user_repo.get_by_username(payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        http_401("Incorrect username or password")

    # Tworzymy tokeny, które teraz zawierają unikalny identyfikator 'jti'
    access_token = create_access_token(
        sub=str(user.id), role=user.role, organization_id=str(user.organization_id)
    )
    refresh_token = create_refresh_token(
        sub=str(user.id), role=user.role, organization_id=str(user.organization_id)
    )
    
    # Dekodujemy token, aby uzyskać 'jti' i datę wygaśnięcia
    token_payload = decode_token(access_token)
    jti = uuid.UUID(token_payload.get("jti"))
    exp = token_payload.get("exp")
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    
    # Tworzymy nową, aktywną sesję w bazie danych
    await session_repo.create_session(jti=jti, user_id=user.id, expires_at=expires_at)

    return TokenResponse(
        data=TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user)
        )
    )

@router.post("/logout", status_code=204)
async def logout(
    token: str = Depends(get_bearer_token),
    session_repo: UserSessionRepository = Depends(get_session_repo)
):
    try:
        payload = decode_token(token)
        jti_str = payload.get("jti")
        if jti_str:
            await session_repo.deactivate_session(uuid.UUID(jti_str))
    except Exception:
        # Ignorujemy błędy, np. dla wygasłego tokena
        pass
    return

@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    # Logika odświeżania tokena również powinna zostać rozbudowana
    # o deaktywację starej sesji i stworzenie nowej. Na razie zostawiamy uproszczoną.
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            http_401("Invalid refresh token")

        access = create_access_token(
            sub=payload["sub"],
            role=payload["role"],
            organization_id=payload.get("organization_id")
        )
        return {"success": True, "data": {"access_token": access}}

    except Exception:
        http_401("Invalid or expired refresh token")

@router.get("/me", response_model=UserResponse)
async def get_current_user_data(
    user_payload: dict = Depends(get_current_user_payload),
    repo: UserRepository = Depends(get_user_repo)
):
    user_id = user_payload.get("sub")
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
