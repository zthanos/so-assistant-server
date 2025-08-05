"""Domain models."""
# This file will be replaced by individual model files in each domain directory
# For now, it's a placeholder to ensure the database module works correctly

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Enum
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
    
    # Relationships
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    requirement_documents = relationship("RequirementDocument", back_populates="project", cascade="all, delete-orphan")
    requirement_items = relationship("RequirementItem", back_populates="project", cascade="all, delete-orphan")
    diagrams = relationship("Diagram", back_populates="project", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    solution_outlines = relationship("SolutionOutline", back_populates="project", cascade="all, delete-orphan")
    adrs = relationship("ADR", back_populates="project", cascade="all, delete-orphan")