"""Architecture Decision Record (ADR) domain models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class ADR(Base):
    """Architecture Decision Record (ADR) model."""
    __tablename__ = "adrs"
    
    # Core fields that exist in both old and new schema
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Original field, keep as required for backward compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # New fields (will be added after migration)
    # These are commented out until migration is applied
    # status = Column(String(50), nullable=True, default="proposed")
    # context = Column(Text, nullable=True)
    # decision = Column(Text, nullable=True)
    # consequences = Column(Text, nullable=True)
    # alternatives = Column(Text, nullable=True)
    # author = Column(String(255), nullable=True)
    # tags = Column(JSON, nullable=True, default=list)

    # Relationships
    project = relationship("Project", back_populates="adrs")