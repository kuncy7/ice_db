from pydantic import BaseModel, UUID4, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Schematy dla Organization ---

class OrganizationBase(BaseModel):
    name: str
    type: str = 'client'
    status: str = 'active'
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    tax_id: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

# Schemat zwracany przez API - zawiera dodatkowe pola tylko do odczytu
class Organization(OrganizationBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Schematy dla User ---

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    role: str = 'operator'
    status: str = 'active'

class UserCreate(UserBase):
    password: str
    organization_id: UUID4

# Schemat zwracany przez API
class User(UserBase):
    id: UUID4
    organization_id: UUID4
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Schematy dla Autoryzacji ---

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
