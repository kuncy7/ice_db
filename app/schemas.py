import uuid
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Literal, Dict, Any, List, TypeVar, Generic
from datetime import datetime

# =================
#  Generic Schemas
# =================

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    page: int
    limit: int
    pages: int
    total: int
    has_next: bool
    has_prev: bool
    items: List[T]

# =================
#  Base & ORM Config
# =================

class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# =================
#  Organizations
# =================

class OrganizationBase(BaseModel):
    name: str
    type: Literal['client', 'partner', 'internal']
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    tax_id: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[Literal['client', 'partner', 'internal']] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    tax_id: Optional[str] = None
    status: Optional[Literal['active', 'inactive', 'suspended']] = None

class OrganizationResponse(OrganizationBase, OrmBase):
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# =================
#  Users
# =================

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Literal['admin', 'operator', 'client']

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    organization_id: uuid.UUID

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[Literal['admin', 'operator', 'client']] = None
    status: Optional[Literal['active', 'inactive', 'locked']] = None

class PasswordUpdate(BaseModel):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase, OrmBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# =================
#  Ice Rinks
# =================

class IceRinkBase(BaseModel):
    name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    type: Literal['standard', 'olympic', 'training'] = 'standard'
    chiller_type: str
    max_power_consumption: float
    ssp_endpoint: Optional[str] = None
    ssp_api_key: Optional[str] = None

class IceRinkCreate(IceRinkBase):
    organization_id: uuid.UUID

class IceRinkUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    type: Optional[Literal['standard', 'olympic', 'training']] = None
    chiller_type: Optional[str] = None
    max_power_consumption: Optional[float] = None
    ssp_endpoint: Optional[str] = None
    ssp_api_key: Optional[str] = None
    status: Optional[Literal['active', 'maintenance', 'inactive']] = None

class IceRinkResponse(IceRinkBase, OrmBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    ssp_status: str
    status: str
    last_communication: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# =================
#  Measurements
# =================

class MeasurementBase(BaseModel):
    timestamp: datetime
    ice_temperature: float
    chiller_power: float
    chiller_status: str
    ambient_temperature: Optional[float] = None
    humidity: Optional[float] = None
    energy_consumption: float
    data_source: Literal['ssp', 'manual', 'calculated'] = 'ssp'
    quality_score: float = Field(1.0, ge=0.0, le=1.0)

class MeasurementCreate(MeasurementBase):
    ice_rink_id: uuid.UUID

class MeasurementResponse(MeasurementBase, OrmBase):
    id: uuid.UUID
    ice_rink_id: uuid.UUID

# =================
#  Weather Providers
# =================
class WeatherProviderBase(BaseModel):
    name: str
    api_endpoint: str
    api_key: Optional[str] = None
    status: Literal['active', 'inactive', 'error'] = 'active'
    rate_limit: int = 1000

class WeatherProviderCreate(WeatherProviderBase):
    pass

class WeatherProviderUpdate(BaseModel):
    name: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    status: Optional[Literal['active', 'inactive', 'error']] = None
    rate_limit: Optional[int] = None

class WeatherProviderResponse(WeatherProviderBase, OrmBase):
    id: uuid.UUID
    last_used: Optional[datetime] = None
    created_at: datetime

# =================
#  Weather Forecasts
# =================
class WeatherForecastResponse(OrmBase):
    forecast_time: datetime
    temperature_min: float
    temperature_max: float
    humidity: Optional[float] = None

# =================
#  Service Tickets & Comments
# =================

class TicketCommentBase(BaseModel):
    comment: str
    is_internal: bool = False

class TicketCommentCreate(TicketCommentBase):
    pass

class TicketCommentResponse(TicketCommentBase, OrmBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

class ServiceTicketBase(BaseModel):
    category: str
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    priority: Literal['low', 'medium', 'high', 'critical'] = 'medium'

class ServiceTicketCreate(ServiceTicketBase):
    ice_rink_id: uuid.UUID

class ServiceTicketUpdate(BaseModel):
    status: Optional[Literal['new', 'assigned', 'in_progress', 'resolved', 'closed']] = None
    priority: Optional[Literal['low', 'medium', 'high', 'critical']] = None
    assigned_to_id: Optional[uuid.UUID] = None

class ServiceTicketResponse(ServiceTicketBase, OrmBase):
    id: uuid.UUID
    ticket_number: str
    ice_rink_id: uuid.UUID
    organization_id: uuid.UUID
    created_by_id: uuid.UUID
    assigned_to_id: Optional[uuid.UUID] = None
    status: str
    source: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# =================
#  Detailed Responses (with relations)
# =================

class IceRinkDetailResponse(IceRinkResponse):
    measurements: List[MeasurementResponse] = []
    weather_forecasts: List[WeatherForecastResponse] = []

class ServiceTicketDetailResponse(ServiceTicketResponse):
    comments: List[TicketCommentResponse] = []

# =================
#  Authentication
# =================

class LoginRequest(BaseModel):
    username: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse

class TokenResponse(BaseModel):
    success: bool = True
    data: TokenData
