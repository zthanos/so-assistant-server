"""Base repository implementation.

This module provides a base repository class that can be extended by specific repositories.
It implements common CRUD operations and follows the repository pattern.
"""
from typing import Generic, TypeVar, Type, List, Optional, Any, Dict, Union, Callable
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func, and_, or_
from sqlalchemy.sql import Select
from pydantic import BaseModel

from app.core.database import Base
from app.core.exceptions import NotFoundException, DatabaseException

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
FilterType = Dict[str, Any]

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository class with common CRUD operations.
    
    This class provides common CRUD operations for a specific model type.
    It can be extended by specific repositories to add custom operations.
    
    Attributes:
        model: The SQLAlchemy model class.
    """
    
    def __init__(self, model: Type[ModelType]):
        """Initialize the repository with a model class.
        
        Args:
            model: The SQLAlchemy model class.
        """
        self.model = model
    
    def create(self, db: Session, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """Create a new record.
        
        Args:
            db: The database session.
            obj_in: The data to create the record with.
            
        Returns:
            The created record.
        """
        try:
            obj_in_data = obj_in.dict() if isinstance(obj_in, BaseModel) else obj_in
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error creating {self.model.__name__}: {str(e)}", original_exception=e)
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a record by ID.
        
        Args:
            db: The database session.
            id: The ID of the record to get.
            
        Returns:
            The record if found, None otherwise.
        """
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            raise DatabaseException(f"Error retrieving {self.model.__name__} with id {id}: {str(e)}", original_exception=e)
    
    def get_or_404(self, db: Session, id: Any) -> ModelType:
        """Get a record by ID or raise a 404 exception.
        
        Args:
            db: The database session.
            id: The ID of the record to get.
            
        Returns:
            The record if found.
            
        Raises:
            NotFoundException: If the record is not found.
        """
        obj = self.get(db, id)
        if obj is None:
            raise NotFoundException(
                f"{self.model.__name__} with id {id} not found",
                resource_type=self.model.__name__,
                resource_id=id
            )
        return obj
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, filters: Optional[FilterType] = None
    ) -> List[ModelType]:
        """Get multiple records.
        
        Args:
            db: The database session.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            filters: Optional filters to apply.
            
        Returns:
            A list of records.
        """
        try:
            query = db.query(self.model)
            if filters:
                query = self._apply_filters(query, filters)
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error retrieving {self.model.__name__} records: {str(e)}", original_exception=e)
    
    def count(self, db: Session, filters: Optional[FilterType] = None) -> int:
        """Count the number of records.
        
        Args:
            db: The database session.
            filters: Optional filters to apply.
            
        Returns:
            The number of records.
        """
        try:
            query = db.query(func.count(self.model.id))
            if filters:
                query = self._apply_filters(query, filters)
            return query.scalar()
        except Exception as e:
            raise DatabaseException(f"Error counting {self.model.__name__} records: {str(e)}", original_exception=e)
    
    def exists(self, db: Session, id: Any) -> bool:
        """Check if a record exists.
        
        Args:
            db: The database session.
            id: The ID of the record to check.
            
        Returns:
            True if the record exists, False otherwise.
        """
        try:
            return db.query(db.query(self.model).filter(self.model.id == id).exists()).scalar()
        except Exception as e:
            raise DatabaseException(f"Error checking existence of {self.model.__name__} with id {id}: {str(e)}", original_exception=e)
    
    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record.
        
        Args:
            db: The database session.
            db_obj: The record to update.
            obj_in: The data to update the record with.
            
        Returns:
            The updated record.
        """
        try:
            obj_data = db_obj.__dict__
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error updating {self.model.__name__}: {str(e)}", original_exception=e)
    
    def update_by_id(
        self, db: Session, *, id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record by ID.
        
        Args:
            db: The database session.
            id: The ID of the record to update.
            obj_in: The data to update the record with.
            
        Returns:
            The updated record.
            
        Raises:
            NotFoundException: If the record is not found.
        """
        db_obj = self.get_or_404(db, id)
        return self.update(db, db_obj=db_obj, obj_in=obj_in)
    
    def delete(self, db: Session, *, id: Any) -> ModelType:
        """Delete a record.
        
        Args:
            db: The database session.
            id: The ID of the record to delete.
            
        Returns:
            The deleted record.
            
        Raises:
            NotFoundException: If the record is not found.
        """
        try:
            obj = db.query(self.model).get(id)
            if obj is None:
                raise NotFoundException(
                    f"{self.model.__name__} with id {id} not found",
                    resource_type=self.model.__name__,
                    resource_id=id
                )
            db.delete(obj)
            db.commit()
            return obj
        except NotFoundException:
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error deleting {self.model.__name__} with id {id}: {str(e)}", original_exception=e)
    
    def _apply_filters(self, query, filters: FilterType):
        """Apply filters to a query.
        
        Args:
            query: The query to apply filters to.
            filters: The filters to apply.
            
        Returns:
            The filtered query.
        """
        for field, value in filters.items():
            if hasattr(self.model, field):
                if isinstance(value, list):
                    query = query.filter(getattr(self.model, field).in_(value))
                else:
                    query = query.filter(getattr(self.model, field) == value)
        return query


class AsyncBaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Async base repository class with common CRUD operations.
    
    This class provides common CRUD operations for a specific model type using async SQLAlchemy.
    It can be extended by specific repositories to add custom operations.
    
    Attributes:
        model: The SQLAlchemy model class.
    """
    
    def __init__(self, model: Type[ModelType]):
        """Initialize the repository with a model class.
        
        Args:
            model: The SQLAlchemy model class.
        """
        self.model = model
    
    async def create(self, db: AsyncSession, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """Create a new record asynchronously.
        
        Args:
            db: The async database session.
            obj_in: The data to create the record with.
            
        Returns:
            The created record.
        """
        try:
            obj_in_data = obj_in.dict() if isinstance(obj_in, BaseModel) else obj_in
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            raise DatabaseException(f"Error creating {self.model.__name__}: {str(e)}", original_exception=e)
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get a record by ID asynchronously.
        
        Args:
            db: The async database session.
            id: The ID of the record to get.
            
        Returns:
            The record if found, None otherwise.
        """
        try:
            result = await db.execute(select(self.model).filter(self.model.id == id))
            return result.scalars().first()
        except Exception as e:
            raise DatabaseException(f"Error retrieving {self.model.__name__} with id {id}: {str(e)}", original_exception=e)
    
    async def get_or_404(self, db: AsyncSession, id: Any) -> ModelType:
        """Get a record by ID or raise a 404 exception asynchronously.
        
        Args:
            db: The async database session.
            id: The ID of the record to get.
            
        Returns:
            The record if found.
            
        Raises:
            NotFoundException: If the record is not found.
        """
        obj = await self.get(db, id)
        if obj is None:
            raise NotFoundException(
                f"{self.model.__name__} with id {id} not found",
                resource_type=self.model.__name__,
                resource_id=id
            )
        return obj
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, filters: Optional[FilterType] = None
    ) -> List[ModelType]:
        """Get multiple records asynchronously.
        
        Args:
            db: The async database session.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            filters: Optional filters to apply.
            
        Returns:
            A list of records.
        """
        try:
            query = select(self.model)
            if filters:
                query = self._apply_filters(query, filters)
            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseException(f"Error retrieving {self.model.__name__} records: {str(e)}", original_exception=e)
    
    async def count(self, db: AsyncSession, filters: Optional[FilterType] = None) -> int:
        """Count the number of records asynchronously.
        
        Args:
            db: The async database session.
            filters: Optional filters to apply.
            
        Returns:
            The number of records.
        """
        try:
            query = select(func.count(self.model.id))
            if filters:
                query = self._apply_filters(query, filters)
            result = await db.execute(query)
            return result.scalar()
        except Exception as e:
            raise DatabaseException(f"Error counting {self.model.__name__} records: {str(e)}", original_exception=e)
    
    async def exists(self, db: AsyncSession, id: Any) -> bool:
        """Check if a record exists asynchronously.
        
        Args:
            db: The async database session.
            id: The ID of the record to check.
            
        Returns:
            True if the record exists, False otherwise.
        """
        try:
            result = await db.execute(select(self.model).filter(self.model.id == id))
            return result.scalars().first() is not None
        except Exception as e:
            raise DatabaseException(f"Error checking existence of {self.model.__name__} with id {id}: {str(e)}", original_exception=e)
    
    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record asynchronously.
        
        Args:
            db: The async database session.
            db_obj: The record to update.
            obj_in: The data to update the record with.
            
        Returns:
            The updated record.
        """
        try:
            obj_data = {c.name: getattr(db_obj, c.name) for c in db_obj.__table__.columns}
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            raise DatabaseException(f"Error updating {self.model.__name__}: {str(e)}", original_exception=e)
    
    async def update_by_id(
        self, db: AsyncSession, *, id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record by ID asynchronously.
        
        Args:
            db: The async database session.
            id: The ID of the record to update.
            obj_in: The data to update the record with.
            
        Returns:
            The updated record.
            
        Raises:
            NotFoundException: If the record is not found.
        """
        db_obj = await self.get_or_404(db, id)
        return await self.update(db, db_obj=db_obj, obj_in=obj_in)
    
    async def delete(self, db: AsyncSession, *, id: Any) -> ModelType:
        """Delete a record asynchronously.
        
        Args:
            db: The async database session.
            id: The ID of the record to delete.
            
        Returns:
            The deleted record.
            
        Raises:
            NotFoundException: If the record is not found.
        """
        try:
            result = await db.execute(select(self.model).filter(self.model.id == id))
            obj = result.scalars().first()
            if obj is None:
                raise NotFoundException(
                    f"{self.model.__name__} with id {id} not found",
                    resource_type=self.model.__name__,
                    resource_id=id
                )
            await db.delete(obj)
            await db.commit()
            return obj
        except NotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise DatabaseException(f"Error deleting {self.model.__name__} with id {id}: {str(e)}", original_exception=e)
    
    def _apply_filters(self, query: Select, filters: FilterType) -> Select:
        """Apply filters to a query.
        
        Args:
            query: The query to apply filters to.
            filters: The filters to apply.
            
        Returns:
            The filtered query.
        """
        for field, value in filters.items():
            if hasattr(self.model, field):
                if isinstance(value, list):
                    query = query.where(getattr(self.model, field).in_(value))
                else:
                    query = query.where(getattr(self.model, field) == value)
        return query

class CRUDRepository(BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """CRUD repository class that extends the base repository.
    
    This class provides additional CRUD operations and utilities.
    It can be used as a base class for specific repositories.
    """
    
    def get_by_field(self, db: Session, field: str, value: Any) -> Optional[ModelType]:
        """Get a record by a specific field value.
        
        Args:
            db: The database session.
            field: The field to filter by.
            value: The value to filter for.
            
        Returns:
            The record if found, None otherwise.
        """
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"Field {field} does not exist on model {self.model.__name__}")
            return db.query(self.model).filter(getattr(self.model, field) == value).first()
        except Exception as e:
            raise DatabaseException(f"Error retrieving {self.model.__name__} with {field}={value}: {str(e)}", original_exception=e)
    
    def get_by_field_or_404(self, db: Session, field: str, value: Any) -> ModelType:
        """Get a record by a specific field value or raise a 404 exception.
        
        Args:
            db: The database session.
            field: The field to filter by.
            value: The value to filter for.
            
        Returns:
            The record if found.
            
        Raises:
            NotFoundException: If the record is not found.
        """
        obj = self.get_by_field(db, field, value)
        if obj is None:
            raise NotFoundException(
                f"{self.model.__name__} with {field}={value} not found",
                resource_type=self.model.__name__
            )
        return obj
    
    def get_multi_by_field(
        self, db: Session, field: str, value: Any, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records by a specific field value.
        
        Args:
            db: The database session.
            field: The field to filter by.
            value: The value to filter for.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of records.
        """
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"Field {field} does not exist on model {self.model.__name__}")
            return db.query(self.model).filter(getattr(self.model, field) == value).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error retrieving {self.model.__name__} records with {field}={value}: {str(e)}", original_exception=e)
    
    def bulk_create(self, db: Session, *, objs_in: List[Union[CreateSchemaType, Dict[str, Any]]]) -> List[ModelType]:
        """Create multiple records.
        
        Args:
            db: The database session.
            objs_in: The data to create the records with.
            
        Returns:
            The created records.
        """
        try:
            db_objs = []
            for obj_in in objs_in:
                obj_in_data = obj_in.dict() if isinstance(obj_in, BaseModel) else obj_in
                db_obj = self.model(**obj_in_data)
                db.add(db_obj)
                db_objs.append(db_obj)
            db.commit()
            for db_obj in db_objs:
                db.refresh(db_obj)
            return db_objs
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error bulk creating {self.model.__name__} records: {str(e)}", original_exception=e)
    
    def bulk_update(
        self, db: Session, *, ids: List[Any], obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> List[ModelType]:
        """Update multiple records by ID.
        
        Args:
            db: The database session.
            ids: The IDs of the records to update.
            obj_in: The data to update the records with.
            
        Returns:
            The updated records.
        """
        try:
            update_data = obj_in.dict(exclude_unset=True) if isinstance(obj_in, BaseModel) else obj_in
            db_objs = db.query(self.model).filter(self.model.id.in_(ids)).all()
            for db_obj in db_objs:
                for field, value in update_data.items():
                    if hasattr(db_obj, field):
                        setattr(db_obj, field, value)
                db.add(db_obj)
            db.commit()
            for db_obj in db_objs:
                db.refresh(db_obj)
            return db_objs
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error bulk updating {self.model.__name__} records: {str(e)}", original_exception=e)
    
    def bulk_delete(self, db: Session, *, ids: List[Any]) -> List[ModelType]:
        """Delete multiple records by ID.
        
        Args:
            db: The database session.
            ids: The IDs of the records to delete.
            
        Returns:
            The deleted records.
        """
        try:
            db_objs = db.query(self.model).filter(self.model.id.in_(ids)).all()
            for db_obj in db_objs:
                db.delete(db_obj)
            db.commit()
            return db_objs
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error bulk deleting {self.model.__name__} records: {str(e)}", original_exception=e)


class AsyncCRUDRepository(AsyncBaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Async CRUD repository class that extends the async base repository.
    
    This class provides additional CRUD operations and utilities.
    It can be used as a base class for specific repositories.
    """
    
    async def get_by_field(self, db: AsyncSession, field: str, value: Any) -> Optional[ModelType]:
        """Get a record by a specific field value asynchronously.
        
        Args:
            db: The async database session.
            field: The field to filter by.
            value: The value to filter for.
            
        Returns:
            The record if found, None otherwise.
        """
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"Field {field} does not exist on model {self.model.__name__}")
            result = await db.execute(select(self.model).filter(getattr(self.model, field) == value))
            return result.scalars().first()
        except Exception as e:
            raise DatabaseException(f"Error retrieving {self.model.__name__} with {field}={value}: {str(e)}", original_exception=e)
    
    async def get_by_field_or_404(self, db: AsyncSession, field: str, value: Any) -> ModelType:
        """Get a record by a specific field value or raise a 404 exception asynchronously.
        
        Args:
            db: The async database session.
            field: The field to filter by.
            value: The value to filter for.
            
        Returns:
            The record if found.
            
        Raises:
            NotFoundException: If the record is not found.
        """
        obj = await self.get_by_field(db, field, value)
        if obj is None:
            raise NotFoundException(
                f"{self.model.__name__} with {field}={value} not found",
                resource_type=self.model.__name__
            )
        return obj
    
    async def get_multi_by_field(
        self, db: AsyncSession, field: str, value: Any, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records by a specific field value asynchronously.
        
        Args:
            db: The async database session.
            field: The field to filter by.
            value: The value to filter for.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of records.
        """
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"Field {field} does not exist on model {self.model.__name__}")
            result = await db.execute(
                select(self.model)
                .filter(getattr(self.model, field) == value)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            raise DatabaseException(f"Error retrieving {self.model.__name__} records with {field}={value}: {str(e)}", original_exception=e)
    
    async def bulk_create(self, db: AsyncSession, *, objs_in: List[Union[CreateSchemaType, Dict[str, Any]]]) -> List[ModelType]:
        """Create multiple records asynchronously.
        
        Args:
            db: The async database session.
            objs_in: The data to create the records with.
            
        Returns:
            The created records.
        """
        try:
            db_objs = []
            for obj_in in objs_in:
                obj_in_data = obj_in.dict() if isinstance(obj_in, BaseModel) else obj_in
                db_obj = self.model(**obj_in_data)
                db.add(db_obj)
                db_objs.append(db_obj)
            await db.commit()
            for db_obj in db_objs:
                await db.refresh(db_obj)
            return db_objs
        except Exception as e:
            await db.rollback()
            raise DatabaseException(f"Error bulk creating {self.model.__name__} records: {str(e)}", original_exception=e)
    
    async def bulk_update(
        self, db: AsyncSession, *, ids: List[Any], obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> List[ModelType]:
        """Update multiple records by ID asynchronously.
        
        Args:
            db: The async database session.
            ids: The IDs of the records to update.
            obj_in: The data to update the records with.
            
        Returns:
            The updated records.
        """
        try:
            update_data = obj_in.dict(exclude_unset=True) if isinstance(obj_in, BaseModel) else obj_in
            result = await db.execute(select(self.model).filter(self.model.id.in_(ids)))
            db_objs = result.scalars().all()
            for db_obj in db_objs:
                for field, value in update_data.items():
                    if hasattr(db_obj, field):
                        setattr(db_obj, field, value)
                db.add(db_obj)
            await db.commit()
            for db_obj in db_objs:
                await db.refresh(db_obj)
            return db_objs
        except Exception as e:
            await db.rollback()
            raise DatabaseException(f"Error bulk updating {self.model.__name__} records: {str(e)}", original_exception=e)
    
    async def bulk_delete(self, db: AsyncSession, *, ids: List[Any]) -> List[ModelType]:
        """Delete multiple records by ID asynchronously.
        
        Args:
            db: The async database session.
            ids: The IDs of the records to delete.
            
        Returns:
            The deleted records.
        """
        try:
            result = await db.execute(select(self.model).filter(self.model.id.in_(ids)))
            db_objs = result.scalars().all()
            for db_obj in db_objs:
                await db.delete(db_obj)
            await db.commit()
            return db_objs
        except Exception as e:
            await db.rollback()
            raise DatabaseException(f"Error bulk deleting {self.model.__name__} records: {str(e)}", original_exception=e)