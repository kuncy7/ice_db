# (Nowy plik app/repositories/weather_provider.py)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models import WeatherProvider

class WeatherProviderRepository(BaseRepository[WeatherProvider]):
    def __init__(self, session: AsyncSession):
        super().__init__(WeatherProvider, session)

    async def get_active_provider(self) -> WeatherProvider | None:
        query = select(WeatherProvider).where(WeatherProvider.status == 'active').limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
