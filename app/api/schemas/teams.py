"""Team API schemas."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class TeamBase(BaseModel):
    """Base team schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the team")
    role: str = Field(..., min_length=1, max_length=255, description="Role of the team")
    members: List[str] = Field(default_factory=list, description="List of team member names")
    responsibilities: List[str] = Field(default_factory=list, description="List of team responsibilities")

    @validator('members')
    def validate_members(cls, v):
        """Validate members list."""
        if not isinstance(v, list):
            raise ValueError('Members must be a list')
        
        # Remove duplicates and empty strings while preserving order
        seen = set()
        unique_members = []
        for member in v:
            if isinstance(member, str) and member.strip() and member not in seen:
                seen.add(member)
                unique_members.append(member.strip())
        
        return unique_members

    @validator('responsibilities')
    def validate_responsibilities(cls, v):
        """Validate responsibilities list."""
        if not isinstance(v, list):
            raise ValueError('Responsibilities must be a list')
        
        # Remove duplicates and empty strings while preserving order
        seen = set()
        unique_responsibilities = []
        for responsibility in v:
            if isinstance(responsibility, str) and responsibility.strip() and responsibility not in seen:
                seen.add(responsibility)
                unique_responsibilities.append(responsibility.strip())
        
        return unique_responsibilities

    @validator('name')
    def validate_name(cls, v):
        """Validate team name."""
        if not v or not v.strip():
            raise ValueError('Team name cannot be empty')
        return v.strip()

    @validator('role')
    def validate_role(cls, v):
        """Validate team role."""
        if not v or not v.strip():
            raise ValueError('Team role cannot be empty')
        return v.strip()


class TeamCreate(TeamBase):
    """Team creation schema."""
    project_id: str = Field(..., description="ID of the project this team belongs to")


class TeamUpdate(BaseModel):
    """Team update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated name")
    role: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated role")
    members: Optional[List[str]] = Field(None, description="Updated members list")
    responsibilities: Optional[List[str]] = Field(None, description="Updated responsibilities list")

    @validator('members')
    def validate_members(cls, v):
        """Validate members list."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError('Members must be a list')
        
        # Remove duplicates and empty strings while preserving order
        seen = set()
        unique_members = []
        for member in v:
            if isinstance(member, str) and member.strip() and member not in seen:
                seen.add(member)
                unique_members.append(member.strip())
        
        return unique_members

    @validator('responsibilities')
    def validate_responsibilities(cls, v):
        """Validate responsibilities list."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError('Responsibilities must be a list')
        
        # Remove duplicates and empty strings while preserving order
        seen = set()
        unique_responsibilities = []
        for responsibility in v:
            if isinstance(responsibility, str) and responsibility.strip() and responsibility not in seen:
                seen.add(responsibility)
                unique_responsibilities.append(responsibility.strip())
        
        return unique_responsibilities

    @validator('name')
    def validate_name(cls, v):
        """Validate team name."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Team name cannot be empty')
        return v.strip() if v else v

    @validator('role')
    def validate_role(cls, v):
        """Validate team role."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Team role cannot be empty')
        return v.strip() if v else v


class TeamUpsert(TeamBase):
    """Team upsert schema for create or update operations."""
    project_id: str = Field(..., description="ID of the project this team belongs to")


class TeamResponse(TeamBase):
    """Team response schema."""
    id: int = Field(..., description="Unique identifier")
    project_id: str = Field(..., description="ID of the project")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TeamSearchFilters(BaseModel):
    """Schema for team search filters."""
    name: Optional[str] = Field(None, description="Filter by team name (partial match)")
    role: Optional[str] = Field(None, description="Filter by team role (partial match)")
    member: Optional[str] = Field(None, description="Filter by team member name (partial match)")
    responsibility: Optional[str] = Field(None, description="Filter by responsibility (partial match)")