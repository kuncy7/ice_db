from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import JSONB
from app.db import SessionLocal
from app.deps import get_current_user, require_role
from app.utils import paginate
from app.schemas import IceRinkCreate, IceRinkUpdate

# --- Etap 3: test połączenia SSP ---
import httpx
import time

router = APIRouter(prefix="/api/ice-rinks", tags=["ice-rinks"])

@router.get("")
async def list_ice_rinks(page: int = 1, limit: int = 20,
                         organization_id: str | None = None,
                         status: str | None = None,
                         ssp_status: str | None = None,
                         location: str | None = None,
                         user=Depends(get_current_user)):
    offset = (page - 1) * limit
    filters = ["1=1"]
    params = {"limit": limit, "offset": offset}
    if organization_id:
        filters.append("organization_id = :org")
        params["org"] = organization_id
    if status:
        filters.append("status = :status")
        params["status"] = status
    if ssp_status:
        filters.append("ssp_status = :ssp_status")
        params["ssp_status"] = ssp_status
    if location:
        filters.append("location ILIKE :loc")
        params["loc"] = f"%{location}%"
    if user.get("role") == "client":
        filters.append("organization_id = :myorg")
        params["myorg"] = user.get("organization_id")

    where = " AND ".join(filters)
    async with SessionLocal() as s:
        rows = (await s.execute(text(f"""
            SELECT id::text, organization_id::text, name, location, latitude, longitude, dimensions,
                   type, chiller_type, max_power_consumption,
                   ssp_status, last_communication, status, created_at
            FROM ice_rinks
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), params)).mappings().all()
        total = (await s.execute(text(f"SELECT COUNT(*) FROM ice_rinks WHERE {where}"), params)).scalar_one()
    return {"success": True, "data": {"ice_rinks": rows, "pagination": paginate(total, page, limit)}}

@router.get("/{id}")
async def get_ice_rink(id: str, user=Depends(get_current_user)):
    org_filter = ""
    params = {"id": id}
    if user.get("role") == "client":
        org_filter = "AND organization_id = :myorg"
        params["myorg"] = user.get("organization_id")

    async with SessionLocal() as s:
        rink = (await s.execute(text(f"""
            SELECT id::text, organization_id::text, name, location, latitude, longitude, dimensions,
                   type, chiller_type, max_power_consumption,
                   ssp_status, last_communication, status, created_at, updated_at
            FROM ice_rinks WHERE id = :id {org_filter}
        """), params)).mappings().first()
        if not rink:
            raise HTTPException(status_code=404, detail="Ice rink not found")

        measurements = (await s.execute(text("""
            SELECT id::text, timestamp, ice_temperature, chiller_power, chiller_status,
                   ambient_temperature, humidity, energy_consumption, data_source, quality_score
            FROM measurements WHERE ice_rink_id=:id
            ORDER BY timestamp DESC LIMIT 100
        """), {"id": id})).mappings().all()

        forecasts = (await s.execute(text("""
            SELECT forecast_time, temperature_min, temperature_max, humidity, solar_radiation,
                   wind_speed, precipitation_probability, data_quality
            FROM weather_forecasts WHERE ice_rink_id=:id
            ORDER BY forecast_time ASC LIMIT 168
        """), {"id": id})).mappings().all()

    return {"success": True, "data": {**dict(rink), "measurements": measurements, "weather_forecasts": forecasts}}

@router.post("", dependencies=[Depends(require_role("admin","operator"))])
async def create_ice_rink(payload: IceRinkCreate, user=Depends(get_current_user)):
    async with SessionLocal() as s:
        stmt = text("""
            INSERT INTO ice_rinks (id, organization_id, name, location, latitude, longitude, dimensions,
                                   type, chiller_type, max_power_consumption,
                                   ssp_endpoint, ssp_api_key, ssp_status, status,
                                   created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), :org, :name, :loc, :lat, :lon, COALESCE(:dim, '{}'::jsonb),
                    :type, :chiller, :max_pwr,
                    :ssp_ep, :ssp_key, 'disconnected', 'active',
                    NOW(), NOW(), :uid, :uid)
            RETURNING id::text
        """).bindparams(bindparam("dim", type_=JSONB))

        rid = (await s.execute(stmt, {
            "org": payload.organization_id,
            "name": payload.name,
            "loc": payload.location,
            "lat": payload.latitude,
            "lon": payload.longitude,
            "dim": payload.dimensions,
            "type": payload.type,
            "chiller": payload.chiller_type,
            "max_pwr": payload.max_power_consumption,
            "ssp_ep": payload.ssp_endpoint,
            "ssp_key": payload.ssp_api_key,
            "uid": user.get("sub"),
        })).scalar_one()
        await s.commit()
    return {"success": True, "data": {"id": rid}}

@router.put("/{id}", dependencies=[Depends(require_role("admin","operator"))])
async def update_ice_rink(id: str, payload: IceRinkUpdate, user=Depends(get_current_user)):
    fields = []
    params = {"id": id, "by": user.get("sub")}
    for key, val in payload.model_dump(exclude_unset=True).items():
        if key == "dimensions":
            fields.append("dimensions = :dim")
            params["dim"] = val
            continue
        fields.append(f"{key} = :{key}")
        params[key] = val
    if not fields:
        return {"success": True, "data": {"id": id}}
    set_sql = ", ".join(fields) + ", updated_at=NOW(), updated_by=:by"
    async with SessionLocal() as s:
        await s.execute(text(f"UPDATE ice_rinks SET {set_sql} WHERE id=:id"), params)
        await s.commit()
    return {"success": True, "data": {"id": id}}

# ----------------------------
#  POST /api/ice-rinks/{id}/test-connection
# ----------------------------
@router.post("/{id}/test-connection", dependencies=[Depends(require_role("admin","operator"))])
async def test_connection(id: str, user=Depends(get_current_user)):
    # Pobierz endpoint i klucz
    async with SessionLocal() as s:
        rink = (await s.execute(text("""
            SELECT id::text, ssp_endpoint, ssp_api_key
            FROM ice_rinks WHERE id = :id
        """), {"id": id})).mappings().first()
        if not rink:
            raise HTTPException(status_code=404, detail="Ice rink not found")

    url = rink["ssp_endpoint"]
    if not url:
        raise HTTPException(status_code=400, detail="SSP endpoint is not configured for this ice rink")
    headers = {"Authorization": f"Bearer {rink['ssp_api_key']}"} if rink["ssp_api_key"] else {}

    # Spróbuj HEAD, jeśli brak – GET
    start = time.perf_counter()
    ok = False
    status_code = None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                r = await client.head(url, headers=headers)
            except httpx.HTTPError:
                r = await client.get(url, headers=headers)
        status_code = r.status_code
        ok = status_code < 400
    except Exception:
        ok = False
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    # Aktualizuj last_communication jeśli OK
    if ok:
        async with SessionLocal() as s:
            await s.execute(text("""
                UPDATE ice_rinks SET last_communication = NOW(), ssp_status = 'connected' WHERE id = :id
            """), {"id": id})
            await s.commit()
    else:
        # Opcjonalnie oznacz jako error (zostawiamy disconnected jeżeli tak wolisz)
        async with SessionLocal() as s:
            await s.execute(text("""
                UPDATE ice_rinks SET ssp_status = 'error' WHERE id = :id
            """), {"id": id})
            await s.commit()

    return {
        "success": True,
        "data": {
            "ice_rink_id": id,
            "ssp_endpoint": url,
            "status": "success" if ok else "error",
            "http_status": status_code,
            "response_time_ms": elapsed_ms
        }
    }
