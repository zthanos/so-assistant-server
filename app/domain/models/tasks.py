"""Task domain models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base

class TaskStatus(enum.Enum):
    """Task status enum."""
    todo = "To Do"
    in_progress = "In Progress"
    done = "Done"

class Task(Base):
    """Task model."""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    description = Column(Text, nullable=False)
    assigned_to_team_id = Column(Integer, ForeignKey("teams.id"))
    status = Column(Enum(TaskStatus), default=TaskStatus.todo)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    assigned_team = relationship("Team", back_populates="tasks")