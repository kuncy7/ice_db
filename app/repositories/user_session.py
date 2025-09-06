import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models import UserSession

class UserSessionRepository(BaseRepository[UserSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(UserSession, session)

    async def create_session(self, jti: uuid.UUID, user_id: uuid.UUID, expires_at: datetime) -> UserSession:
        session_data = {
            "id": jti,
            "user_id": user_id,
            "expires_at": expires_at
        }
        return await self.create(session_data)

    async def get_session(self, jti: uuid.UUID) -> UserSession | None:
        result = await self.session.execute(select(UserSession).where(UserSession.id == jti))
        return result.scalar_one_or_none()

    async def deactivate_session(self, jti: uuid.UUID) -> bool:
        session = await self.get_session(jti)
        if not session:
            return False
        
        session.is_active = False
        await self.session.commit()
        return True
