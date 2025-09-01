from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models import User, Organization
from app.schemas import OrganizationCreate, OrganizationUpdate, Organization as OrganizationSchema
from app.database import get_db
from app.core import security

router = APIRouter()

@router.post("/", response_model=OrganizationSchema, status_code=status.HTTP_201_CREATED)
def create_organization(
    org: OrganizationCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_org = db.query(Organization).filter(Organization.name == org.name).first()
    if db_org:
        raise HTTPException(status_code=400, detail="Organization with this name already exists")
    new_org = Organization(**org.dict(), created_by=current_user.id)
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org

@router.get("/", response_model=List[OrganizationSchema])
def read_organizations(
    status: Optional[str] = None,
    type: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    query = db.query(Organization)
    if status:
        query = query.filter(Organization.status == status)
    if type:
        query = query.filter(Organization.type == type)
    orgs = query.offset(skip).limit(limit).all()
    return orgs

@router.get("/{organization_id}", response_model=OrganizationSchema)
def read_organization(
    organization_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_org = db.query(Organization).filter(Organization.id == organization_id).first()
    if db_org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return db_org

@router.put("/{organization_id}", response_model=OrganizationSchema)
def update_organization(
    organization_id: UUID,
    org_in: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not db_org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    update_data = org_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_org, field, value)
    
    db_org.updated_by = current_user.id
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org

@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not db_org:
        raise HTTPException(status_code=404, detail="Organization not found")
    db.delete(db_org)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
