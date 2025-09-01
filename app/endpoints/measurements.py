from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import io
import csv
from starlette.responses import StreamingResponse
import math

from app.models import User, IceRink, Measurement
from app.schemas import MeasurementCreate, Measurement as MeasurementSchema, PaginatedResponse
from app.core import security
from app.database import get_db

router = APIRouter()

# ... (endpoint POST bez zmian) ...
@router.post("/{ice_rink_id}/measurements", response_model=MeasurementSchema, status_code=status.HTTP_201_CREATED)
def create_measurement_for_rink(ice_rink_id: UUID, measurement_in: MeasurementCreate, db: Session = Depends(get_db), current_user: User = Depends(security.get_current_user)):
    db_ice_rink = db.query(IceRink).filter(IceRink.id == ice_rink_id).first()
    if not db_ice_rink:
        raise HTTPException(status_code=404, detail="Ice rink not found")
    new_measurement = Measurement(**measurement_in.dict(), ice_rink_id=ice_rink_id)
    db.add(new_measurement)
    db.commit()
    db.refresh(new_measurement)
    return new_measurement

@router.get("/{ice_rink_id}/measurements", response_model=PaginatedResponse[MeasurementSchema])
def read_measurements(
    ice_rink_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    data_source: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    query = db.query(Measurement).filter(Measurement.ice_rink_id == ice_rink_id)
    
    if start_date:
        query = query.filter(Measurement.timestamp >= start_date)
    if end_date:
        query = query.filter(Measurement.timestamp <= end_date)
    if data_source:
        query = query.filter(Measurement.data_source == data_source)
        
    total = query.count()
    measurements = query.order_by(desc(Measurement.timestamp)).offset(skip).limit(limit).all()

    return {
        "data": measurements,
        "pagination": {
            "total": total,
            "page": (skip // limit) + 1,
            "limit": limit,
            "total_pages": math.ceil(total / limit)
        }
    }

@router.get("/{ice_rink_id}/measurements/latest", response_model=MeasurementSchema)
def read_latest_measurement(ice_rink_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(security.get_current_user)):
    latest_measurement = db.query(Measurement).filter(Measurement.ice_rink_id == ice_rink_id).order_by(desc(Measurement.timestamp)).first()
    if not latest_measurement:
        raise HTTPException(status_code=404, detail="No measurements found for this ice rink")
    return latest_measurement

@router.get("/{ice_rink_id}/measurements/export")
def export_measurements(
    ice_rink_id: UUID,
    start_date: datetime,
    end_date: datetime,
    format: str = Query("csv", enum=["csv", "json"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    # ... (logika eksportu bez zmian) ...
    query = db.query(Measurement).filter(Measurement.ice_rink_id == ice_rink_id)
    query = query.filter(Measurement.timestamp >= start_date)
    query = query.filter(Measurement.timestamp <= end_date)
    measurements = query.order_by(Measurement.timestamp).all()
    if not measurements:
        raise HTTPException(status_code=404, detail="No measurements found for the given time range")

    if format == "json":
        output = [MeasurementSchema.from_orm(m).dict(by_alias=True) for m in measurements]
        return output

    if format == "csv":
        stream = io.StringIO()
        writer = csv.writer(stream)
        headers = MeasurementSchema.model_fields.keys()
        writer.writerow(headers)
        for measurement in measurements:
            row_data = MeasurementSchema.from_orm(measurement).dict()
            writer.writerow([row_data[header] for header in headers])
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=measurements_{ice_rink_id}_{start_date.date()}_{end_date.date()}.csv"
        return response
