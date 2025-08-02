"""Team repository implementation.

This module provides a repository for Team entities.
It extends the base repository and adds team-specific query methods.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.repositories.base import CRUDRepository
from app.domain.models.teams import Team
from app.api.schemas.teams import TeamCreate, TeamUpdate
from app.core.exceptions import NotFoundException, DatabaseException

class TeamRepository(CRUDRepository[Team, TeamCreate, TeamUpdate]):
    """Team repository class.
    
    This class provides CRUD operations and team-specific query methods.
    """
    
    def __init__(self):
        """Initialize the repository with the Team model."""
        super().__init__(Team)
    
    def get_by_project(self, db: Session, *, project_id: str, skip: int = 0, limit: int = 100) -> List[Team]:
        """Get teams for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of teams for the project.
        """
        return self.get_multi_by_field(db, "project_id", project_id, skip=skip, limit=limit)
    
    def get_by_name(self, db: Session, *, project_id: str, name: str) -> Optional[Team]:
        """Get a team by name for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            name: The name of the team.
            
        Returns:
            The team if found, None otherwise.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id,
                self.model.name == name
            ).first()
        except Exception as e:
            raise DatabaseException(f"Error getting team by name: {str(e)}", original_exception=e)
    
    def get_with_tasks(self, db: Session, *, id: int) -> Optional[Team]:
        """Get a team with tasks loaded.
        
        Args:
            db: The database session.
            id: The ID of the team.
            
        Returns:
            The team with tasks if found, None otherwise.
        """
        try:
            return db.query(self.model).filter(
                self.model.id == id
            ).options(
                joinedload(Team.tasks)
            ).first()
        except Exception as e:
            raise DatabaseException(f"Error getting team with tasks: {str(e)}", original_exception=e)
    
    def search_teams(
        self, db: Session, *, project_id: str, query: str, skip: int = 0, limit: int = 100
    ) -> List[Team]:
        """Search teams by name or members for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            query: The search query.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of teams matching the search query.
        """
        try:
            search_query = f"%{query}%"
            return db.query(self.model).filter(
                self.model.project_id == project_id,
                (self.model.name.ilike(search_query) | self.model.members.ilike(search_query))
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error searching teams: {str(e)}", original_exception=e)
    
    def count_by_project(self, db: Session, *, project_id: str) -> int:
        """Count the number of teams for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            
        Returns:
            The number of teams for the project.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id
            ).count()
        except Exception as e:
            raise DatabaseException(f"Error counting teams: {str(e)}", original_exception=e)

# Create a singleton instance
team_repository = TeamRepository()