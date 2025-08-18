"""Team service implementation."""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import get_db
from app.repositories.team_repository import team_repository
from app.repositories.project_repository import project_repository
from app.domain.models.teams import Team
from app.api.schemas.teams import (
    TeamCreate, TeamUpdate, TeamUpsert, TeamResponse, 
    TeamSearchFilters
)
from app.core.exceptions import NotFoundException, BadRequestException, DatabaseException
from app.exceptions.systems_teams_exceptions import (
    TeamNotFoundException, DuplicateTeamException, TeamValidationException,
    TeamMemberValidationException, TeamOperationException
)
from app.utils.pagination import PaginationParams, PaginationResult, Paginator
from app.utils.filtering import FilterCondition, QueryFilter

logger = logging.getLogger(__name__)


class TeamService:
    """Service for team operations with business logic."""
    
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with dependencies.
        
        Args:
            db: The database session.
        """
        self.db = db
        self.repository = team_repository
        self.project_repository = project_repository
    
    def create_team(self, db: Session, team_data: TeamCreate) -> TeamResponse:
        """Create a new team with project validation.
        
        Args:
            db: Database session.
            team_data: The team creation data.
            
        Returns:
            The created team response.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            BadRequestException: If the team data is invalid or name already exists.
            DatabaseException: If there's a database error.
        """
        logger.info(f"Creating team for project {team_data.project_id}: {team_data.name}")
        
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, team_data.project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {team_data.project_id} not found",
                    resource_type="Project",
                    resource_id=team_data.project_id
                )
            
            # Check if team name already exists in the project
            existing_team = self.repository.get_by_project_and_name(
                db, team_data.project_id, team_data.name
            )
            if existing_team:
                raise DuplicateTeamException(
                    f"Team with name '{team_data.name}' already exists in project {team_data.project_id}",
                    team_name=team_data.name,
                    project_id=team_data.project_id
                )
            
            # Validate member names if provided
            if team_data.members:
                validation_result = self.repository.validate_member_names(team_data.members)
                if not validation_result["valid"]:
                    error_details = []
                    if validation_result["invalid_members"]:
                        error_details.append(f"Invalid members: {', '.join(validation_result['invalid_members'])}")
                    if validation_result["duplicate_members"]:
                        error_details.append(f"Duplicate members: {', '.join(validation_result['duplicate_members'])}")
                    raise BadRequestException(f"Member validation failed: {'; '.join(error_details)}")
            
            # Validate responsibilities (check for empty strings)
            if team_data.responsibilities:
                invalid_responsibilities = [resp for resp in team_data.responsibilities if not resp or not resp.strip()]
                if invalid_responsibilities:
                    raise BadRequestException("Responsibilities cannot be empty or contain only whitespace")
            
            # Create the team
            team = self.repository.create(db, obj_in=team_data)
            
            logger.info(f"Successfully created team {team.name} with ID {team.id}")
            return self._to_response(team)
            
        except (NotFoundException, DuplicateTeamException, TeamMemberValidationException, TeamValidationException):
            raise
        except Exception as e:
            logger.error(f"Error creating team {team_data.name}: {e}")
            raise TeamOperationException(
                f"Error creating team: {str(e)}", 
                operation="create",
                team_name=team_data.name,
                project_id=team_data.project_id,
                status_code=500
            )
    
    def get_team(self, db: Session, team_id: int) -> TeamResponse:
        """Get a team by ID.
        
        Args:
            db: Database session.
            team_id: The team ID.
            
        Returns:
            The team response.
            
        Raises:
            NotFoundException: If the team doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            team = self.repository.get_or_404(db, team_id)
            return self._to_response(team)
            
        except NotFoundException:
            raise TeamNotFoundException(
                f"Team with ID {team_id} not found",
                team_id=team_id
            )
        except Exception as e:
            logger.error(f"Error retrieving team {team_id}: {e}")
            raise TeamOperationException(
                f"Error retrieving team: {str(e)}", 
                operation="get",
                status_code=500
            )
    
    def upsert_team(self, db: Session, team_data: TeamUpsert) -> TeamResponse:
        """Create or update a team using project_id + name as natural key.
        
        Args:
            db: Database session.
            team_data: The team upsert data.
            
        Returns:
            The created or updated team response.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            BadRequestException: If the team data is invalid.
            DatabaseException: If there's a database error.
        """
        logger.info(f"Upserting team for project {team_data.project_id}: {team_data.name}")
        
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, team_data.project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {team_data.project_id} not found",
                    resource_type="Project",
                    resource_id=team_data.project_id
                )
            
            # Validate member names if provided
            if team_data.members:
                validation_result = self.repository.validate_member_names(team_data.members)
                if not validation_result["valid"]:
                    error_details = []
                    if validation_result["invalid_members"]:
                        error_details.append(f"Invalid members: {', '.join(validation_result['invalid_members'])}")
                    if validation_result["duplicate_members"]:
                        error_details.append(f"Duplicate members: {', '.join(validation_result['duplicate_members'])}")
                    raise BadRequestException(f"Member validation failed: {'; '.join(error_details)}")
            
            # Validate responsibilities (check for empty strings)
            if team_data.responsibilities:
                invalid_responsibilities = [resp for resp in team_data.responsibilities if not resp or not resp.strip()]
                if invalid_responsibilities:
                    raise BadRequestException("Responsibilities cannot be empty or contain only whitespace")
            
            # Perform upsert
            team_dict = team_data.dict(exclude={'project_id'})
            team = self.repository.upsert_team(
                db, team_data.project_id, team_data.name, team_dict
            )
            
            logger.info(f"Successfully upserted team {team.name} with ID {team.id}")
            return self._to_response(team)
            
        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error upserting team {team_data.name}: {e}")
            raise DatabaseException(f"Error upserting team: {str(e)}", original_exception=e)
    
    def update_team(self, db: Session, team_id: int, team_data: TeamUpdate) -> TeamResponse:
        """Update an existing team.
        
        Args:
            db: Database session.
            team_id: The team ID.
            team_data: The team update data.
            
        Returns:
            The updated team response.
            
        Raises:
            NotFoundException: If the team doesn't exist.
            BadRequestException: If the update data is invalid.
            DatabaseException: If there's a database error.
        """
        logger.info(f"Updating team {team_id}")
        
        try:
            # Get the existing team
            existing_team = self.repository.get_or_404(db, team_id)
            
            # If name is being updated, check for duplicates
            if team_data.name and team_data.name != existing_team.name:
                duplicate_team = self.repository.get_by_project_and_name(
                    db, existing_team.project_id, team_data.name
                )
                if duplicate_team:
                    raise BadRequestException(
                        f"Team with name '{team_data.name}' already exists in project {existing_team.project_id}"
                    )
            
            # Validate member names if provided
            if team_data.members is not None:
                validation_result = self.repository.validate_member_names(team_data.members)
                if not validation_result["valid"]:
                    error_details = []
                    if validation_result["invalid_members"]:
                        error_details.append(f"Invalid members: {', '.join(validation_result['invalid_members'])}")
                    if validation_result["duplicate_members"]:
                        error_details.append(f"Duplicate members: {', '.join(validation_result['duplicate_members'])}")
                    raise BadRequestException(f"Member validation failed: {'; '.join(error_details)}")
            
            # Validate responsibilities if provided
            if team_data.responsibilities is not None:
                invalid_responsibilities = [resp for resp in team_data.responsibilities if not resp or not resp.strip()]
                if invalid_responsibilities:
                    raise BadRequestException("Responsibilities cannot be empty or contain only whitespace")
            
            # Update the team
            team = self.repository.update_by_id(db, id=team_id, obj_in=team_data)
            
            logger.info(f"Successfully updated team {team.name} with ID {team.id}")
            return self._to_response(team)
            
        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error updating team {team_id}: {e}")
            raise DatabaseException(f"Error updating team: {str(e)}", original_exception=e)
    
    def delete_team(self, db: Session, team_id: int) -> bool:
        """Delete a team.
        
        Args:
            db: Database session.
            team_id: The team ID.
            
        Returns:
            True if the team was deleted.
            
        Raises:
            NotFoundException: If the team doesn't exist.
            DatabaseException: If there's a database error.
        """
        logger.info(f"Deleting team {team_id}")
        
        try:
            # Check if team exists and get its details for logging
            team = self.repository.get_or_404(db, team_id)
            team_name = team.name
            
            # Delete the team
            self.repository.delete(db, id=team_id)
            
            logger.info(f"Successfully deleted team {team_name} with ID {team_id}")
            return True
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting team {team_id}: {e}")
            raise DatabaseException(f"Error deleting team: {str(e)}", original_exception=e)
    
    def get_teams_for_project(
        self, 
        project_id: str, 
        pagination: PaginationParams,
        filters: Optional[List[FilterCondition]] = None,
        search: Optional[str] = None
    ) -> PaginationResult[TeamResponse]:
        """Get all Teams for a project with pagination and filtering.
        
        Args:
            project_id: The ID of the project.
            pagination: Pagination parameters.
            filters: List of filter conditions.
            search: Search term.
            
        Returns:
            Paginated result of Teams for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Build base query
        query = self.db.query(Team).filter(Team.project_id == project_id)
        
        # Apply filters
        if filters:
            allowed_fields = ["name", "role", "created_at", "updated_at"]
            query = QueryFilter.apply_filters(query, filters, Team, allowed_fields)
        
        # Apply search
        if search:
            search_fields = ["name", "role"]
            query = QueryFilter.apply_search(query, search, search_fields, Team)
        
        # Apply pagination
        allowed_sort_fields = ["name", "role", "created_at", "updated_at"]
        result = Paginator.paginate_query(
            query,
            pagination.page,
            pagination.per_page,
            pagination.sort_by,
            pagination.sort_order,
            allowed_sort_fields
        )
        
        # Convert SQLAlchemy models to Pydantic models
        team_responses = to_response(TeamResponse, result.items)
        
        return PaginationResult(
            items=team_responses,
            total=result.total,
            page=result.page,
            per_page=result.per_page,
            pages=result.pages,
            has_next=result.has_next,
            has_prev=result.has_prev
        )


    def list_teams(
        self, 
        db: Session, 
        project_id: str, 
        filters: Optional[TeamSearchFilters] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[TeamResponse]:
        """List teams for a project with optional filtering.
        
        Args:
            db: Database session.
            project_id: The project ID.
            filters: Optional search filters.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of team responses.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            # Get teams based on filters
            if filters:
                teams = self.repository.search_teams(db, project_id, filters, skip, limit)
            else:
                teams = self.repository.get_by_project(db, project_id, skip, limit)
            
            return [self._to_response(team) for team in teams]
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error listing teams for project {project_id}: {e}")
            raise DatabaseException(f"Error listing teams: {str(e)}", original_exception=e)
    
    def get_teams_by_role(
        self, 
        db: Session, 
        project_id: str, 
        role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TeamResponse]:
        """Get teams by project and role.
        
        Args:
            db: Database session.
            project_id: The project ID.
            role: The role to filter by.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of team responses.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            teams = self.repository.get_teams_by_role(db, project_id, role, skip, limit)
            return [self._to_response(team) for team in teams]
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting teams with role {role} for project {project_id}: {e}")
            raise DatabaseException(f"Error getting teams by role: {str(e)}", original_exception=e)
    
    def get_teams_with_member(
        self, 
        db: Session, 
        project_id: str, 
        member_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TeamResponse]:
        """Get teams that have a specific member.
        
        Args:
            db: Database session.
            project_id: The project ID.
            member_name: The name of the member to search for.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of team responses.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            teams = self.repository.get_teams_with_member(db, project_id, member_name, skip, limit)
            return [self._to_response(team) for team in teams]
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting teams with member {member_name} for project {project_id}: {e}")
            raise DatabaseException(f"Error getting teams with member: {str(e)}", original_exception=e)
    
    def count_teams(
        self, 
        db: Session, 
        project_id: str, 
        filters: Optional[TeamSearchFilters] = None
    ) -> int:
        """Count teams for a project with optional filtering.
        
        Args:
            db: Database session.
            project_id: The project ID.
            filters: Optional search filters.
            
        Returns:
            Number of teams matching the criteria.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            return self.repository.count_by_project(db, project_id, filters)
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error counting teams for project {project_id}: {e}")
            raise DatabaseException(f"Error counting teams: {str(e)}", original_exception=e)
    
    def validate_team_members(self, members: List[str]) -> Dict[str, Any]:
        """Validate team member names.
        
        Args:
            members: List of member names to validate.
            
        Returns:
            Dictionary with validation results.
            
        Raises:
            DatabaseException: If there's an error during validation.
        """
        try:
            return self.repository.validate_member_names(members)
            
        except Exception as e:
            logger.error(f"Error validating team members: {e}")
            raise DatabaseException(f"Error validating team members: {str(e)}", original_exception=e)
    
    def analyze_team_responsibilities(
        self, 
        db: Session, 
        project_id: str
    ) -> Dict[str, Any]:
        """Analyze team responsibilities for overlaps and gaps.
        
        Args:
            db: Database session.
            project_id: The project ID.
            
        Returns:
            Dictionary with responsibility analysis.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            # Get all teams for the project
            teams = self.repository.get_by_project(db, project_id, skip=0, limit=1000)
            
            # Analyze responsibilities
            all_responsibilities = []
            team_responsibilities = {}
            
            for team in teams:
                if team.responsibilities:
                    team_responsibilities[team.name] = team.responsibilities
                    all_responsibilities.extend(team.responsibilities)
            
            # Find overlapping responsibilities
            responsibility_counts = {}
            for resp in all_responsibilities:
                responsibility_counts[resp] = responsibility_counts.get(resp, 0) + 1
            
            overlapping_responsibilities = {
                resp: count for resp, count in responsibility_counts.items() if count > 1
            }
            
            return {
                "total_teams": len(teams),
                "teams_with_responsibilities": len(team_responsibilities),
                "unique_responsibilities": len(set(all_responsibilities)),
                "total_responsibility_assignments": len(all_responsibilities),
                "overlapping_responsibilities": overlapping_responsibilities,
                "team_responsibilities": team_responsibilities
            }
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error analyzing team responsibilities for project {project_id}: {e}")
            raise DatabaseException(f"Error analyzing team responsibilities: {str(e)}", original_exception=e)
    
    def _to_response(self, team: Team) -> TeamResponse:
        """Convert a Team model to TeamResponse.
        
        Args:
            team: The team model.
            
        Returns:
            The team response.
        """
        return TeamResponse(
            id=team.id,
            project_id=team.project_id,
            name=team.name,
            role=team.role,
            members=team.members or [],
            responsibilities=team.responsibilities or [],
            created_at=team.created_at,
            updated_at=team.updated_at
        )
def to_response(model_cls, items):
    return [model_cls.model_validate(i, from_attributes=True) for i in items]        