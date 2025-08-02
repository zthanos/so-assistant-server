"""Architecture Decision Record (ADR) schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ADRBase(BaseModel):
    """Base ADR schema."""
    title: str
    content: str

class ADRCreate(ADRBase):
    """ADR creation schema."""
    project_id: str

class ADRUpdate(ADRBase):
    """ADR update schema."""
    title: Optional[str] = None
    content: Optional[str] = None

class ADRResponse(ADRBase):
    """ADR response schema."""
    id: int
    project_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True