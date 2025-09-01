from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID  # <-- Dodajemy import UUID do walidacji ID w ścieżce

# Importy absolutne, które już mamy
from app.models import User, Organization
from app.schemas import OrganizationCreate, Organization as OrganizationSchema
from app.database import get_db
from app.core import security

router = APIRouter()

@router.post("/", response_model=OrganizationSchema)
def create_organization(
    org: OrganizationCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    """
    Tworzy nową organizację. Wymaga autoryzacji.
    """
    db_org = db.query(Organization).filter(Organization.name == org.name).first()
    if db_org:
        raise HTTPException(status_code=400, detail="Organization with this name already exists")
    
    new_org = Organization(**org.dict())
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org

@router.get("/", response_model=List[OrganizationSchema])
def read_organizations(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    """
    Pobiera listę organizacji. Wymaga autoryzacji.
    """
    orgs = db.query(Organization).offset(skip).limit(limit).all()
    return orgs

# --- NOWY ENDPOINT PONIŻEJ ---

@router.get("/{organization_id}", response_model=OrganizationSchema)
def read_organization(
    organization_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    """
    Pobiera szczegóły konkretnej organizacji na podstawie jej ID. Wymaga autoryzacji.
    """
    db_org = db.query(Organization).filter(Organization.id == organization_id).first()
    
    if db_org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    return db_org
