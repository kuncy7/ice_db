from pydantic import BaseModel, UUID4, EmailStr
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal

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

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    tax_id: Optional[str] = None

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

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str

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

# --- Schematy dla IceRink ---
class IceRinkBase(BaseModel):
    name: str
    location: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    dimensions: Optional[Any] = None
    type: str = 'standard'
    chiller_type: str
    max_power_consumption: Decimal
    ssp_endpoint: Optional[str] = None
    ssp_api_key: Optional[str] = None
    status: str = 'active'
class IceRinkCreate(IceRinkBase):
    organization_id: UUID4
class IceRinkUpdate(IceRinkBase):
    name: Optional[str] = None
    location: Optional[str] = None
    chiller_type: Optional[str] = None
    max_power_consumption: Optional[Decimal] = None
class IceRink(IceRinkBase):
    id: UUID4
    organization_id: UUID4
    ssp_status: str
    created_at: datetime
    updated_at: datetime
    created_by: UUID4
    class Config:
        from_attributes = True

# --- Schematy dla Measurement ---
class MeasurementBase(BaseModel):
    timestamp: datetime
    ice_temperature: Decimal
    chiller_power: Decimal
    chiller_status: str
    ambient_temperature: Optional[Decimal] = None
    humidity: Optional[Decimal] = None
    energy_consumption: Decimal
    data_source: str = 'manual'
    quality_score: Decimal = 1.0
class MeasurementCreate(MeasurementBase):
    pass
class Measurement(MeasurementBase):
    id: UUID4
    ice_rink_id: UUID4
    class Config:
        from_attributes = True
