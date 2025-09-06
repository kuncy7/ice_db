import uuid
import io
import csv
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from app.deps import require_role, get_measurement_repo, get_rink_repo
from app.repositories.measurement import MeasurementRepository
from app.repositories.ice_rink import IceRinkRepository
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
        pages=(total + limit - 1) // limit if limit > 0 else 0,
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

@router.get("/export")
async def export_measurements(
    rink_id: uuid.UUID,
    format: str = Query("csv", enum=["csv", "json", "xlsx"]),
    limit: int = 1000,
    measurement_repo: MeasurementRepository = Depends(get_measurement_repo),
    rink_repo: IceRinkRepository = Depends(get_rink_repo),
    _=Depends(require_role("admin", "operator", "client"))
):
    rink = await rink_repo.get_by_id(rink_id)
    if not rink:
        raise HTTPException(status_code=404, detail="Ice rink not found")

    measurements, _ = await measurement_repo.get_measurements_for_rink(rink_id=rink_id, limit=limit)
    
    if not measurements:
        return {"message": "No data to export for this ice rink."}

    data_to_export = []
    for m in measurements:
        data = MeasurementResponse.model_validate(m).model_dump()
        data['ice_rink_name'] = m.ice_rink.name
        del data['id']
        del data['ice_rink_id']
        data_to_export.append(data)

    if format == "json":
        return data_to_export

    headers = ['ice_rink_name'] + [key for key in data_to_export[0].keys() if key != 'ice_rink_name']

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data_to_export)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                                 headers={"Content-Disposition": f"attachment; filename={rink.name}_measurements.csv"})

    elif format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = "Measurements"
        ws.append(headers)

        for row_data in data_to_export:
            row_values = [row_data.get(header) for header in headers]
            for i, value in enumerate(row_values):
                if isinstance(value, datetime) and value.tzinfo:
                    row_values[i] = value.astimezone(timezone.utc).replace(tzinfo=None)
            ws.append(row_values)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{rink.name}_measurements.xlsx"'}
        )
