from __future__ import annotations
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, EmailStr, UUID4, ConfigDict
from datetime import datetime

# Base enabling from_orm style in Pydantic v2
class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# ---- Pagination ----
class PaginationInfo(ORMModel):
    total: int
    page: int
    limit: int
    total_pages: int

T = TypeVar("T")

class PaginatedResponse(ORMModel, Generic[T]):
    data: List[T]
    pagination: PaginationInfo

# ---- Organization ----
class OrganizationBase(ORMModel):
    name: str
    type: str = "client"
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    tax_id: Optional[str] = None
    status: str = "active"

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(ORMModel):
    name: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    tax_id: Optional[str] = None
    status: Optional[str] = None

class Organization(OrganizationBase):
    id: UUID4
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID4] = None
    updated_by: Optional[UUID4] = None

# ---- User ----
class UserBase(ORMModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    role: str = "viewer"
    organization_id: Optional[UUID4] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(ORMModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    organization_id: Optional[UUID4] = None

class UserPasswordChange(ORMModel):
    old_password: str
    new_password: str

class User(UserBase):
    id: UUID4
    password_changed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID4] = None
    updated_by: Optional[UUID4] = None

# ---- Ice Rink ----
class IceRinkBase(ORMModel):
    name: str
    location: Optional[str] = None
    status: str = "active"
    ssp_status: str = "disconnected"
    organization_id: Optional[UUID4] = None

class IceRinkCreate(IceRinkBase):
    pass

class IceRinkUpdate(ORMModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    ssp_status: Optional[str] = None
    organization_id: Optional[UUID4] = None

class IceRink(IceRinkBase):
    id: UUID4
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID4] = None
    updated_by: Optional[UUID4] = None

# ---- Measurements ----
class MeasurementBase(ORMModel):
    timestamp: datetime
    ice_temperature: float
    chiller_power: float
    chiller_status: str
    ambient_temperature: Optional[float] = None
    humidity: Optional[float] = None
    energy_consumption: float
    data_source: str = "manual"
    quality_score: float = 1.0

class MeasurementCreate(MeasurementBase):
    pass

class Measurement(MeasurementBase):
    id: UUID4
    ice_rink_id: UUID4
    created_at: Optional[datetime] = None

# ---- Tokens ----
class Token(ORMModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None

class TokenData(ORMModel):
    username: str
