from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from app.models import User, IceRink
from app.schemas import IceRinkCreate, IceRinkUpdate, IceRink as IceRinkSchema
from app.core import security
from app.database import get_db

router = APIRouter()

@router.post("/", response_model=IceRinkSchema, status_code=status.HTTP_201_CREATED)
def create_ice_rink(
    ice_rink_in: IceRinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    new_ice_rink = IceRink(**ice_rink_in.dict(), created_by=current_user.id)
    db.add(new_ice_rink)
    db.commit()
    db.refresh(new_ice_rink)
    return new_ice_rink

@router.get("/", response_model=List[IceRinkSchema])
def read_ice_rinks(
    organization_id: Optional[UUID] = None,
    status: Optional[str] = None,
    ssp_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    query = db.query(IceRink)
    if organization_id:
        query = query.filter(IceRink.organization_id == organization_id)
    if status:
        query = query.filter(IceRink.status == status)
    if ssp_status:
        query = query.filter(IceRink.ssp_status == ssp_status)
    ice_rinks = query.offset(skip).limit(limit).all()
    return ice_rinks

@router.get("/{ice_rink_id}", response_model=IceRinkSchema)
def read_ice_rink(
    ice_rink_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_ice_rink = db.query(IceRink).filter(IceRink.id == ice_rink_id).first()
    if db_ice_rink is None:
        raise HTTPException(status_code=404, detail="Ice rink not found")
    return db_ice_rink

@router.put("/{ice_rink_id}", response_model=IceRinkSchema)
def update_ice_rink(
    ice_rink_id: UUID,
    ice_rink_in: IceRinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_ice_rink = db.query(IceRink).filter(IceRink.id == ice_rink_id).first()
    if not db_ice_rink:
        raise HTTPException(status_code=404, detail="Ice rink not found")
    update_data = ice_rink_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ice_rink, field, value)
    db_ice_rink.updated_by = current_user.id
    db.add(db_ice_rink)
    db.commit()
    db.refresh(db_ice_rink)
    return db_ice_rink

@router.post("/{ice_rink_id}/test-connection")
def test_ssp_connection(
    ice_rink_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_ice_rink = db.query(IceRink).filter(IceRink.id == ice_rink_id).first()
    if not db_ice_rink:
        raise HTTPException(status_code=404, detail="Ice rink not found")
    # TODO: Zaimplementować faktyczną logikę testowania połączenia z SSP
    return {
        "success": True,
        "data": { "status": "connected", "response_time": 150.5, "last_communication": datetime.now(timezone.utc), "error_message": None }
    }

@router.delete("/{ice_rink_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ice_rink(
    ice_rink_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_ice_rink = db.query(IceRink).filter(IceRink.id == ice_rink_id).first()
    if not db_ice_rink:
        raise HTTPException(status_code=404, detail="Ice rink not found")
    db.delete(db_ice_rink)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
