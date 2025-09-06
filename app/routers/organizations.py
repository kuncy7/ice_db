import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.deps import require_role, get_org_repo
from app.repositories.organization import OrganizationRepository
from app.schemas import (OrganizationCreate, OrganizationUpdate, OrganizationResponse,
                           PaginatedResponse)

router = APIRouter(prefix="/api/organizations", tags=["organizations"])

@router.get("", response_model=PaginatedResponse[OrganizationResponse])
async def list_organizations(
    page: int = 1,
    limit: int = 20,
    repo: OrganizationRepository = Depends(get_org_repo),
    _=Depends(require_role("admin", "operator"))
):
    offset = (page - 1) * limit
    orgs, total = await repo.get_paginated_list(skip=offset, limit=limit)
    return PaginatedResponse(
        page=page, limit=limit, total=total,
        pages=(total + limit - 1) // limit,
        has_next=page * limit < total,
        has_prev=page > 1,
        items=orgs
    )

@router.post("", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    payload: OrganizationCreate,
    repo: OrganizationRepository = Depends(get_org_repo),
    _=Depends(require_role("admin", "operator"))
):
    if await repo.get_by_name(payload.name):
        raise HTTPException(status_code=409, detail="Organization with this name already exists")
    new_org = await repo.create(payload.model_dump())
    return new_org

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: uuid.UUID,
    repo: OrganizationRepository = Depends(get_org_repo),
    _=Depends(require_role("admin", "operator"))
):
    org = await repo.get_by_id(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    payload: OrganizationUpdate,
    repo: OrganizationRepository = Depends(get_org_repo),
    _=Depends(require_role("admin", "operator"))
):
    updated_org = await repo.update(org_id, payload.model_dump(exclude_unset=True))
    if not updated_org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return updated_org
