from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models import User
from app.schemas import UserCreate, UserPasswordChange, User as UserSchema
from app.core import security
from app.database import get_db

router = APIRouter()

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = security.get_password_hash(user.password)
    new_user = User(**user.dict(exclude={"password"}), password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=List[UserSchema])
def read_users(
    role: Optional[str] = None,
    status: Optional[str] = None,
    organization_id: Optional[UUID] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)
    if organization_id:
        query = query.filter(User.organization_id == organization_id)
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserSchema)
def read_user(
    user_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: UUID, 
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = user_in.dict(exclude_unset=True)
    if 'password' in update_data and update_data['password']:
        db_user.password_hash = security.get_password_hash(update_data['password'])
        del update_data['password']
    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}/password")
def change_user_password(
    user_id: UUID,
    passwords: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not security.verify_password(passwords.current_password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    db_user.password_hash = security.get_password_hash(passwords.new_password)
    db.add(db_user)
    db.commit()
    return {"message": "Password updated successfully"}

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
