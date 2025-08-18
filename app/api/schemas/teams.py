"""Team API schemas."""

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    FieldValidationInfo,
    model_validator,
    ConfigDict,
    field_serializer,
    validator
)
from typing import List, Optional, Any
from datetime import datetime


class TeamBase(BaseModel):
    """Base team schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Name of the team")
    role: str = Field(..., min_length=1, max_length=255, description="Role of the team")
    members: List[str] = Field(
        default_factory=list, description="List of team member names"
    )
    responsibilities: List[str] = Field(
        default_factory=list, description="List of team responsibilities"
    )

    @field_validator("name", "role", mode="before")
    @classmethod
    def validate_and_strip_non_empty(cls, v: Any, info: FieldValidationInfo) -> str:
        if not isinstance(v, str):
            raise TypeError(f"{info.field_name} must be a string")
        s = v.strip()
        if not s:
            raise ValueError(f"Team {info.field_name} cannot be empty")
        return s

    @field_validator("members", "responsibilities", mode="before")
    @classmethod
    def validate_string_list(cls, v: Any, info: FieldValidationInfo) -> List[str]:
        if v is None:
            return []
        if not isinstance(v, list):
            # δέξου tuple/set και κάν’ τα list, αλλιώς error
            if isinstance(v, (tuple, set)):
                v = list(v)
            else:
                raise TypeError(f"{info.field_name} must be a list")
        seen = set()
        unique: List[str] = []
        for item in v:
            if not isinstance(item, str):
                raise TypeError(f"Each item in {info.field_name} must be a string")
            s = item.strip()
            if s and s not in seen:
                seen.add(s)
                unique.append(s)
        return unique


# class TeamBase(BaseModel):
#     """Base team schema."""
#     name: str = Field(..., min_length=1, max_length=255, description="Name of the team")
#     role: str = Field(..., min_length=1, max_length=255, description="Role of the team")
#     members: List[str] = Field(default_factory=list, description="List of team member names")
#     responsibilities: List[str] = Field(default_factory=list, description="List of team responsibilities")

#     @validator('members')
#     def validate_members(cls, v):
#         """Validate members list."""
#         if not isinstance(v, list):
#             raise ValueError('Members must be a list')

#         # Remove duplicates and empty strings while preserving order
#         seen = set()
#         unique_members = []
#         for member in v:
#             if isinstance(member, str) and member.strip() and member not in seen:
#                 seen.add(member)
#                 unique_members.append(member.strip())

#         return unique_members

#     @validator('responsibilities')
#     def validate_responsibilities(cls, v):
#         """Validate responsibilities list."""
#         if not isinstance(v, list):
#             raise ValueError('Responsibilities must be a list')

#         # Remove duplicates and empty strings while preserving order
#         seen = set()
#         unique_responsibilities = []
#         for responsibility in v:
#             if isinstance(responsibility, str) and responsibility.strip() and responsibility not in seen:
#                 seen.add(responsibility)
#                 unique_responsibilities.append(responsibility.strip())

#         return unique_responsibilities

#     @validator('name')
#     def validate_name(cls, v):
#         """Validate team name."""
#         if not v or not v.strip():
#             raise ValueError('Team name cannot be empty')
#         return v.strip()

#     @validator('role')
#     def validate_role(cls, v):
#         """Validate team role."""
#         if not v or not v.strip():
#             raise ValueError('Team role cannot be empty')
#         return v.strip()


class TeamCreate(TeamBase):
    """Team creation schema."""

    project_id: str = Field(..., description="ID of the project this team belongs to")


class TeamUpdate(BaseModel):
    """Team update schema."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Updated name"
    )
    role: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Updated role"
    )
    members: Optional[List[str]] = Field(None, description="Updated members list")
    responsibilities: Optional[List[str]] = Field(
        None, description="Updated responsibilities list"
    )

    @validator("members")
    def validate_members(cls, v):
        """Validate members list."""
        if v is None:
            return v

        if not isinstance(v, list):
            raise ValueError("Members must be a list")

        # Remove duplicates and empty strings while preserving order
        seen = set()
        unique_members = []
        for member in v:
            if isinstance(member, str) and member.strip() and member not in seen:
                seen.add(member)
                unique_members.append(member.strip())

        return unique_members

    @validator("responsibilities")
    def validate_responsibilities(cls, v):
        """Validate responsibilities list."""
        if v is None:
            return v

        if not isinstance(v, list):
            raise ValueError("Responsibilities must be a list")

        # Remove duplicates and empty strings while preserving order
        seen = set()
        unique_responsibilities = []
        for responsibility in v:
            if (
                isinstance(responsibility, str)
                and responsibility.strip()
                and responsibility not in seen
            ):
                seen.add(responsibility)
                unique_responsibilities.append(responsibility.strip())

        return unique_responsibilities

    @validator("name")
    def validate_name(cls, v):
        """Validate team name."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Team name cannot be empty")
        return v.strip() if v else v

    @validator("role")
    def validate_role(cls, v):
        """Validate team role."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Team role cannot be empty")
        return v.strip() if v else v


class TeamUpsert(TeamBase):
    """Team upsert schema for create or update operations."""

    project_id: str = Field(..., description="ID of the project this team belongs to")


class TeamResponse(TeamBase):
    id: int = Field(..., description="Unique identifier")
    project_id: str = Field(..., description="ID of the project")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_dt(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat(timespec="seconds") if value else None


class TeamSearchFilters(BaseModel):
    """Schema for team search filters."""

    name: Optional[str] = Field(None, description="Filter by team name (partial match)")
    role: Optional[str] = Field(None, description="Filter by team role (partial match)")
    member: Optional[str] = Field(
        None, description="Filter by team member name (partial match)"
    )
    responsibility: Optional[str] = Field(
        None, description="Filter by responsibility (partial match)"
    )
