from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import IceRink, Organization, User
from app.schemas import IceRinkCreate, IceRinkUpdate, IceRink as IceRinkSchema
from app.core.security import get_current_user, require_roles
from app.utils.responses import success_envelope

router = APIRouter()


def _to_rink_schema(r: IceRink) -> IceRinkSchema:
    return IceRinkSchema.model_validate(r, from_attributes=True)


@router.get("/")
def list_ice_rinks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(IceRink)
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()

    data = {
        "items": [_to_rink_schema(r) for r in items],
        "page": page,
        "limit": limit,
        "total": total,
    }
    return success_envelope(data)


@router.get("/{ice_rink_id}")
def get_ice_rink(
    ice_rink_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = db.query(IceRink).filter(IceRink.id == ice_rink_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Ice rink not found")
    return success_envelope(_to_rink_schema(r))


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "operator"))],
)
def create_ice_rink(
    payload: IceRinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.organization_id:
        org = db.query(Organization).filter(Organization.id == payload.organization_id).first()
        if not org:
            raise HTTPException(status_code=400, detail="organization_id is invalid")

    r = IceRink(**payload.model_dump(exclude_unset=True))
    db.add(r)
    db.commit()
    db.refresh(r)
    return success_envelope(_to_rink_schema(r))


@router.put(
    "/{ice_rink_id}",
    dependencies=[Depends(require_roles("admin", "operator"))],
)
def update_ice_rink(
    ice_rink_id: UUID,
    payload: IceRinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = db.query(IceRink).filter(IceRink.id == ice_rink_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Ice rink not found")

    upd = payload.model_dump(exclude_unset=True)
    if "organization_id" in upd and upd["organization_id"]:
        org = db.query(Organization).filter(Organization.id == upd["organization_id"]).first()
        if not org:
            raise HTTPException(status_code=400, detail="organization_id is invalid")

    for k, v in upd.items():
        setattr(r, k, v)

    db.add(r)
    db.commit()
    db.refresh(r)
    return success_envelope(_to_rink_schema(r))


@router.delete(
    "/{ice_rink_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin", "operator"))],
)
def delete_ice_rink(
    ice_rink_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = db.query(IceRink).filter(IceRink.id == ice_rink_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Ice rink not found")

    db.delete(r)
    db.commit()
    # 204 — brak body
