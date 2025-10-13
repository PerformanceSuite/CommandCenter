"""
Base repository for common CRUD operations.
"""

from typing import Any, Generic, Type, TypeVar
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for CRUD operations on a SQLAlchemy model.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize the repository with a SQLAlchemy model.

        Args:
            model: The SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """
        Get a single record by ID.

        Args:
            db: The database session
            id: The record ID

        Returns:
            The model instance or None if not found
        """
        statement = select(self.model).where(self.model.id == id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """
        Get all records with optional pagination.

        Args:
            db: The database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            A list of model instances
        """
        statement = select(self.model).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: dict[str, Any]) -> ModelType:
        """
        Create a new record.

        Args:
            db: The database session
            obj_in: A dictionary with the data to create

        Returns:
            The created model instance
        """
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: dict[str, Any]
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            db: The database session
            db_obj: The existing model instance to update
            obj_in: A dictionary with the data to update

        Returns:
            The updated model instance
        """
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> ModelType | None:
        """
        Remove a record by ID.

        Args:
            db: The database session
            id: The record ID

        Returns:
            The removed model instance or None if not found
        """
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj