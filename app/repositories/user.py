from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models import User
from app.security import get_password_hash
import uuid

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(self, data: dict) -> User:
        data["password_hash"] = get_password_hash(data.pop("password"))
        return await self.create(data)

    async def update_password(self, user_id: uuid.UUID, new_password: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        user.password_hash = get_password_hash(new_password)
        await self.session.commit()
        return True
