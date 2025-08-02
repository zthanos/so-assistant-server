"""Review Comment schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum

class ReviewCommentStatus(str, enum.Enum):
    """Review Comment status enum."""
    pending = "pending"
    fixed = "fixed"
    rejected = "rejected"

class ReviewCommentBase(BaseModel):
    """Base Review Comment schema."""
    content: str
    status: Optional[ReviewCommentStatus] = ReviewCommentStatus.pending

class ReviewCommentCreate(ReviewCommentBase):
    """Review Comment creation schema."""
    solution_outline_id: int

class ReviewCommentUpdate(BaseModel):
    """Review Comment update schema."""
    status: ReviewCommentStatus

class ReviewCommentResponse(ReviewCommentBase):
    """Review Comment response schema."""
    id: int
    solution_outline_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True