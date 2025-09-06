from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.db import SessionLocal
from app.deps import get_current_user, require_role
from app.utils import paginate
from app.schemas import OrganizationCreate, OrganizationUpdate

router = APIRouter(prefix="/api/organizations", tags=["organizations"])

@router.get("")
async def list_orgs(page: int = 1, limit: int = 20, type: str | None = None, status: str | None = None, q: str | None = None, user=Depends(get_current_user)):
    offset = (page - 1) * limit
    filters = ["1=1"]
    params = {"limit": limit, "offset": offset}
    if type:
        filters.append('"type" = :type')
        params["type"] = type
    if status:
        filters.append('status = :status')
        params["status"] = status
    if q:
        filters.append('(name ILIKE :q OR COALESCE(address, '') ILIKE :q)')
        params["q"] = f"%{q}%"

    where = " AND ".join(filters)
    async with SessionLocal() as s:
        rows = (await s.execute(text(f"""
            SELECT id::text, name, "type", address, contact_person, contact_email, contact_phone, tax_id, status, created_at
            FROM organizations WHERE {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), params)).mappings().all()
        total = (await s.execute(text(f"SELECT COUNT(*) FROM organizations WHERE {where}"), params)).scalar_one()
    return {"success": True, "data": {"organizations": rows, "pagination": paginate(total, page, limit)}}

@router.get("/{id}")
async def get_org(id: str, user=Depends(get_current_user)):
    async with SessionLocal() as s:
        row = (await s.execute(text("""
            SELECT id::text, name, "type", address, contact_person, contact_email, contact_phone, tax_id, status,
                   created_at, updated_at
            FROM organizations WHERE id=:id
        """), {"id": id})).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Organization not found")
    return {"success": True, "data": row}

@router.post("", dependencies=[Depends(require_role("admin","operator"))])
async def create_org(payload: OrganizationCreate, user=Depends(get_current_user)):
    # /organizations.type has CHECK constraint: ['client','partner','internal']
    async with SessionLocal() as s:
        oid = (await s.execute(text("""
            INSERT INTO organizations (id, name, "type", address, contact_person, contact_email, contact_phone, tax_id,
                                       status, created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), :name, :type, :addr, :cp, :ce, :cphone, :tax, 'active', NOW(), NOW(), :by, :by)
            RETURNING id::text
        """), {
            "name": payload.name,
            "type": payload.type,
            "addr": payload.address,
            "cp": payload.contact_person,
            "ce": payload.contact_email,
            "cphone": payload.contact_phone,
            "tax": payload.tax_id,
            "by": user.get("sub"),
        })).scalar_one()
        await s.commit()
    return {"success": True, "data": {"id": oid}}

@router.put("/{id}", dependencies=[Depends(require_role("admin","operator"))])
async def update_org(id: str, payload: OrganizationUpdate, user=Depends(get_current_user)):
    fields = []
    params = {"id": id, "by": user.get("sub")}
    for key, val in payload.model_dump(exclude_unset=True).items():
        col = key if key != "type" else '"type"'
        fields.append(f"{col} = :{key}")
        params[key] = val
    if not fields:
        return {"success": True, "data": {"id": id}}
    set_sql = ", ".join(fields) + ", updated_at=NOW(), updated_by=:by"
    async with SessionLocal() as s:
        await s.execute(text(f"UPDATE organizations SET {set_sql} WHERE id=:id"), params)
        await s.commit()
    return {"success": True, "data": {"id": id}}
