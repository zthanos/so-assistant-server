"""Requirement API schemas."""

from pydantic import BaseModel, Field, validator, ValidationError
from typing import Optional, List, Dict, Any
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


# Requirement Item schemas for individual requirement tracking
class RequirementItemStatus(str, enum.Enum):
    """Requirement item status enum."""
    new = "new"
    accepted = "accepted"
    rejected = "rejected"


class RequirementItemPriority(str, enum.Enum):
    """Requirement item priority enum."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RequirementItemBase(BaseModel):
    """Base requirement item schema."""
    title: str = Field(..., min_length=1, max_length=500, description="Title of the requirement item")
    description: str = Field(..., min_length=1, description="Detailed description of the requirement")
    priority: RequirementItemPriority = Field(
        RequirementItemPriority.medium, 
        description="Priority level of the requirement"
    )


class RequirementItemCreate(RequirementItemBase):
    """Requirement item creation schema."""
    project_id: str = Field(..., description="ID of the project this requirement belongs to")


class RequirementItemUpdate(BaseModel):
    """Requirement item update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Updated title")
    description: Optional[str] = Field(None, min_length=1, description="Updated description")
    priority: Optional[RequirementItemPriority] = Field(None, description="Updated priority")
    status: Optional[RequirementItemStatus] = Field(None, description="Updated status")


class RequirementItemUpsert(BaseModel):
    """Requirement item upsert schema for create or update operations."""
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=500, description="Title of the requirement item")
    description: str = Field(..., min_length=1, description="Detailed description of the requirement")
    priority: RequirementItemPriority = Field(
        RequirementItemPriority.medium, 
        description="Priority level of the requirement"
    )
    status: Optional[RequirementItemStatus] = Field(None, description="Status of the requirement")


class RequirementItemBatchUpsert(BaseModel):
    """Schema for batch upsert operations."""
    items: List[Dict[str, Any]] = Field(
        ..., 
        description="List of requirement items to upsert, each with an 'id' and upsert data",
        min_items=1,
        max_items=100
    )
    
    @validator('items')
    def validate_items(cls, v):
        """Validate that each item has required fields."""
        for i, item in enumerate(v):
            if 'id' not in item:
                raise ValueError(f"Item at index {i} missing required 'id' field")
            if not isinstance(item['id'], int):
                raise ValueError(f"Item at index {i} 'id' must be an integer")
            
            # Validate the upsert data
            try:
                upsert_data = {k: v for k, v in item.items() if k != 'id'}
                RequirementItemUpsert(**upsert_data)
            except ValidationError as e:
                raise ValueError(f"Item at index {i} has invalid upsert data: {e}")
        
        return v


class RequirementItemBatchUpsertResponse(BaseModel):
    """Response schema for batch upsert operations."""
    success_count: int = Field(..., description="Number of items successfully upserted")
    error_count: int = Field(..., description="Number of items that failed to upsert")
    results: List[Dict[str, Any]] = Field(..., description="Detailed results for each item")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success_count": 2,
                "error_count": 1,
                "results": [
                    {
                        "id": 1,
                        "status": "success",
                        "item": {
                            "id": 1,
                            "project_id": "project-123",
                            "title": "Updated Requirement",
                            "description": "Updated description",
                            "priority": "high",
                            "status": "new"
                        }
                    },
                    {
                        "id": 2,
                        "status": "error",
                        "error": "Project with id invalid-project not found"
                    }
                ]
            }
        }


class RequirementItemResponse(RequirementItemBase):
    """Requirement item response schema."""
    id: int = Field(..., description="Unique identifier")
    project_id: str = Field(..., description="ID of the project")
    status: RequirementItemStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class RequirementItemStatusUpdate(BaseModel):
    """Schema for updating requirement item status only."""
    status: RequirementItemStatus = Field(..., description="New status for the requirement item")


# AI Suggestion schemas
class RequirementSuggestionRequest(BaseModel):
    """Schema for requirement suggestion requests."""
    project_id: str = Field(..., description="ID of the project to generate suggestions for")
    max_suggestions: Optional[int] = Field(
        default=10, 
        ge=1, 
        le=50, 
        description="Maximum number of suggestions to generate"
    )


class RequirementSuggestion(BaseModel):
    """Schema for individual requirement suggestions."""
    title: str = Field(..., description="Suggested requirement title")
    description: str = Field(..., description="Suggested requirement description")
    priority: RequirementItemPriority = Field(..., description="Suggested priority level")
    rationale: str = Field(..., description="AI explanation for why this requirement is suggested")


class RequirementSuggestionResponse(BaseModel):
    """Schema for requirement suggestion response."""
    suggestions: list[RequirementSuggestion] = Field(..., description="List of suggested requirements")
    project_id: str = Field(..., description="ID of the project")
    generated_at: datetime = Field(..., description="Timestamp when suggestions were generated")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }