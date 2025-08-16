"""Team repository implementation."""

import logging
import time
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text, Text

from app.repositories.base import CRUDRepository
from app.domain.models.teams import Team
from app.api.schemas.teams import TeamCreate, TeamUpdate, TeamSearchFilters
from app.core.exceptions import NotFoundException, DatabaseException

logger = logging.getLogger(__name__)


class TeamRepository(CRUDRepository[Team, TeamCreate, TeamUpdate]):
    """Repository for teams with project-specific operations."""
    
    def __init__(self):
        """Initialize the repository with the Team model."""
        super().__init__(Team)
    
    def get_by_project(
        self, 
        db: Session,
        project_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Team]:
        """Get teams by project.
        
        Args:
            db: Database session.
            project_id: The ID of the project.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of teams.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        start_time = time.time()
        
        try:
            query = db.query(Team).filter(Team.project_id == project_id)
            teams = query.order_by(Team.name).offset(skip).limit(limit).all()
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"Retrieved {len(teams)} teams for project {project_id} in {execution_time}ms")
            
            return teams
            
        except Exception as e:
            logger.error(f"Error retrieving teams for project {project_id}: {e}")
            raise DatabaseException(f"Error retrieving teams: {str(e)}", original_exception=e)
    
    def get_by_project_and_name(
        self, 
        db: Session, 
        project_id: str, 
        name: str
    ) -> Optional[Team]:
        """Get a team by project ID and name.
        
        Args:
            db: Database session.
            project_id: The ID of the project.
            name: The name of the team.
            
        Returns:
            The team if found, None otherwise.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            return db.query(Team).filter(
                and_(Team.project_id == project_id, Team.name == name)
            ).first()
            
        except Exception as e:
            logger.error(f"Error retrieving team {name} for project {project_id}: {e}")
            raise DatabaseException(f"Error retrieving team: {str(e)}", original_exception=e)
    
    def search_teams(
        self,
        db: Session,
        project_id: str,
        filters: TeamSearchFilters,
        skip: int = 0,
        limit: int = 100
    ) -> List[Team]:
        """Search teams with filters.
        
        Args:
            db: Database session.
            project_id: The ID of the project.
            filters: Search filters.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of filtered teams.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        start_time = time.time()
        
        try:
            query = db.query(Team).filter(Team.project_id == project_id)
            
            # Apply filters
            if filters.name:
                query = query.filter(Team.name.ilike(f"%{filters.name}%"))
            
            if filters.role:
                query = query.filter(Team.role.ilike(f"%{filters.role}%"))
            
            if filters.member:
                # Search for member name in the JSON members array
                # For SQLite, we'll use a simple text search in the JSON
                query = query.filter(
                    func.lower(func.cast(Team.members, Text)).like(f"%{filters.member.lower()}%")
                )
            
            if filters.responsibility:
                # Search for responsibility in the JSON responsibilities array
                query = query.filter(
                    func.lower(func.cast(Team.responsibilities, Text)).like(f"%{filters.responsibility.lower()}%")
                )
            
            # Order by name for consistent results
            query = query.order_by(Team.name)
            
            teams = query.offset(skip).limit(limit).all()
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"Search returned {len(teams)} teams for project {project_id} in {execution_time}ms")
            
            return teams
            
        except Exception as e:
            logger.error(f"Error searching teams for project {project_id}: {e}")
            raise DatabaseException(f"Error searching teams: {str(e)}", original_exception=e)
    
    def count_by_project(self, db: Session, project_id: str, filters: Optional[TeamSearchFilters] = None) -> int:
        """Count teams by project with optional filters.
        
        Args:
            db: Database session.
            project_id: The ID of the project.
            filters: Optional search filters.
            
        Returns:
            Number of teams matching the criteria.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            query = db.query(func.count(Team.id)).filter(Team.project_id == project_id)
            
            if filters:
                if filters.name:
                    query = query.filter(Team.name.ilike(f"%{filters.name}%"))
                
                if filters.role:
                    query = query.filter(Team.role.ilike(f"%{filters.role}%"))
                
                if filters.member:
                    query = query.filter(
                        func.lower(func.cast(Team.members, Text)).like(f"%{filters.member.lower()}%")
                    )
                
                if filters.responsibility:
                    query = query.filter(
                        func.lower(func.cast(Team.responsibilities, Text)).like(f"%{filters.responsibility.lower()}%")
                    )
            
            return query.scalar()
            
        except Exception as e:
            logger.error(f"Error counting teams for project {project_id}: {e}")
            raise DatabaseException(f"Error counting teams: {str(e)}", original_exception=e)
    
    def validate_member_names(self, members: List[str]) -> Dict[str, Any]:
        """Validate team member names.
        
        Args:
            members: List of member names to validate.
            
        Returns:
            Dictionary with validation results.
        """
        try:
            if not members:
                return {
                    "valid": True,
                    "invalid_members": [],
                    "duplicate_members": []
                }
            
            # Check for duplicates
            seen = set()
            duplicates = []
            for member in members:
                if member in seen:
                    duplicates.append(member)
                else:
                    seen.add(member)
            
            # Check for invalid names (empty or whitespace-only)
            invalid_members = [member for member in members if not member or not member.strip()]
            
            return {
                "valid": len(invalid_members) == 0 and len(duplicates) == 0,
                "invalid_members": invalid_members,
                "duplicate_members": duplicates
            }
            
        except Exception as e:
            logger.error(f"Error validating member names: {e}")
            raise DatabaseException(f"Error validating member names: {str(e)}", original_exception=e)
    
    def upsert_team(
        self, 
        db: Session, 
        project_id: str, 
        name: str, 
        team_data: Dict[str, Any]
    ) -> Team:
        """Create or update a team using project_id and name as natural key.
        
        Args:
            db: Database session.
            project_id: The ID of the project.
            name: The name of the team.
            team_data: The team data to create or update with.
            
        Returns:
            The created or updated team.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        start_time = time.time()
        
        try:
            # Validate member names if provided
            if 'members' in team_data and team_data['members']:
                validation_result = self.validate_member_names(team_data['members'])
                if not validation_result['valid']:
                    error_details = []
                    if validation_result['invalid_members']:
                        error_details.append(f"Invalid members: {', '.join(validation_result['invalid_members'])}")
                    if validation_result['duplicate_members']:
                        error_details.append(f"Duplicate members: {', '.join(validation_result['duplicate_members'])}")
                    raise DatabaseException(f"Member validation failed: {'; '.join(error_details)}")
            
            # Try to find existing team
            existing_team = self.get_by_project_and_name(db, project_id, name)
            
            if existing_team:
                # Update existing team
                for field, value in team_data.items():
                    if hasattr(existing_team, field) and field != 'project_id':
                        setattr(existing_team, field, value)
                
                db.add(existing_team)
                db.commit()
                db.refresh(existing_team)
                
                execution_time = int((time.time() - start_time) * 1000)
                logger.info(f"Updated team {name} for project {project_id} in {execution_time}ms")
                
                return existing_team
            else:
                # Create new team
                team_data['project_id'] = project_id
                team_data['name'] = name
                
                new_team = Team(**team_data)
                db.add(new_team)
                db.commit()
                db.refresh(new_team)
                
                execution_time = int((time.time() - start_time) * 1000)
                logger.info(f"Created team {name} for project {project_id} in {execution_time}ms")
                
                return new_team
                
        except DatabaseException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error upserting team {name} for project {project_id}: {e}")
            raise DatabaseException(f"Error upserting team: {str(e)}", original_exception=e)
    
    def delete_by_project_and_name(self, db: Session, project_id: str, name: str) -> bool:
        """Delete a team by project ID and name.
        
        Args:
            db: Database session.
            project_id: The ID of the project.
            name: The name of the team.
            
        Returns:
            True if the team was deleted, False if not found.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            team = self.get_by_project_and_name(db, project_id, name)
            if team:
                db.delete(team)
                db.commit()
                logger.info(f"Deleted team {name} from project {project_id}")
                return True
            return False
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting team {name} from project {project_id}: {e}")
            raise DatabaseException(f"Error deleting team: {str(e)}", original_exception=e)
    
    def get_teams_by_role(
        self, 
        db: Session, 
        project_id: str, 
        role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Team]:
        """Get teams by project and role.
        
        Args:
            db: Database session.
            project_id: The ID of the project.
            role: The role to filter by.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of teams with the specified role.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            query = db.query(Team).filter(
                and_(Team.project_id == project_id, Team.role.ilike(f"%{role}%"))
            )
            return query.order_by(Team.name).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error retrieving teams with role {role} for project {project_id}: {e}")
            raise DatabaseException(f"Error retrieving teams by role: {str(e)}", original_exception=e)
    
    def get_teams_with_member(
        self, 
        db: Session, 
        project_id: str, 
        member_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Team]:
        """Get teams that have a specific member.
        
        Args:
            db: Database session.
            project_id: The ID of the project.
            member_name: The name of the member to search for.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of teams containing the specified member.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            query = db.query(Team).filter(
                and_(
                    Team.project_id == project_id,
                    func.lower(func.cast(Team.members, Text)).like(f"%{member_name.lower()}%")
                )
            )
            return query.order_by(Team.name).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error retrieving teams with member {member_name} for project {project_id}: {e}")
            raise DatabaseException(f"Error retrieving teams with member: {str(e)}", original_exception=e)
    
    def get_with_tasks(self, db: Session, team_id: int) -> Optional[Team]:
        """Get a team with tasks loaded.
        
        Args:
            db: Database session.
            team_id: The ID of the team.
            
        Returns:
            The team with tasks if found, None otherwise.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            return db.query(Team).filter(
                Team.id == team_id
            ).options(
                joinedload(Team.tasks)
            ).first()
        except Exception as e:
            logger.error(f"Error getting team with tasks for team {team_id}: {e}")
            raise DatabaseException(f"Error getting team with tasks: {str(e)}", original_exception=e)


# Create a singleton instance
team_repository = TeamRepository()