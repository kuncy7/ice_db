import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.deps import require_role, get_rink_repo, get_weather_forecast_repo
from app.repositories.ice_rink import IceRinkRepository
from app.repositories.weather_forecast import WeatherForecastRepository
from app.schemas import (IceRinkCreate, IceRinkUpdate, IceRinkResponse, IceRinkDetailResponse,
                         PaginatedResponse, WeatherForecastResponse)

router = APIRouter(prefix="/api/ice-rinks", tags=["ice-rinks"])

@router.get("", response_model=PaginatedResponse[IceRinkResponse])
async def list_ice_rinks(
    page: int = 1,
    limit: int = 20,
    repo: IceRinkRepository = Depends(get_rink_repo),
    user_payload: dict = Depends(require_role("admin", "operator", "client"))
):
    offset = (page - 1) * limit
    filters = {}
    if user_payload.get("role") == "client":
        filters["organization_id"] = user_payload.get("organization_id")

    rinks, total = await repo.get_paginated_list(skip=offset, limit=limit, filters=filters)
    return PaginatedResponse(
        page=page, limit=limit, total=total,
        pages=(total + limit - 1) // limit,
        has_next=page * limit < total,
        has_prev=page > 1,
        items=rinks
    )

@router.post("", response_model=IceRinkResponse, status_code=201)
async def create_ice_rink(
    payload: IceRinkCreate,
    repo: IceRinkRepository = Depends(get_rink_repo),
    _=Depends(require_role("admin", "operator"))
):
    new_rink = await repo.create(payload.model_dump())
    return new_rink

@router.get("/{rink_id}", response_model=IceRinkDetailResponse)
async def get_ice_rink(
    rink_id: uuid.UUID,
    repo: IceRinkRepository = Depends(get_rink_repo),
    user_payload: dict = Depends(require_role("admin", "operator", "client"))
):
    rink = await repo.get_by_id_with_details(rink_id)
    if not rink:
        raise HTTPException(status_code=404, detail="Ice rink not found")
    
    # Sprawdzenie uprawnień dla roli 'client'
    if user_payload.get("role") == "client" and str(rink.organization_id) != user_payload.get("organization_id"):
        raise HTTPException(status_code=403, detail="Forbidden")
        
    return rink

@router.put("/{rink_id}", response_model=IceRinkResponse)
async def update_ice_rink(
    rink_id: uuid.UUID,
    payload: IceRinkUpdate,
    repo: IceRinkRepository = Depends(get_rink_repo),
    _=Depends(require_role("admin", "operator"))
):
    updated_rink = await repo.update(rink_id, payload.model_dump(exclude_unset=True))
    if not updated_rink:
        raise HTTPException(status_code=404, detail="Ice rink not found")
    return updated_rink

@router.get("/{rink_id}/weather-forecasts", response_model=List[WeatherForecastResponse])
async def get_weather_forecasts_for_rink(
    rink_id: uuid.UUID,
    days: int = Query(7, ge=1, le=7),
    repo: WeatherForecastRepository = Depends(get_weather_forecast_repo),
    _=Depends(require_role("admin", "operator", "client"))
):
    """
    Retrieves weather forecasts for a specific ice rink for the upcoming days.
    """
    forecasts = await repo.get_forecasts_for_rink(rink_id=rink_id, days=days)
    if not forecasts:
        # To nie jest błąd, po prostu może jeszcze nie być prognoz
        return []
    return forecasts
