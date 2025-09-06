from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models import Organization

class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, session: AsyncSession):
        super().__init__(Organization, session)

    async def get_by_name(self, name: str) -> Organization | None:
        result = await self.session.execute(
            select(Organization).where(Organization.name == name)
        )
        return result.scalar_one_or_none()
