import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models import IceRink

class IceRinkRepository(BaseRepository[IceRink]):
    def __init__(self, session: AsyncSession):
        super().__init__(IceRink, session)

    async def get_by_id_with_details(self, rink_id: uuid.UUID) -> IceRink | None:
        """
        Pobiera lodowisko razem z powiązanymi pomiarami i prognozami pogody.
        """
        query = (
            select(IceRink)
            .where(IceRink.id == rink_id)
            .options(
                selectinload(IceRink.measurements),
                selectinload(IceRink.weather_forecasts)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
