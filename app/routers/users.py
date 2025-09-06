import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.deps import require_role, get_user_repo, get_current_user_payload
from app.repositories.user import UserRepository
from app.schemas import (UserCreate, UserResponse, UserUpdate,
                         PasswordUpdate)
from app.security import verify_password
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
        # Konwersja stringa z tokena na UUID dla repozytorium
        filters["organization_id"] = uuid.UUID(user_payload.get("organization_id"))

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

@router.put("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
    user_id: uuid.UUID,
    payload: PasswordUpdate, # <-- POPRAWKA: Używamy teraz konkretnego schematu
    repo: UserRepository = Depends(get_user_repo),
    current_user_payload: dict = Depends(get_current_user_payload)
):
    """
    Updates a user's password.
    - Admins can change any password providing only 'new_password'.
    - Regular users can change their own password providing 'current_password' and 'new_password'.
    """
    current_user_id = uuid.UUID(current_user_payload.get("sub"))
    current_user_role = current_user_payload.get("role")

    target_user = await repo.get_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Przypadek 1: Administrator zmienia hasło
    if current_user_role == 'admin':
        await repo.update_password(user_id, payload.new_password)
        return

    # Przypadek 2: Użytkownik zmienia własne hasło
    if current_user_id == user_id:
        if not payload.current_password:
            raise HTTPException(status_code=422, detail="Field 'current_password' is required for non-admin users.")
        
        if not verify_password(payload.current_password, target_user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect current password.")
        
        await repo.update_password(user_id, payload.new_password)
        return

    # Przypadek 3: Brak uprawnień
    raise HTTPException(status_code=403, detail="Not enough permissions to change this user's password.")
