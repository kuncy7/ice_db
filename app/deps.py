from fastapi import Depends, HTTPException, Header
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.security import decode_token, verify_password
from app.errors import http_401, http_403
from app.db import SessionLocal
from app.repositories.user import UserRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.ice_rink import IceRinkRepository
from app.repositories.measurement import MeasurementRepository
from app.repositories.service_ticket import ServiceTicketRepository
from app.repositories.weather_provider import WeatherProviderRepository
from app.repositories.weather_forecast import WeatherForecastRepository

# Zależność dostarczająca sesję bazodanową
async def get_db_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

# Zależności dostarczające instancje repozytoriów
def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)

def get_org_repo(session: AsyncSession = Depends(get_db_session)) -> OrganizationRepository:
    return OrganizationRepository(session)

def get_rink_repo(session: AsyncSession = Depends(get_db_session)) -> IceRinkRepository:
    return IceRinkRepository(session)

def get_measurement_repo(session: AsyncSession = Depends(get_db_session)) -> MeasurementRepository:
    return MeasurementRepository(session)

def get_ticket_repo(session: AsyncSession = Depends(get_db_session)) -> ServiceTicketRepository:
    return ServiceTicketRepository(session)

def get_weather_provider_repo(session: AsyncSession = Depends(get_db_session)) -> WeatherProviderRepository:
    return WeatherProviderRepository(session)

def get_weather_forecast_repo(session: AsyncSession = Depends(get_db_session)) -> WeatherForecastRepository:
    return WeatherForecastRepository(session)

# Zależności autoryzacji (reszta pliku)
async def get_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        http_401("Missing or invalid Authorization header")
    return authorization.split(" ", 1)[1].strip()

async def get_current_user_payload(token: str = Depends(get_bearer_token)) -> dict:
    try:
        payload = decode_token(token)
    except Exception:
        http_401("Invalid token")
    if payload.get("type") != "access":
        http_401("Access token required")
    return payload

def require_role(*roles: str):
    async def _inner(user: dict = Depends(get_current_user_payload)):
        if user.get("role") not in roles:
            http_403("Insufficient role")
        return user
    return _inner
