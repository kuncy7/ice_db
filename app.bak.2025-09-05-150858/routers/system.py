from fastapi import APIRouter, Depends
from sqlalchemy import text
from datetime import datetime, timezone
from app.db import SessionLocal, ping_db
from app.deps import get_current_user

APP_START = datetime.now(timezone.utc)

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/status")
async def system_status(user=Depends(get_current_user)):
    database_status = "ok"
    try:
        await ping_db()
    except Exception:
        database_status = "error"
    async with SessionLocal() as s:
        ssp_connections = (await s.execute(text("SELECT COUNT(*) FROM ice_rinks WHERE ssp_status='connected'"))).scalar_one()
        # optional last backup if system_config exists
        last_backup = (await s.execute(text("SELECT value FROM system_config WHERE key='last_backup'"))).scalar_one_or_none()
        weather_api_status = (await s.execute(text("SELECT value FROM system_config WHERE key='weather_api_status'"))).scalar_one_or_none()
        ai_models_status = (await s.execute(text("SELECT value FROM system_config WHERE key='ai_models_status'"))).scalar_one_or_none()
    uptime_delta = datetime.now(timezone.utc) - APP_START
    return {
        "success": True,
        "data": {
            "system_status": "ok" if database_status == "ok" else "degraded",
            "database_status": database_status,
            "ssp_connections": ssp_connections,
            "weather_api_status": weather_api_status or "unknown",
            "ai_models_status": ai_models_status or "unknown",
            "last_backup": last_backup,
            "uptime": str(uptime_delta).split('.')[0],
        },
    }
