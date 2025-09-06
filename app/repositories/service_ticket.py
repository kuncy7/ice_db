# (Nowy plik app/repositories/service_ticket.py)

import uuid
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models import ServiceTicket, TicketComment

class ServiceTicketRepository(BaseRepository[ServiceTicket]):
    def __init__(self, session: AsyncSession):
        super().__init__(ServiceTicket, session)

    async def get_ticket_with_details(self, ticket_id: uuid.UUID) -> Optional[ServiceTicket]:
        query = (
            select(ServiceTicket)
            .where(ServiceTicket.id == ticket_id)
            .options(selectinload(ServiceTicket.comments).selectinload(TicketComment.user))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add_comment_to_ticket(self, ticket_id: uuid.UUID, user_id: uuid.UUID, comment_data: dict) -> Optional[TicketComment]:
        ticket = await self.get_by_id(ticket_id)
        if not ticket:
            return None
        
        new_comment = TicketComment(
            ticket_id=ticket_id,
            user_id=user_id,
            **comment_data
        )
        self.session.add(new_comment)
        await self.session.commit()
        await self.session.refresh(new_comment)
        return new_comment
