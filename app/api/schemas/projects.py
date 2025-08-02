"""Project API schemas."""

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


class ProjectOutlineResponse(ProjectResponse):
    """Project outline response schema with related entities."""
    requirements: List["RequirementResponse"] = Field(default_factory=list)
    diagrams: List["DiagramResponse"] = Field(default_factory=list)
    teams: List["TeamResponse"] = Field(default_factory=list)
    tasks: List["TaskResponse"] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


# Forward references will be resolved after importing other schemas
try:
    from app.api.schemas.requirements import RequirementResponse
    from app.api.schemas.diagrams import DiagramResponse
    from app.api.schemas.teams import TeamResponse
    from app.api.schemas.tasks import TaskResponse
    ProjectOutlineResponse.model_rebuild()
except ImportError:
    # Handle circular import by using string annotations
    pass