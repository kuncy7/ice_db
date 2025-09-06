from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.deps import require_role, get_db_session, get_system_config_repo, get_current_user_payload
from app.repositories.system import SystemRepository
from app.repositories.system_config import SystemConfigRepository
from app.schemas import SystemConfigUpdate, SystemConfigResponse

router = APIRouter(prefix="/api/system", tags=["system"])

# ... istniejący endpoint /status ...
# (skopiuj go z poprzedniej poprawnej wersji)

@router.get("/config", response_model=List[SystemConfigResponse])
async def get_system_config(
    repo: SystemConfigRepository = Depends(get_system_config_repo),
    _=Depends(require_role("admin"))
):
    """
    Retrieves all system configuration parameters.
    """
    configs = await repo.get_all_configs()
    return configs

@router.put("/config/{key}", response_model=SystemConfigResponse)
async def update_system_config_value(
    key: str,
    payload: SystemConfigUpdate,
    repo: SystemConfigRepository = Depends(get_system_config_repo),
    user_payload: dict = Depends(require_role("admin"))
):
    """
    Updates the value of a single configuration parameter.
    """
    user_id = user_payload.get("sub")
    updated_config = await repo.update_by_key(key, payload.value, user_id)
    if not updated_config:
        raise HTTPException(status_code=404, detail=f"Configuration key '{key}' not found.")
    return updated_config
