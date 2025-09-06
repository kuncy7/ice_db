from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import text
from app.db import SessionLocal
from app.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas import LoginRequest, RefreshRequest
from app.errors import http_401

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
async def login(payload: LoginRequest = Body(...)):
    async with SessionLocal() as s:
        row = (await s.execute(text("SELECT id::text, username, password_hash, role, organization_id::text FROM users WHERE username=:u"),
                                {"u": payload.username})).mappings().first()
        if not row or not verify_password(payload.password, row["password_hash"]):
            http_401("Incorrect username or password")
        access = create_access_token(row["id"], row["role"], row["organization_id"])
        refresh = create_refresh_token(row["id"], row["role"], row["organization_id"])
        return {
            "success": True,
            "data": {
                "access_token": access,
                "refresh_token": refresh,
                "user": {
                    "id": row["id"],
                    "username": row["username"],
                    "role": row["role"],
                    "organization_id": row["organization_id"],
                },
            },
        }

@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        http_401("Invalid refresh token")
    if payload.get("type") != "refresh":
        http_401("Invalid refresh token")
    access = create_access_token(payload["sub"], payload["role"], payload.get("organization_id"))
    refresh = create_refresh_token(payload["sub"], payload["role"], payload.get("organization_id"))
    return {"success": True, "data": {"access_token": access, "refresh_token": refresh}}

@router.get("/me")
async def me(user = Depends(lambda: None)):
    # Placeholder; the /me route is not strictly required by spec;
    return {"success": True}
