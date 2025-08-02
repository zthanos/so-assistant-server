"""Requirement API schemas."""

from pydantic import BaseModel
from typing import Optional
import enum


class RequirementCategory(str, enum.Enum):
    """Requirement category enum."""
    functional = "Functional"
    non_functional = "Non-Functional"


class RequirementStatus(str, enum.Enum):
    """Requirement status enum."""
    pending = "Pending"
    approved = "Approved"
    implemented = "Implemented"


class RequirementBase(BaseModel):
    """Base requirement schema."""
    description: str
    category: RequirementCategory


class RequirementCreate(RequirementBase):
    """Requirement creation schema."""
    pass


class RequirementUpdate(BaseModel):
    """Requirement update schema."""
    description: Optional[str] = None
    category: Optional[RequirementCategory] = None
    status: Optional[RequirementStatus] = None


class RequirementResponse(RequirementBase):
    """Requirement response schema."""
    id: int
    project_id: str
    status: RequirementStatus
    
    class Config:
        from_attributes = True