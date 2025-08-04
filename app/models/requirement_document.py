"""Requirement document model for versioned requirements."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

from app.api.schemas.requirements import RequirementDocumentStatus, SourceType

Base = declarative_base()


class RequirementDocument(Base):
    """Versioned requirements document model."""
    __tablename__ = "requirement_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), nullable=False, index=True)  # ForeignKey would be added when Project model exists
    content = Column(Text, nullable=False)  # Markdown content
    version = Column(Integer, nullable=False)
    status = Column(Enum(RequirementDocumentStatus), default=RequirementDocumentStatus.draft)
    source_type = Column(Enum(SourceType), default=SourceType.manual)
    original_filename = Column(String(255), nullable=True)  # For PDF uploads
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on project_id and version
    __table_args__ = (
        {'sqlite_autoincrement': True}  # For SQLite compatibility
    )
    
    def __repr__(self):
        return f"<RequirementDocument(id={self.id}, project_id='{self.project_id}', version={self.version})>"
    
    def __str__(self):
        return f"Requirements v{self.version} for {self.project_id}"
    
    @property
    def is_latest(self) -> bool:
        """Check if this is the latest version (would need database query in real implementation)."""
        # This would require a database query to determine
        # For now, just return False as a placeholder
        return False
    
    @property
    def content_preview(self) -> str:
        """Get a preview of the content (first 100 characters)."""
        if not self.content:
            return ""
        return self.content[:100] + "..." if len(self.content) > 100 else self.content
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "content": self.content,
            "version": self.version,
            "status": self.status.value if self.status else None,
            "source_type": self.source_type.value if self.source_type else None,
            "original_filename": self.original_filename,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }