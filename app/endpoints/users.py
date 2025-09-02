from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Organization
from app.schemas import UserCreate, UserUpdate, User as UserSchema
from app.core.security import get_current_user, require_roles, get_password_hash
from app.utils.responses import success_envelope

router = APIRouter()

_ALLOWED_ROLES = {"admin", "operator", "viewer"}


def _to_user_schema(u: User) -> UserSchema:
    return UserSchema.model_validate(u, from_attributes=True)


@router.get("/", dependencies=[Depends(require_roles("admin"))])
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(User)
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()

    data = {
        "items": [_to_user_schema(u) for u in items],
        "page": page,
        "limit": limit,
        "total": total,
    }
    return success_envelope(data)


@router.get("/{user_id}", dependencies=[Depends(require_roles("admin"))])
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return success_envelope(_to_user_schema(u))


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("admin"))])
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Walidacja organization_id (w DB jest NOT NULL)
    if not payload.organization_id:
        raise HTTPException(status_code=400, detail="organization_id is required")

    org = db.query(Organization).filter(Organization.id == payload.organization_id).first()
    if not org:
        raise HTTPException(status_code=400, detail="organization_id is invalid")

    # Walidacja roli
    if payload.role and payload.role not in _ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="role is invalid")

    # Hash hasła
    password_hash = get_password_hash(payload.password)

    u = User(
        organization_id=payload.organization_id,
        username=payload.username,
        email=payload.email,
        password_hash=password_hash,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        status="active" if payload.is_active else "inactive",
        created_by=current_user.id if current_user else None,
    )

    db.add(u)
    db.commit()
    db.refresh(u)
    return success_envelope(_to_user_schema(u))


@router.put("/{user_id}", dependencies=[Depends(require_roles("admin"))])
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    upd = payload.model_dump(exclude_unset=True)

    if "organization_id" in upd:
        if upd["organization_id"] is None:
            raise HTTPException(status_code=400, detail="organization_id cannot be null")
        org = db.query(Organization).filter(Organization.id == upd["organization_id"]).first()
        if not org:
            raise HTTPException(status_code=400, detail="organization_id is invalid")

    if "role" in upd:
        if upd["role"] not in _ALLOWED_ROLES:
            raise HTTPException(status_code=400, detail="role is invalid")

    if "password" in upd and upd["password"]:
        u.password_hash = get_password_hash(upd.pop("password"))

    for k, v in upd.items():
        setattr(u, k, v)

    db.add(u)
    db.commit()
    db.refresh(u)
    return success_envelope(_to_user_schema(u))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles("admin"))])
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(u)
    db.commit()
    # 204 — brak body
