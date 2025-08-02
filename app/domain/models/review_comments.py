"""Review Comment domain models."""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base

class ReviewCommentStatus(enum.Enum):
    """Review Comment status enum."""
    pending = "pending"
    fixed = "fixed"
    rejected = "rejected"

class ReviewComment(Base):
    """Review Comment model."""
    __tablename__ = "review_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    solution_outline_id = Column(Integer, ForeignKey("solution_outlines.id"), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(ReviewCommentStatus), default=ReviewCommentStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    solution_outline = relationship("SolutionOutline", back_populates="review_comments")