from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import IceRink, SystemConfig

class SystemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_db_connection(self) -> bool:
        try:
            await self.session.execute(select(1))
            return True
        except Exception:
            return False

    async def get_ssp_connections(self) -> int:
        query = select(func.count(IceRink.id)).where(IceRink.ssp_status == 'connected')
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def get_full_status(self) -> dict:
        ssp_connections = await self.get_ssp_connections()
        
        # Pobieramy dynamicznie statusy z tabeli system_config
        query = select(SystemConfig).where(SystemConfig.key.in_([
            'weather_api_status', 'ai_models_status', 'last_backup'
        ]))
        result = await self.session.execute(query)
        configs = {item.key: item.value for item in result.scalars().all()}
        
        db_status = "ok" # Wiemy, że jest ok, bo ta funkcja by się nie wykonała
        system_status = "degraded" if configs.get('weather_api_status', 'unknown') != 'ok' else "ok"
        
        return {
            "system_status": system_status,
            "database_status": db_status,
            "ssp_connections": ssp_connections,
            "weather_api_status": configs.get('weather_api_status', 'unknown'),
            "ai_models_status": configs.get('ai_models_status', 'unknown'),
            "last_backup": configs.get('last_backup'),
        }
