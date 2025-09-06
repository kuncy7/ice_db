import uuid
from datetime import datetime
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.repositories.base import BaseRepository
from app.models import Measurement

class MeasurementRepository(BaseRepository[Measurement]):
    def __init__(self, session: AsyncSession):
        super().__init__(Measurement, session)

    async def get_measurements_for_rink(
        self,
        rink_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[Measurement], int]:
        
        query = select(Measurement).where(Measurement.ice_rink_id == rink_id)
        if start_date:
            query = query.where(Measurement.timestamp >= start_date)
        if end_date:
            query = query.where(Measurement.timestamp <= end_date)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        items_query = query.order_by(Measurement.timestamp.desc()).offset(skip).limit(limit)
        items = (await self.session.execute(items_query)).scalars().all()

        return items, total
    
    async def get_latest_for_rink(self, rink_id: uuid.UUID) -> Measurement | None:
        query = (
            select(Measurement)
            .where(Measurement.ice_rink_id == rink_id)
            .order_by(Measurement.timestamp.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
