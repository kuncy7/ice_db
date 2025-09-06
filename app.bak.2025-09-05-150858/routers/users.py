from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.db import SessionLocal
from app.deps import get_current_user, require_role
from app.utils import paginate

router = APIRouter(prefix="/api/users", tags=["users"])

# Schematy dokładnie wg specyfikacji (bez full_name):
class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str  # 'admin'|'operator'|'client'
    organization_id: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    organization_id: Optional[str] = None
    status: Optional[str] = None  # 'active'|'inactive'

class PasswordUpdate(BaseModel):
    password: str

@router.get("", dependencies=[Depends(require_role("admin","operator"))])
async def list_users(page: int = 1, limit: int = 20, user=Depends(get_current_user)):
    offset = (page - 1) * limit
    filters = ["1=1"]
    params = {"limit": limit, "offset": offset}

    if user.get("role") == "client":
        filters.append("organization_id = :myorg")
        params["myorg"] = user.get("organization_id")

    where = " AND ".join(filters)

    async with SessionLocal() as s:
        rows = (await s.execute(text(f"""
            SELECT id::text, username, role, organization_id::text, email,
                   first_name, last_name, status, created_at
            FROM users
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), params)).mappings().all()
        total = (await s.execute(text(f"SELECT COUNT(*) FROM users WHERE {where}"), params)).scalar_one()

    return {"success": True, "data": {"users": rows, "pagination": paginate(total, page, limit)}}

@router.get("/{id}", dependencies=[Depends(require_role("admin","operator","client"))])
async def get_user(id: str, user=Depends(get_current_user)):
    org_filter = ""
    params = {"id": id}
    if user.get("role") == "client":
        org_filter = "AND organization_id = :myorg"
        params["myorg"] = user.get("organization_id")

    async with SessionLocal() as s:
        row = (await s.execute(text(f"""
            SELECT id::text, username, role, organization_id::text, email,
                   first_name, last_name, status, created_at, updated_at
            FROM users
            WHERE id = :id {org_filter}
        """), params)).mappings().first()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

    return {"success": True, "data": row}

@router.post("", dependencies=[Depends(require_role("admin"))])
async def create_user(payload: UserCreate, user=Depends(get_current_user)):
    from app.security import get_password_hash
    password_hash = get_password_hash(payload.password)

    async with SessionLocal() as s:
        exists = (await s.execute(text("SELECT 1 FROM users WHERE username=:u"), {"u": payload.username})).first()
        if exists:
            raise HTTPException(status_code=409, detail="Username already exists")

        uid = (await s.execute(text("""
            INSERT INTO users
                (id, username, password_hash, role, organization_id, email,
                 first_name, last_name, status, created_at, updated_at, created_by, updated_by)
            VALUES
                (gen_random_uuid(), :username, :ph, :role, :org, :email,
                 :first_name, :last_name, 'active', NOW(), NOW(), :by, :by)
            RETURNING id::text
        """), {
            "username": payload.username,
            "ph": password_hash,
            "role": payload.role,
            "org": payload.organization_id,
            "email": payload.email,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "by": user.get("sub"),
        })).scalar_one()
        await s.commit()

    return {"success": True, "data": {"id": uid}}

@router.put("/{id}", dependencies=[Depends(require_role("admin"))])
async def update_user(id: str, payload: UserUpdate, user=Depends(get_current_user)):
    sets = []
    params = {"id": id, "by": user.get("sub")}
    if payload.email is not None:
        sets.append("email=:email")
        params["email"] = payload.email
    if payload.first_name is not None:
        sets.append("first_name=:first_name")
        params["first_name"] = payload.first_name
    if payload.last_name is not None:
        sets.append("last_name=:last_name")
        params["last_name"] = payload.last_name
    if payload.role is not None:
        sets.append("role=:role")
        params["role"] = payload.role
    if payload.organization_id is not None:
        sets.append("organization_id=:org")
        params["org"] = payload.organization_id
    if payload.status is not None:
        sets.append("status=:status")
        params["status"] = payload.status

    if not sets:
        return {"success": True, "data": {"id": id}}

    set_clause = ", ".join(sets) + ", updated_at=NOW(), updated_by=:by"

    async with SessionLocal() as s:
        res = await s.execute(text(f"UPDATE users SET {set_clause} WHERE id=:id"), params)
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        await s.commit()

    return {"success": True, "data": {"id": id}}

@router.put("/{id}/password", dependencies=[Depends(require_role("admin"))])
async def update_password(id: str, payload: PasswordUpdate, user=Depends(get_current_user)):
    from app.security import get_password_hash
    ph = get_password_hash(payload.password)

    async with SessionLocal() as s:
        res = await s.execute(text("""
            UPDATE users
            SET password_hash=:ph, updated_at=NOW(), updated_by=:by
            WHERE id=:id
        """), {"ph": ph, "by": user.get("sub"), "id": id})
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        await s.commit()

    return {"success": True, "data": {"id": id}}
