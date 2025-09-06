# (Nowy plik app/routers/service_tickets.py)

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.deps import require_role, get_ticket_repo, get_current_user_payload
from app.repositories.service_ticket import ServiceTicketRepository
from app.schemas import (ServiceTicketCreate, ServiceTicketUpdate, ServiceTicketResponse,
                           ServiceTicketDetailResponse, TicketCommentCreate, TicketCommentResponse,
                           PaginatedResponse, ServiceTicketStatusUpdate, ServiceTicketAssign)

router = APIRouter(prefix="/api/service-tickets", tags=["service-tickets"])

@router.get("", response_model=PaginatedResponse[ServiceTicketResponse])
async def list_service_tickets(
    page: int = 1,
    limit: int = 20,
    repo: ServiceTicketRepository = Depends(get_ticket_repo),
    _=Depends(require_role("admin", "operator", "client"))
):
    offset = (page - 1) * limit
    tickets, total = await repo.get_paginated_list(skip=offset, limit=limit)
    return PaginatedResponse(
        page=page, limit=limit, total=total,
        pages=(total + limit - 1) // limit if limit > 0 else 0,
        has_next=page * limit < total,
        has_prev=page > 1,
        items=tickets
    )

@router.post("", response_model=ServiceTicketResponse, status_code=status.HTTP_201_CREATED)
async def create_service_ticket(
    payload: ServiceTicketCreate,
    repo: ServiceTicketRepository = Depends(get_ticket_repo),
    user_payload: dict = Depends(get_current_user_payload)
):
    # Wymaga importu OrganizationRepository i IceRinkRepository w repozytorium zgłoszeń
    # lub dodatkowej logiki weryfikacji tutaj
    from app.models import IceRink
    rink = await repo.session.get(IceRink, payload.ice_rink_id)
    if not rink:
        raise HTTPException(status_code=404, detail="Ice rink not found")

    ticket_data = payload.model_dump()
    ticket_data["created_by_id"] = user_payload.get("sub")
    ticket_data["organization_id"] = rink.organization_id

    new_ticket = await repo.create(ticket_data)
    return new_ticket

@router.get("/{ticket_id}", response_model=ServiceTicketDetailResponse)
async def get_service_ticket(
    ticket_id: uuid.UUID,
    repo: ServiceTicketRepository = Depends(get_ticket_repo),
    _=Depends(require_role("admin", "operator", "client"))
):
    ticket = await repo.get_ticket_with_details(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")
    return ticket

@router.put("/{ticket_id}", response_model=ServiceTicketResponse)
async def update_service_ticket(
    ticket_id: uuid.UUID,
    payload: ServiceTicketUpdate,
    repo: ServiceTicketRepository = Depends(get_ticket_repo),
    _=Depends(require_role("admin", "operator"))
):
    updated_ticket = await repo.update(ticket_id, payload.model_dump(exclude_unset=True))
    if not updated_ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")
    return updated_ticket

@router.post("/{ticket_id}/comments", response_model=TicketCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment_to_ticket(
    ticket_id: uuid.UUID,
    payload: TicketCommentCreate,
    repo: ServiceTicketRepository = Depends(get_ticket_repo),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = user_payload.get("sub")
    comment = await repo.add_comment_to_ticket(ticket_id, user_id, payload.model_dump())
    if not comment:
        raise HTTPException(status_code=404, detail="Service ticket not found")
    return comment

@router.put("/{ticket_id}/status", response_model=ServiceTicketResponse)
async def update_ticket_status(
    ticket_id: uuid.UUID,
    payload: ServiceTicketStatusUpdate,
    repo: ServiceTicketRepository = Depends(get_ticket_repo),
    user_payload: dict = Depends(require_role("admin", "operator"))
):
    user_id = user_payload.get("sub")
    updated_ticket = await repo.update_status(
        ticket_id=ticket_id, 
        user_id=user_id, 
        new_status=payload.status, 
        comment_text=payload.comment
    )
    if not updated_ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")
    return updated_ticket

@router.put("/{ticket_id}/assign", response_model=ServiceTicketResponse)
async def assign_ticket_to_user(
    ticket_id: uuid.UUID,
    payload: ServiceTicketAssign,
    repo: ServiceTicketRepository = Depends(get_ticket_repo),
    user_payload: dict = Depends(require_role("admin", "operator"))
):
    assigning_user_id = user_payload.get("sub")
    assigned_ticket = await repo.assign_ticket(
        ticket_id=ticket_id, 
        assigned_to_id=payload.assigned_to_id, 
        assigning_user_id=assigning_user_id
    )
    if not assigned_ticket:
        raise HTTPException(status_code=404, detail="Service ticket or user to assign not found")
    return assigned_ticket
