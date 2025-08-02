"""Solution Outline domain models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base

class SolutionOutlineStatus(enum.Enum):
    """Solution Outline status enum."""
    draft = "draft"
    published = "published"
    archived = "archived"

class SolutionOutline(Base):
    """Solution Outline model."""
    __tablename__ = "solution_outlines"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    status = Column(Enum(SolutionOutlineStatus), default=SolutionOutlineStatus.draft)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="solution_outlines")
    review_comments = relationship("ReviewComment", back_populates="solution_outline", cascade="all, delete-orphan")

    # Composite unique constraint to ensure unique versions per project
    __table_args__ = (
        UniqueConstraint('project_id', 'version', name='uix_project_version'),
    )