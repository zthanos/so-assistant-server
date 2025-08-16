"""Project API schemas."""

import app.api.v1.endpoints
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import enum


class ProjectState(str, enum.Enum):
    """Project state enum."""
    active = "active"
    archived = "archived"
    deleted = "deleted"


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
    state: Optional[ProjectState] = ProjectState.active


class ProjectCreate(ProjectBase):
    """Project creation schema."""
    id: str


class ProjectUpdate(ProjectBase):
    """Project update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    state: Optional[ProjectState] = None


class ProjectResponse(ProjectBase):
    """Project response schema."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SolutionOutlineResponse(BaseModel):
    """Solution outline response schema."""
    latest_version: int = Field(..., description="Latest version number")
    status: str = Field(..., description="Current status")
    content: Optional[str] = Field(None, description="Solution outline content")

    class Config:
        from_attributes = True


class RequirementOutlineDocumentResponse(BaseModel):
    latest_version: int = Field(..., description="Latest version number")
    status: str = Field(..., description="Current status")
    content: Optional[str] = Field(None, description="Solution outline content")

    class Config:
        from_attributes = True
 

class RequirementsOutlineResponse(BaseModel):
    """Requirements outline response schema."""
    document: Optional["RequirementDocumentResponse"] = Field(default=None, description="Requirements document information")
    status_breakdown: dict = Field(default_factory=dict, description="Breakdown by status")
    latest_version: Optional[int] = Field(None, description="Latest requirements document version")
    items: List["RequirementItemResponse"] = Field(default_factory=list, description="Recent requirement items")

    class Config:
        from_attributes = True


class ProjectOutlineResponse(ProjectResponse):
    """Enhanced project outline response schema with all related entities."""
    solution_outline: Optional[SolutionOutlineResponse] = Field(default=None, description="Solution outline information")
    requirements_outline: Optional[RequirementOutlineDocumentResponse] = Field(default=None, description="Requirements summary")

    

    
    systems: List["SystemResponse"] = Field(default_factory=list, description="Project systems")
    teams: List["TeamResponse"] = Field(default_factory=list, description="Project teams")
    diagrams: List["DiagramResponse"] = Field(default_factory=list, description="Project diagrams")
    tasks: List["TaskResponse"] = Field(default_factory=list, description="Project tasks")
    
    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_latest(cls, project) -> "ProjectOutlineResponse":
        solution = project.solution_outlines[0] if project.solution_outlines else None
        requirement = project.requirement_documents[0] if project.requirement_documents else None

        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            code=project.code,
            state=project.state,
            created_at=project.created_at,
            updated_at=project.updated_at,
            solution_outline=SolutionOutlineResponse(
                latest_version=solution.version,
                status=solution.status,
                content=solution.content
            ) if solution else None,
            requirements_outline=RequirementOutlineDocumentResponse(
                latest_version=requirement.version,
                status=requirement.status,
                content=requirement.content
            ) if requirement else None,
            systems=project.systems,
            teams=project.teams,
            diagrams=project.diagrams,
            tasks=project.tasks
        )
# Forward references will be resolved after importing other schemas
try:
    from app.api.schemas.requirements import RequirementItemResponse
    from app.api.schemas.requirements import RequirementDocumentResponse
    from app.api.schemas.diagrams import DiagramResponse
    from app.api.schemas.teams import TeamResponse
    from app.api.schemas.systems import SystemResponse
    from app.api.schemas.tasks import TaskResponse
    ProjectOutlineResponse.model_rebuild()
    RequirementsOutlineResponse.model_rebuild()
except ImportError:
    # Handle circular import by using string annotations
    pass