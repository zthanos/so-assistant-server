"""Notes schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class NoteBase(BaseModel):
    """Base Note schema."""
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class NoteCreate(NoteBase):
    """Note creation schema."""
    project_id: str

class NoteUpdate(BaseModel):
    """Note update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class NoteUpsert(BaseModel):
    """Note upsert schema for create or update operations."""
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    note_id: Optional[int] = None  # If provided, update existing note; if None, create new

class NoteResponse(NoteBase):
    """Note response schema."""
    id: int
    project_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }