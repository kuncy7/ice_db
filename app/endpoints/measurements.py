from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import csv

from app.database import get_db
from app.models import Measurement, IceRink, User
from app.schemas import MeasurementCreate, Measurement as MeasurementSchema
from app.core.security import get_current_user, require_roles
from app.utils.responses import success_envelope

router = APIRouter()

# --- helpers -----------------------------------------------------------------

def _get_rink_or_404(db: Session, rink_id: UUID) -> IceRink:
    rink = db.query(IceRink).filter(IceRink.id == rink_id).first()
    if not rink:
        raise HTTPException(status_code=404, detail="Ice rink not found")
    return rink

def _to_schema(m: Measurement) -> MeasurementSchema:
    return MeasurementSchema.model_validate(m, from_attributes=True)

# --- endpoints ---------------------------------------------------------------

@router.post(
    "/{ice_rink_id}/measurements",
    dependencies=[Depends(require_roles("admin", "operator"))],
)
def create_measurement(
    ice_rink_id: UUID,
    payload: MeasurementCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Idempotentne utworzenie/aktualizacja pomiaru:
    - jeśli istnieje Measurement dla (ice_rink_id, timestamp) -> UPDATE i 200 OK
    - w przeciwnym razie -> INSERT i 201 Created
    """
    _get_rink_or_404(db, ice_rink_id)

    if payload.timestamp is None:
        raise HTTPException(status_code=400, detail="timestamp is required")

    # Sprawdź, czy już istnieje rekord o tym samym kluczu unikalnym
    existing = (
        db.query(Measurement)
        .filter(
            Measurement.ice_rink_id == ice_rink_id,
            Measurement.timestamp == payload.timestamp,
        )
        .first()
    )

    if existing:
        # aktualizacja pól (upsert – część update)
        existing.ice_temperature   = payload.ice_temperature
        existing.chiller_power     = payload.chiller_power
        existing.chiller_status    = payload.chiller_status
        existing.ambient_temperature = payload.ambient_temperature
        existing.humidity          = payload.humidity
        existing.energy_consumption = payload.energy_consumption
        existing.data_source       = payload.data_source
        existing.quality_score     = payload.quality_score

        db.add(existing)
        db.commit()
        db.refresh(existing)
        response.status_code = status.HTTP_200_OK
        return success_envelope(_to_schema(existing))

    # wstawienie nowego (upsert – część insert)
    m = Measurement(
        ice_rink_id=ice_rink_id,
        timestamp=payload.timestamp,
        ice_temperature=payload.ice_temperature,
        chiller_power=payload.chiller_power,
        chiller_status=payload.chiller_status,
        ambient_temperature=payload.ambient_temperature,
        humidity=payload.humidity,
        energy_consumption=payload.energy_consumption,
        data_source=payload.data_source,
        quality_score=payload.quality_score,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    response.status_code = status.HTTP_201_CREATED
    return success_envelope(_to_schema(m))


@router.get(
    "/{ice_rink_id}/measurements/latest",
    dependencies=[Depends(get_current_user)],
)
def get_latest_measurement(
    ice_rink_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Zwraca ostatni pomiar dla lodowiska.
    """
    _get_rink_or_404(db, ice_rink_id)

    m = (
        db.query(Measurement)
        .filter(Measurement.ice_rink_id == ice_rink_id)
        .order_by(Measurement.timestamp.desc())
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="No measurements found")
    return success_envelope(_to_schema(m))


@router.get(
    "/{ice_rink_id}/measurements/export",
    dependencies=[Depends(get_current_user)],
)
def export_measurements(
    ice_rink_id: UUID,
    db: Session = Depends(get_db),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    format: str = Query("csv", pattern="^(csv)$"),
):
    """
    Eksport pomiarów do CSV.
    """
    _get_rink_or_404(db, ice_rink_id)

    q = db.query(Measurement).filter(Measurement.ice_rink_id == ice_rink_id)
    if sort == "asc":
        q = q.order_by(Measurement.timestamp.asc())
    else:
        q = q.order_by(Measurement.timestamp.desc())
    rows: List[Measurement] = q.all()

    # tylko CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "timestamp",
        "ice_temperature",
        "chiller_power",
        "chiller_status",
        "ambient_temperature",
        "humidity",
        "energy_consumption",
        "data_source",
        "quality_score",
    ])
    for m in rows:
        writer.writerow([
            m.timestamp.isoformat() if m.timestamp else None,
            m.ice_temperature,
            m.chiller_power,
            m.chiller_status,
            m.ambient_temperature,
            m.humidity,
            m.energy_consumption,
            m.data_source,
            m.quality_score,
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=measurements.csv"},
    )
