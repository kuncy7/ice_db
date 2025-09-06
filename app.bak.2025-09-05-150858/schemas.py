from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal, Dict, Any

# Auth
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str

class UserRef(BaseModel):
    id: str
    username: str
    role: str
    organization_id: Optional[str] = None

class LoginResponse(BaseModel):
    success: bool = True
    data: dict

class RefreshRequest(BaseModel):
    refresh_token: str

# Org
class OrganizationBase(BaseModel):
    name: str
    type: Literal['client','partner','internal']
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    tax_id: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[Literal['client','partner','internal']] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    tax_id: Optional[str] = None
    status: Optional[Literal['active','maintenance','inactive']] = None

# Users
class UserCreate(BaseModel):
    username: str
    password: str
    role: Literal['admin','operator','client']
    organization_id: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

class UserUpdate(BaseModel):
    role: Optional[Literal['admin','operator','client']] = None
    organization_id: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    status: Optional[Literal['active','inactive']] = None

class ChangePassword(BaseModel):
    password: str

# Ice rinks
class IceRinkCreate(BaseModel):
    organization_id: str
    name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None  # stored as JSONB
    type: Literal['standard','olympic','training'] = 'standard'
    chiller_type: str
    max_power_consumption: float
    ssp_endpoint: Optional[str] = None
    ssp_api_key: Optional[str] = None

class IceRinkUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    type: Optional[Literal['standard','olympic','training']] = None
    chiller_type: Optional[str] = None
    max_power_consumption: Optional[float] = None
    ssp_endpoint: Optional[str] = None
    ssp_api_key: Optional[str] = None
    status: Optional[Literal['active','maintenance','inactive']] = None
    ssp_status: Optional[Literal['connected','disconnected','error']] = None
