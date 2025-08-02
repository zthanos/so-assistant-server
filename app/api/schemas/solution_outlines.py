"""Solution Outline schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import enum

class SolutionOutlineStatus(str, enum.Enum):
    """Solution Outline status enum."""
    draft = "draft"
    published = "published"
    archived = "archived"

class SolutionOutlineBase(BaseModel):
    """Base Solution Outline schema."""
    content: str
    status: Optional[SolutionOutlineStatus] = SolutionOutlineStatus.draft

class SolutionOutlineCreate(SolutionOutlineBase):
    """Solution Outline creation schema."""
    project_id: str

class SolutionOutlineUpdate(SolutionOutlineBase):
    """Solution Outline update schema."""
    content: Optional[str] = None
    status: Optional[SolutionOutlineStatus] = None

class SolutionOutlineResponse(SolutionOutlineBase):
    """Solution Outline response schema."""
    id: int
    project_id: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SolutionOutlineVersionInfo(BaseModel):
    """Solution Outline version info schema."""
    version: int
    created_at: datetime
    status: SolutionOutlineStatus

    class Config:
        from_attributes = True