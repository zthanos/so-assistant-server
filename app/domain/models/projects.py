"""Project domain models."""
from sqlalchemy import Column, String, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base

class ProjectState(enum.Enum):
    """Project state enum."""
    active = "active"
    archived = "archived"
    deleted = "deleted"

class Project(Base):
    """Project model."""
    __tablename__ = "projects"
    
    id = Column(String(255), primary_key=True, index=True, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    code = Column(String(255))  # New field for project code
    state = Column(Enum(ProjectState), default=ProjectState.active)  # New field for project state
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (temporarily without cascade to avoid database schema issues)
    solution_outlines = relationship("SolutionOutline", back_populates="project")
    adrs = relationship("ADR", back_populates="project")
    teams = relationship("Team", back_populates="project")
    tasks = relationship("Task", back_populates="project")
    requirements = relationship("Requirement", back_populates="project")
    requirement_documents = relationship("RequirementDocument", back_populates="project")
    requirement_items = relationship("RequirementItem", back_populates="project")
    diagrams = relationship("Diagram", back_populates="project")