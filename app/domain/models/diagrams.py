"""Diagram domain models."""

from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Diagram(Base):
    """Diagram model."""
    __tablename__ = "diagrams"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    mermaid_code = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="diagrams")