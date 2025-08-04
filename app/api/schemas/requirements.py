"""Requirement API schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
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


class SourceType(str, enum.Enum):
    """Source type for requirements."""
    manual = "manual"
    pdf_upload = "pdf_upload"


class RequirementDocumentStatus(str, enum.Enum):
    """Requirement document status."""
    draft = "draft"
    published = "published"
    archived = "archived"


# Legacy requirement schemas (kept for backward compatibility)
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


# New requirement document schemas with versioning
class RequirementDocumentBase(BaseModel):
    """Base requirement document schema."""
    content: str = Field(..., description="Markdown content of the requirements document")
    status: Optional[RequirementDocumentStatus] = Field(
        RequirementDocumentStatus.draft, 
        description="Status of the requirements document"
    )


class RequirementDocumentCreate(RequirementDocumentBase):
    """Requirement document creation schema."""
    project_id: str = Field(..., description="ID of the project")
    source_type: Optional[SourceType] = Field(
        SourceType.manual, 
        description="Source type of the requirements"
    )
    original_filename: Optional[str] = Field(
        None, 
        description="Original filename for PDF uploads"
    )


class RequirementDocumentUpdate(BaseModel):
    """Requirement document update schema."""
    content: Optional[str] = Field(None, description="Updated markdown content")
    status: Optional[RequirementDocumentStatus] = Field(
        None, 
        description="Updated status"
    )


class RequirementDocumentUpsert(RequirementDocumentBase):
    """Requirement document upsert schema for create or update operations."""
    source_type: Optional[SourceType] = Field(
        SourceType.manual, 
        description="Source type of the requirements"
    )
    original_filename: Optional[str] = Field(
        None, 
        description="Original filename for PDF uploads"
    )


class RequirementDocumentResponse(RequirementDocumentBase):
    """Requirement document response schema."""
    id: int = Field(..., description="Unique identifier")
    project_id: str = Field(..., description="ID of the project")
    version: int = Field(..., description="Version number")
    source_type: SourceType = Field(..., description="Source type of the requirements")
    original_filename: Optional[str] = Field(None, description="Original filename for PDF uploads")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class RequirementDocumentVersionInfo(BaseModel):
    """Requirement document version info schema."""
    version: int = Field(..., description="Version number")
    status: RequirementDocumentStatus = Field(..., description="Document status")
    source_type: SourceType = Field(..., description="Source type")
    original_filename: Optional[str] = Field(None, description="Original filename")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }