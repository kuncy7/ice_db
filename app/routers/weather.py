import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.deps import require_role, get_weather_provider_repo
from app.repositories.weather_provider import WeatherProviderRepository
from app.schemas import (WeatherProviderCreate, WeatherProviderUpdate,
                           WeatherProviderResponse, PaginatedResponse)

router = APIRouter(prefix="/api/weather/providers", tags=["weather"])

@router.get("", response_model=PaginatedResponse[WeatherProviderResponse])
async def list_weather_providers(
    page: int = 1,
    limit: int = 20,
    repo: WeatherProviderRepository = Depends(get_weather_provider_repo),
    _=Depends(require_role("admin"))
):
    offset = (page - 1) * limit
    providers, total = await repo.get_paginated_list(skip=offset, limit=limit)
    
    return PaginatedResponse(
        page=page, limit=limit, total=total,
        pages=(total + limit - 1) // limit if limit > 0 else 0,
        has_next=page * limit < total,
        has_prev=page > 1,
        items=providers
    )

@router.post("", response_model=WeatherProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_weather_provider(
    payload: WeatherProviderCreate,
    repo: WeatherProviderRepository = Depends(get_weather_provider_repo),
    _=Depends(require_role("admin"))
):
    new_provider = await repo.create(payload.model_dump())
    return new_provider

@router.put("/{provider_id}", response_model=WeatherProviderResponse)
async def update_weather_provider(
    provider_id: uuid.UUID,
    payload: WeatherProviderUpdate,
    repo: WeatherProviderRepository = Depends(get_weather_provider_repo),
    _=Depends(require_role("admin"))
):
    """
    Updates a weather provider's configuration.
    """
    updated_provider = await repo.update(provider_id, payload.model_dump(exclude_unset=True))
    if not updated_provider:
        raise HTTPException(status_code=404, detail="Weather provider not found")
    return updated_provider
