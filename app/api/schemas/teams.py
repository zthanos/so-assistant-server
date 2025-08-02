"""Team schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TeamBase(BaseModel):
    """Base Team schema."""
    name: str
    members: Optional[str] = None

class TeamCreate(TeamBase):
    """Team creation schema."""
    project_id: str

class TeamUpdate(TeamBase):
    """Team update schema."""
    name: Optional[str] = None
    members: Optional[str] = None

class TeamResponse(TeamBase):
    """Team response schema."""
    id: int
    project_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True