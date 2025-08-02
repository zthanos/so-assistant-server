"""Requirement domain models."""

import enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum
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


class Requirement(Base):
    """Requirement model."""
    __tablename__ = "requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(RequirementCategory), nullable=False)
    status = Column(Enum(RequirementStatus), default=RequirementStatus.pending)
    
    # Relationships
    project = relationship("Project", back_populates="requirements")