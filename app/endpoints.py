from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas
from .database import get_db

router = APIRouter()

@router.post("/organizations/", response_model=schemas.Organization, tags=["Organizations"])
def create_organization(org: schemas.OrganizationCreate, db: Session = Depends(get_db)):
    db_org = db.query(models.Organization).filter(models.Organization.name == org.name).first()
    if db_org:
        raise HTTPException(status_code=400, detail="Organization with this name already exists")
    
    new_org = models.Organization(**org.dict())
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org

@router.get("/organizations/", response_model=List[schemas.Organization], tags=["Organizations"])
def read_organizations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orgs = db.query(models.Organization).offset(skip).limit(limit).all()
    return orgs

