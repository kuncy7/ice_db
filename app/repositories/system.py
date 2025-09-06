from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import IceRink

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
        # Ta funkcja może zostać rozbudowana o odczytywanie statusu
        # z tabeli system_config, gdy będzie ona używana.
        ssp_connections = await self.get_ssp_connections()
        
        return {
            "system_status": "ok",
            "database_status": "ok",
            "ssp_connections": ssp_connections,
            "weather_api_status": "unknown", # Placeholder
            "ai_models_status": "unknown",   # Placeholder
            "last_backup": None,             # Placeholder
        }
