# (Nowy plik app/repositories/service_ticket.py)

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

    async def update_status(self, ticket_id: uuid.UUID, user_id: uuid.UUID, new_status: str, comment_text: Optional[str] = None) -> Optional[ServiceTicket]:
        ticket = await self.get_by_id(ticket_id)
        if not ticket:
            return None
        
        # Zapisujemy stary status, aby dodać go w komentarzu
        old_status = ticket.status
        ticket.status = new_status
        
        # Tworzymy automatyczny komentarz systemowy
        system_comment = f"Status zgłoszenia zmieniony z '{old_status}' na '{new_status}'."
        if comment_text:
            system_comment += f"\n\nKomentarz użytkownika: {comment_text}"

        new_comment_obj = TicketComment(
            ticket_id=ticket_id,
            user_id=user_id,
            comment=system_comment,
            is_internal=True # Zmiany statusu są zawsze wewnętrzne
        )
        self.session.add(new_comment_obj)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def assign_ticket(self, ticket_id: uuid.UUID, assigned_to_id: uuid.UUID, assigning_user_id: uuid.UUID) -> Optional[ServiceTicket]:
        # Pobieramy zgłoszenie i przyszłego przypisanego użytkownika, aby mieć jego nazwę
        from app.models import User # Import wewnątrz funkcji, by uniknąć cyklicznych zależności
        
        ticket = await self.get_by_id(ticket_id)
        assigned_user = await self.session.get(User, assigned_to_id)

        if not ticket or not assigned_user:
            return None
        
        ticket.assigned_to_id = assigned_to_id
        
        # Dodajemy komentarz systemowy o przypisaniu
        system_comment = f"Zgłoszenie przypisano do użytkownika: {assigned_user.username}."
        new_comment_obj = TicketComment(
            ticket_id=ticket_id,
            user_id=assigning_user_id,
            comment=system_comment,
            is_internal=True
        )
        self.session.add(new_comment_obj)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket
