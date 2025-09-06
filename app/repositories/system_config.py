# (Nowy plik app/repositories/system_config.py)
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models import SystemConfig

class SystemConfigRepository(BaseRepository[SystemConfig]):
    def __init__(self, session: AsyncSession):
        super().__init__(SystemConfig, session)

    async def get_all_configs(self) -> List[SystemConfig]:
        result = await self.session.execute(select(SystemConfig).order_by(SystemConfig.category, SystemConfig.key))
        return result.scalars().all()

    async def get_by_key(self, key: str) -> Optional[SystemConfig]:
        result = await self.session.execute(select(SystemConfig).where(SystemConfig.key == key))
        return result.scalar_one_or_none()
    
    async def update_by_key(self, key: str, value: str, user_id: uuid.UUID) -> Optional[SystemConfig]:
        config_item = await self.get_by_key(key)
        if not config_item:
            return None
        
        # W przyszłości można tu dodać logikę szyfrowania, jeśli is_encrypted=True
        config_item.value = value
        config_item.updated_by_id = user_id
        
        await self.session.commit()
        await self.session.refresh(config_item)
        return config_item
