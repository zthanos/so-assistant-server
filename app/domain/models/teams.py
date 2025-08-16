"""Team domain models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class Team(Base):
    """Team model."""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    members = Column(JSON, default=list)  # List of member names (strings)
    responsibilities = Column(JSON, default=list)  # List of responsibility descriptions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="teams")
    tasks = relationship("Task", back_populates="assigned_team")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'name', name='uq_team_project_name'),
    )