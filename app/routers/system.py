from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from app.deps import require_role, get_db_session
from app.repositories.system import SystemRepository # Należy utworzyć ten plik repozytorium
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/api/system", tags=["system"])

# Czas startu aplikacji, można przenieść do innego modułu
APP_START = datetime.now(timezone.utc)

@router.get("/status")
async def system_status(
    session: AsyncSession = Depends(get_db_session),
    _=Depends(require_role("admin", "operator"))
):
    repo = SystemRepository(session)
    is_db_ok = await repo.check_db_connection()
    
    if not is_db_ok:
        status_data = {
            "system_status": "error",
            "database_status": "error",
            "ssp_connections": 0,
            "weather_api_status": "unknown",
            "ai_models_status": "unknown",
            "last_backup": None,
        }
    else:
        status_data = await repo.get_full_status()

    uptime_delta = datetime.now(timezone.utc) - APP_START
    
    return {
        "success": True,
        "data": {
            **status_data,
            "uptime": str(uptime_delta).split('.')[0],
        },
    }
