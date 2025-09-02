from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organization, User
from app.schemas import OrganizationCreate, OrganizationUpdate, Organization as OrganizationSchema
from app.core.security import get_current_user, require_roles
from app.utils.responses import success_envelope

router = APIRouter()


def _to_org_schema(o: Organization) -> OrganizationSchema:
    return OrganizationSchema.model_validate(o, from_attributes=True)


@router.get("/")
def list_organizations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Organization)
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()

    data = {
        "items": [_to_org_schema(o) for o in items],
        "page": page,
        "limit": limit,
        "total": total,
    }
    return success_envelope(data)


@router.get("/{organization_id}")
def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    o = db.query(Organization).filter(Organization.id == organization_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Organization not found")
    return success_envelope(_to_org_schema(o))


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin"))],
)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    o = Organization(**payload.model_dump(exclude_unset=True))
    db.add(o)
    db.commit()
    db.refresh(o)
    return success_envelope(_to_org_schema(o))


@router.put(
    "/{organization_id}",
    dependencies=[Depends(require_roles("admin"))],
)
def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    o = db.query(Organization).filter(Organization.id == organization_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Organization not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(o, k, v)

    db.add(o)
    db.commit()
    db.refresh(o)
    return success_envelope(_to_org_schema(o))


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
def delete_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    o = db.query(Organization).filter(Organization.id == organization_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Organization not found")
    db.delete(o)
    db.commit()
    # 204 — brak body
