import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.repositories.base import BaseRepository
from app.models import WeatherForecast

class WeatherForecastRepository(BaseRepository[WeatherForecast]):
    def __init__(self, session: AsyncSession):
        super().__init__(WeatherForecast, session)

    async def bulk_upsert(self, forecasts_data: List[dict]):
        if not forecasts_data:
            return
        
        stmt = insert(WeatherForecast).values(forecasts_data)
        update_stmt = stmt.on_conflict_do_update(
            # Ten index musi istnieć w bazie danych. Skrypt go nie tworzył,
            # więc na razie użyjemy pól.
            index_elements=['ice_rink_id', 'forecast_time'],
            set_={
                'temperature_min': stmt.excluded.temperature_min,
                'temperature_max': stmt.excluded.temperature_max,
                'humidity': stmt.excluded.humidity,
            }
        )
        await self.session.execute(update_stmt)
        await self.session.commit()

    async def get_forecasts_for_rink(
        self,
        rink_id: uuid.UUID,
        days: int = 7
    ) -> List[WeatherForecast]:
        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=days)

        query = (
            select(WeatherForecast)
            .where(
                WeatherForecast.ice_rink_id == rink_id,
                WeatherForecast.forecast_time >= now,
                WeatherForecast.forecast_time <= end_date
            )
            .order_by(WeatherForecast.forecast_time.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()
