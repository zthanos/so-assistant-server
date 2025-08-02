"""Team service implementation.

This module provides a service for managing teams.
It follows the service pattern and provides a clean interface for team operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.team_repository import team_repository
from app.repositories.project_repository import project_repository
from app.domain.models.teams import Team
from app.api.schemas.teams import TeamCreate, TeamUpdate, TeamResponse
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.utils.pagination import PaginationParams, PaginationResult, Paginator
from app.utils.filtering import FilterCondition, QueryFilter

class TeamService:
    """Team service class.
    
    This class provides business logic for managing teams.
    """
    
    def __init__(self, db: Session):
        """Initialize the service with dependencies.
        
        Args:
            db: The database session.
        """
        self.db = db
        self.team_repository = team_repository
        self.project_repository = project_repository
    
    def create_team(self, project_id: str, name: str, members: Optional[str] = None) -> Team:
        """Create a new team.
        
        Args:
            project_id: The ID of the project.
            name: The name of the team.
            members: Comma-separated list of team members.
            
        Returns:
            The created team.
            
        Raises:
            NotFoundException: If the project is not found.
            ConflictException: If a team with the same name already exists for the project.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Check if team with same name exists
        existing_team = self.team_repository.get_by_name(self.db, project_id=project_id, name=name)
        if existing_team:
            raise ConflictException(
                f"Team with name '{name}' already exists for project {project_id}",
                resource_type="Team",
                conflict_field="name"
            )
        
        # Create team
        team_data = TeamCreate(
            project_id=project_id,
            name=name,
            members=members
        )
        
        return self.team_repository.create(self.db, obj_in=team_data)
    
    def get_team(self, team_id: int) -> Team:
        """Get a team by ID.
        
        Args:
            team_id: The ID of the team.
            
        Returns:
            The team.
            
        Raises:
            NotFoundException: If the team is not found.
        """
        return self.team_repository.get_or_404(self.db, team_id)
    
    def get_team_with_tasks(self, team_id: int) -> Team:
        """Get a team with its tasks.
        
        Args:
            team_id: The ID of the team.
            
        Returns:
            The team with tasks.
            
        Raises:
            NotFoundException: If the team is not found.
        """
        team = self.team_repository.get_with_tasks(self.db, id=team_id)
        if not team:
            raise NotFoundException(f"Team with ID {team_id} not found", resource_type="Team")
        return team
    
    def get_teams_for_project(
        self, 
        project_id: str, 
        pagination: PaginationParams,
        filters: Optional[List[FilterCondition]] = None,
        search: Optional[str] = None
    ) -> PaginationResult[Team]:
        """Get all teams for a project with pagination and filtering.
        
        Args:
            project_id: The ID of the project.
            pagination: Pagination parameters.
            filters: List of filter conditions.
            search: Search term.
            
        Returns:
            Paginated result of teams for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Build base query
        query = self.db.query(Team).filter(Team.project_id == project_id)
        
        # Apply filters
        if filters:
            allowed_fields = ["name", "members", "created_at", "updated_at"]
            query = QueryFilter.apply_filters(query, filters, Team, allowed_fields)
        
        # Apply search
        if search:
            search_fields = ["name", "members"]
            query = QueryFilter.apply_search(query, search, search_fields, Team)
        
        # Apply pagination
        allowed_sort_fields = ["name", "created_at", "updated_at"]
        return Paginator.paginate_query(
            query,
            pagination.page,
            pagination.per_page,
            pagination.sort_by,
            pagination.sort_order,
            allowed_sort_fields
        )
    
    def update_team(self, team_id: int, name: Optional[str] = None, members: Optional[str] = None) -> Team:
        """Update a team.
        
        Args:
            team_id: The ID of the team.
            name: The new name of the team.
            members: The new comma-separated list of team members.
            
        Returns:
            The updated team.
            
        Raises:
            NotFoundException: If the team is not found.
            ConflictException: If a team with the same name already exists for the project.
            BadRequestException: If no update fields are provided.
        """
        # Check if team exists
        team = self.team_repository.get_or_404(self.db, team_id)
        
        # Check if update fields are provided
        if name is None and members is None:
            raise BadRequestException("No update fields provided")
        
        # Check if name is being updated and if it conflicts with existing team
        if name is not None and name != team.name:
            existing_team = self.team_repository.get_by_name(self.db, project_id=team.project_id, name=name)
            if existing_team and existing_team.id != team_id:
                raise ConflictException(
                    f"Team with name '{name}' already exists for project {team.project_id}",
                    resource_type="Team",
                    conflict_field="name"
                )
        
        # Create update data
        update_data = TeamUpdate(
            name=name if name is not None else team.name,
            members=members if members is not None else team.members
        )
        
        return self.team_repository.update(self.db, db_obj=team, obj_in=update_data)
    
    def delete_team(self, team_id: int) -> Team:
        """Delete a team.
        
        Args:
            team_id: The ID of the team.
            
        Returns:
            The deleted team.
            
        Raises:
            NotFoundException: If the team is not found.
        """
        # Check if team exists
        team = self.team_repository.get_or_404(self.db, team_id)
        
        return self.team_repository.delete(self.db, id=team_id)
    
    def search_teams(
        self, 
        project_id: str, 
        search_query: str, 
        pagination: PaginationParams
    ) -> PaginationResult[Team]:
        """Search teams by name or members for a project.
        
        Args:
            project_id: The ID of the project.
            search_query: The search query.
            pagination: Pagination parameters.
            
        Returns:
            Paginated result of teams matching the search query.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Build base query
        query = self.db.query(Team).filter(Team.project_id == project_id)
        
        # Apply search
        search_fields = ["name", "members"]
        query = QueryFilter.apply_search(query, search_query, search_fields, Team)
        
        # Apply pagination
        allowed_sort_fields = ["name", "created_at", "updated_at"]
        return Paginator.paginate_query(
            query,
            pagination.page,
            pagination.per_page,
            pagination.sort_by,
            pagination.sort_order,
            allowed_sort_fields
        )
    
    def count_teams_for_project(self, project_id: str) -> int:
        """Count the number of teams for a project.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            The number of teams for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        return self.team_repository.count_by_project(self.db, project_id=project_id)

