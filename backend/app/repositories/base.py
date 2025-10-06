"""
Base repository class for common database operations
"""

from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository

        Args:
            model: SQLAlchemy model class
            db: Async database session
        """
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get entity by ID

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None
    ) -> List[ModelType]:
        """
        Get all entities with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Column to order by

        Returns:
            List of entities
        """
        query = select(self.model).offset(skip).limit(limit)

        if order_by is not None:
            query = query.order_by(order_by)
        elif hasattr(self.model, "updated_at"):
            query = query.order_by(self.model.updated_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        """
        Create new entity

        Args:
            **kwargs: Entity attributes

        Returns:
            Created entity
        """
        entity = self.model(**kwargs)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: ModelType, **kwargs) -> ModelType:
        """
        Update entity

        Args:
            entity: Entity to update
            **kwargs: Attributes to update

        Returns:
            Updated entity
        """
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        """
        Delete entity

        Args:
            entity: Entity to delete
        """
        await self.db.delete(entity)
        await self.db.flush()

    async def delete_by_id(self, id: int) -> bool:
        """
        Delete entity by ID

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.flush()
        return result.rowcount > 0

    async def count(self, **filters) -> int:
        """
        Count entities with optional filters

        Args:
            **filters: Filter conditions

        Returns:
            Count of entities
        """
        query = select(func.count()).select_from(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def exists(self, **filters) -> bool:
        """
        Check if entity exists

        Args:
            **filters: Filter conditions

        Returns:
            True if exists, False otherwise
        """
        return await self.count(**filters) > 0

    async def find_one(self, **filters) -> Optional[ModelType]:
        """
        Find single entity by filters

        Args:
            **filters: Filter conditions

        Returns:
            Entity or None if not found
        """
        query = select(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_many(self, **filters) -> List[ModelType]:
        """
        Find multiple entities by filters

        Args:
            **filters: Filter conditions

        Returns:
            List of entities
        """
        query = select(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return list(result.scalars().all())
