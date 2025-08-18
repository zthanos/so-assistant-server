"""Architecture Decision Record (ADR) schemas."""
from pydantic import BaseModel, Field, model_validator, ConfigDict, field_serializer
from typing import Optional, List, Literal, Union
from datetime import datetime

class ADRBase(BaseModel):
    """Base ADR schema."""
    title: str
    content: str
    status: str = "proposed"
    context: Optional[str] = None
    decision: Optional[str] = None
    consequences: Optional[str] = None
    alternatives: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class ADRCreate(ADRBase):
    """ADR creation schema."""
    project_id: str

class ADRUpdate(BaseModel):
    """ADR update schema."""
    id: int
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    context: Optional[str] = None    
    decision: Optional[str] = None
    consequences: Optional[str] = None
    alternatives: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None  

    @model_validator(mode="after")
    def require_some_change(self):
        if all(
            getattr(self, f) is None
            for f in ("title","content","status","context","decision",
                      "consequences","alternatives","author","tags")
        ):
            raise ValueError("ADRUpdate requires at least one field to change.")
        return self    

class ADRUpsert(BaseModel):
    """ADR upsert schema for create or update operations."""
    title: Optional[str] = None
    content: Optional[str] = None
    context: Optional[str] = None
    decision: Optional[str] = None
    consequences: Optional[str] = None
    alternatives: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None   
    id: Optional[int] = None  # If provided, update existing ADR; if None, create new

class ADRResponse(ADRBase):
    """ADR response schema."""
    id: int
    project_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    # Custom JSON serialization for datetime
    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_dt(self, value: datetime) -> str:
        return value.isoformat() if value else None

# ---------- Upsert (clear, explicit) ----------
class ADRUpsertCreate(ADRCreate):
    kind: Literal["create"] = "create"

class ADRUpsertUpdate(ADRUpdate):
    kind: Literal["update"] = "update"

ADRUpsert = Union[ADRUpsertCreate, ADRUpsertUpdate]

# # Extended schemas for future use (after migration)
# class ADRExtendedBase(BaseModel):
#     """Extended ADR schema with all fields (for future use)."""
#     title: str
#     status: str = "proposed"
#     context: Optional[str] = None
#     decision: Optional[str] = None
#     consequences: Optional[str] = None
#     alternatives: Optional[str] = None
#     author: Optional[str] = None
#     tags: List[str] = Field(default_factory=list)
#     content: Optional[str] = None

# class ADRExtendedResponse(ADRExtendedBase):
#     """Extended ADR response schema (for future use)."""
#     id: int
#     project_id: str
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True
#         json_encoders = {
#             datetime: lambda v: v.isoformat() if v else None
#         }




        