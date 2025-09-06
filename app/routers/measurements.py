import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from app.deps import require_role, get_measurement_repo
from app.repositories.measurement import MeasurementRepository
from app.schemas import MeasurementResponse, PaginatedResponse

router = APIRouter(prefix="/api/ice-rinks/{rink_id}/measurements", tags=["measurements"])

@router.get("", response_model=PaginatedResponse[MeasurementResponse])
async def list_measurements(
    rink_id: uuid.UUID,
    page: int = 1,
    limit: int = 100,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    repo: MeasurementRepository = Depends(get_measurement_repo),
    _=Depends(require_role("admin", "operator", "client"))
):
    offset = (page - 1) * limit
    measurements, total = await repo.get_measurements_for_rink(
        rink_id=rink_id, skip=offset, limit=limit, start_date=start_date, end_date=end_date
    )
    return PaginatedResponse(
        page=page, limit=limit, total=total,
        pages=(total + limit - 1) // limit,
        has_next=page * limit < total,
        has_prev=page > 1,
        items=measurements
    )

@router.get("/latest", response_model=MeasurementResponse)
async def get_latest_measurement(
    rink_id: uuid.UUID,
    repo: MeasurementRepository = Depends(get_measurement_repo),
    _=Depends(require_role("admin", "operator", "client"))
):
    measurement = await repo.get_latest_for_rink(rink_id)
    if not measurement:
        raise HTTPException(status_code=404, detail="No measurements found for this ice rink")
    return measurement
