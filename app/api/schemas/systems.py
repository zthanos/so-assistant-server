"""System API schemas."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import enum


class SystemType(str, enum.Enum):
    """System type enum."""
    internal = "internal"
    external = "external"
    integration = "integration"


class SystemBase(BaseModel):
    """Base system schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the system")
    description: Optional[str] = Field(None, description="Description of the system")
    type: SystemType = Field(..., description="Type of the system")
    dependencies: List[str] = Field(default_factory=list, description="List of system dependencies")

    @validator('dependencies')
    def validate_dependencies(cls, v):
        """Validate dependencies list."""
        if not isinstance(v, list):
            raise ValueError('Dependencies must be a list')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_deps = []
        for dep in v:
            if isinstance(dep, str) and dep.strip() and dep not in seen:
                seen.add(dep)
                unique_deps.append(dep.strip())
        
        return unique_deps

    @validator('name')
    def validate_name(cls, v):
        """Validate system name."""
        if not v or not v.strip():
            raise ValueError('System name cannot be empty')
        return v.strip()


class SystemCreate(SystemBase):
    """System creation schema."""
    project_id: str = Field(..., description="ID of the project this system belongs to")


class SystemUpdate(BaseModel):
    """System update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated name")
    description: Optional[str] = Field(None, description="Updated description")
    type: Optional[SystemType] = Field(None, description="Updated type")
    dependencies: Optional[List[str]] = Field(None, description="Updated dependencies list")

    @validator('dependencies')
    def validate_dependencies(cls, v):
        """Validate dependencies list."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError('Dependencies must be a list')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_deps = []
        for dep in v:
            if isinstance(dep, str) and dep.strip() and dep not in seen:
                seen.add(dep)
                unique_deps.append(dep.strip())
        
        return unique_deps

    @validator('name')
    def validate_name(cls, v):
        """Validate system name."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('System name cannot be empty')
        return v.strip() if v else v


class SystemUpsert(SystemBase):
    """System upsert schema for create or update operations."""
    id: Optional[int] = None 
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[SystemType] = None
    dependencies: Optional[List[str]] = None 



class SystemResponse(SystemBase):
    """System response schema."""
    id: int = Field(..., description="Unique identifier")
    project_id: str = Field(..., description="ID of the project")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SystemSearchFilters(BaseModel):
    """Schema for system search filters."""
    name: Optional[str] = Field(None, description="Filter by system name (partial match)")
    type: Optional[SystemType] = Field(None, description="Filter by system type")
    description: Optional[str] = Field(None, description="Filter by description (partial match)")
    has_dependencies: Optional[bool] = Field(None, description="Filter systems with/without dependencies")


class SystemDependencyValidation(BaseModel):
    """Schema for system dependency validation."""
    project_id: str = Field(..., description="ID of the project")
    dependencies: List[str] = Field(..., description="List of dependencies to validate")


class SystemDependencyValidationResponse(BaseModel):
    """Response schema for dependency validation."""
    valid: bool = Field(..., description="Whether all dependencies are valid")
    invalid_dependencies: List[str] = Field(default_factory=list, description="List of invalid dependencies")
    circular_dependencies: List[str] = Field(default_factory=list, description="List of circular dependencies detected")