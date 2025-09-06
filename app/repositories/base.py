from typing import Type, TypeVar, Generic, Optional, List, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update as sqlalchemy_update
from sqlalchemy.orm import selectinload
from app.models import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, obj_id: uuid.UUID, load_relations: Optional[List[str]] = None) -> Optional[ModelType]:
        query = select(self.model).filter_by(id=obj_id)
        if load_relations:
            for relation in load_relations:
                query = query.options(selectinload(getattr(self.model, relation)))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> ModelType:
        db_obj = self.model(**data)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, obj_id: uuid.UUID, data: dict) -> Optional[ModelType]:
        # Filtruj `data` aby usunąć klucze z wartością None
        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            return await self.get_by_id(obj_id)

        query = sqlalchemy_update(self.model).where(self.model.id == obj_id).values(**update_data)
        await self.session.execute(query)
        await self.session.commit()
        return await self.get_by_id(obj_id)
        
    async def get_paginated_list(self, skip: int = 0, limit: int = 20, filters: Optional[dict] = None) -> Tuple[List[ModelType], int]:
        query = select(self.model)
        if filters:
            # Proste filtrowanie, można rozbudować o operatory ILIKE, >, < etc.
            query = query.filter_by(**filters)
        
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        items_query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        items = (await self.session.execute(items_query)).scalars().all()
        
        return items, total
