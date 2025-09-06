from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from app.db import SessionLocal
from app.deps import get_current_user
from datetime import datetime, timezone
from fastapi.responses import StreamingResponse
import io, csv, json
import openpyxl

router = APIRouter(prefix="/api/ice-rinks/{id}/measurements", tags=["measurements"])

@router.get("")
async def list_measurements(id: str,
                            start_date: datetime | None = None,
                            end_date: datetime | None = None,
                            data_source: str | None = None,
                            limit: int = 100,
                            user=Depends(get_current_user)):
    filters = ["ice_rink_id = :id"]
    params = {"id": id, "limit": limit}
    if start_date:
        filters.append("timestamp >= :start")
        params["start"] = start_date
    if end_date:
        filters.append("timestamp <= :end")
        params["end"] = end_date
    if data_source:
        filters.append("data_source = :ds")
        params["ds"] = data_source
    where = " AND ".join(filters)

    async with SessionLocal() as s:
        rows = (await s.execute(text(f"""
            SELECT id::text, timestamp, ice_temperature, chiller_power, chiller_status,
                   ambient_temperature, humidity, energy_consumption, data_source, quality_score
            FROM measurements WHERE {where}
            ORDER BY timestamp DESC LIMIT :limit
        """), params)).mappings().all()
    return {"success": True, "data": rows}

@router.get("/latest")
async def latest_measurement(id: str, user=Depends(get_current_user)):
    async with SessionLocal() as s:
        row = (await s.execute(text("""
            SELECT id::text, timestamp, ice_temperature, chiller_power, chiller_status,
                   ambient_temperature, humidity, energy_consumption, data_source, quality_score
            FROM measurements WHERE ice_rink_id=:id
            ORDER BY timestamp DESC LIMIT 1
        """), {"id": id})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="No measurements found")
    return {"success": True, "data": row}

@router.get("/export")
async def export_measurements(id: str,
                              format: str = Query("csv", enum=["csv","json","xlsx"]),
                              limit: int = 1000,
                              user=Depends(get_current_user)):
    async with SessionLocal() as s:
        rows = (await s.execute(text("""
            SELECT id::text, timestamp, ice_temperature, chiller_power, chiller_status,
                   ambient_temperature, humidity, energy_consumption, data_source, quality_score
            FROM measurements WHERE ice_rink_id=:id
            ORDER BY timestamp DESC LIMIT :limit
        """), {"id": id, "limit": limit})).mappings().all()

    if format == "json":
        return {"success": True, "data": rows}

    elif format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys() if rows else [])
        writer.writeheader()
        writer.writerows(rows)
        buf.seek(0)
        return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                                 headers={"Content-Disposition": f"attachment; filename=measurements.csv"})

    elif format == "xlsx":
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "measurements"

        headers = [
            "timestamp", "ice_temperature", "chiller_power", "chiller_status",
            "ambient_temperature", "humidity", "energy_consumption",
            "data_source", "quality_score"
        ]
        ws.append(headers)

        for r in rows:
            ts = r["timestamp"]
            # openpyxl nie wspiera tz-aware; robimy UTC-naive
            if isinstance(ts, datetime) and ts.tzinfo is not None:
                ts = ts.astimezone(timezone.utc).replace(tzinfo=None)

            ws.append([
                ts,
                r["ice_temperature"],
                r["chiller_power"],
                r["chiller_status"],
                r["ambient_temperature"],
                r["humidity"],
                r["energy_consumption"],
                r["data_source"],
                r["quality_score"],
            ])

        from io import BytesIO
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)

        filename = f"measurements_{id}.xlsx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )
