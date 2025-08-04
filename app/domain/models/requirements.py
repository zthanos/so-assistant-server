"""Requirement domain models."""

import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class RequirementCategory(enum.Enum):
    """Requirement category enum."""
    functional = "Functional"
    non_functional = "Non-Functional"


class RequirementStatus(enum.Enum):
    """Requirement status enum."""
    pending = "Pending"
    approved = "Approved"
    implemented = "Implemented"


class SourceType(enum.Enum):
    """Source type for requirements."""
    manual = "manual"
    pdf_upload = "pdf_upload"


class RequirementDocumentStatus(enum.Enum):
    """Requirement document status."""
    draft = "draft"
    published = "published"
    archived = "archived"


class Requirement(Base):
    """Requirement model (legacy - kept for backward compatibility)."""
    __tablename__ = "requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(RequirementCategory), nullable=False)
    status = Column(Enum(RequirementStatus), default=RequirementStatus.pending)
    
    # Relationships
    project = relationship("Project", back_populates="requirements")


class RequirementDocument(Base):
    """Versioned requirements document model."""
    __tablename__ = "requirement_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    content = Column(Text, nullable=False)  # Markdown content
    version = Column(Integer, nullable=False)
    status = Column(Enum(RequirementDocumentStatus), default=RequirementDocumentStatus.draft)
    source_type = Column(Enum(SourceType), default=SourceType.manual)
    original_filename = Column(String(255), nullable=True)  # For PDF uploads
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="requirement_documents")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'version', name='uq_requirement_document_project_version'),
    )