import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.deps import require_role, get_user_repo
from app.repositories.user import UserRepository
from app.schemas import UserCreate, UserResponse, UserUpdate, PasswordUpdate
from app.utils import paginate

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("", response_model=dict)
async def list_users(
    page: int = 1,
    limit: int = 20,
    repo: UserRepository = Depends(get_user_repo),
    user_payload: dict = Depends(require_role("admin", "operator"))
):
    offset = (page - 1) * limit
    filters = {}
    if user_payload.get("role") == "client":
        filters["organization_id"] = user_payload.get("organization_id")

    users, total = await repo.get_paginated_list(skip=offset, limit=limit, filters=filters)
    
    paginated_data = paginate(total, page, limit)
    paginated_data['users'] = [UserResponse.model_validate(u) for u in users]
    
    return {"success": True, "data": paginated_data}

@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    payload: UserCreate,
    repo: UserRepository = Depends(get_user_repo),
    _=Depends(require_role("admin"))
):
    if await repo.get_by_username(payload.username):
        raise HTTPException(status_code=409, detail="Username already exists")
    if await repo.get_by_email(payload.email):
        raise HTTPException(status_code=409, detail="Email already exists")
    
    new_user = await repo.create_user(payload.model_dump())
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    repo: UserRepository = Depends(get_user_repo),
    _=Depends(require_role("admin", "operator"))
):
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    repo: UserRepository = Depends(get_user_repo),
    _=Depends(require_role("admin"))
):
    updated_user = await repo.update(user_id, payload.model_dump(exclude_unset=True))
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.put("/{user_id}/password")
async def update_user_password(
    user_id: uuid.UUID,
    payload: PasswordUpdate,
    repo: UserRepository = Depends(get_user_repo),
    _=Depends(require_role("admin"))
):
    success = await repo.update_password(user_id, payload.password)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "message": "Password updated successfully."}
