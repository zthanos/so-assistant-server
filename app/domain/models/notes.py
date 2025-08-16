"""Notes domain models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class Note(Base):
    """Note model."""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # For backward compatibility and additional content
    tags = Column(JSON, nullable=True, default=list)  # List of tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="notes")