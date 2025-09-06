from fastapi import APIRouter, Depends, Body
from app.deps import get_user_repo, get_bearer_token
from app.repositories.user import UserRepository
from app.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas import LoginRequest, RefreshRequest, TokenResponse, TokenData, UserResponse
from app.errors import http_401

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest = Body(...),
    repo: UserRepository = Depends(get_user_repo)
):
    user = await repo.get_by_username(payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        http_401("Incorrect username or password")

    access_token = create_access_token(
        sub=str(user.id),
        role=user.role,
        organization_id=str(user.organization_id)
    )
    refresh_token = create_refresh_token(
        sub=str(user.id),
        role=user.role,
        organization_id=str(user.organization_id)
    )

    return TokenResponse(
        data=TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user)
        )
    )

@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            http_401("Invalid refresh token")

        access = create_access_token(
            sub=payload["sub"],
            role=payload["role"],
            organization_id=payload.get("organization_id")
        )
        refresh = create_refresh_token(
            sub=payload["sub"],
            role=payload["role"],
            organization_id=payload.get("organization_id")
        )
        return {"success": True, "data": {"access_token": access, "refresh_token": refresh}}

    except Exception:
        http_401("Invalid or expired refresh token")

@router.post("/logout")
async def logout(token: str = Depends(get_bearer_token)):
    # Tutaj należy zaimplementować logikę blacklistowania tokenu,
    # np. poprzez dodanie jego JTI do bazy danych (Redis lub nowa tabela w PostgreSQL)
    # z czasem wygaśnięcia równym czasowi ważności tokenu.
    return {"success": True, "message": "Successfully logged out"}
