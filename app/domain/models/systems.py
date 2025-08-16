"""System domain models."""
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class SystemType(enum.Enum):
    """System type enum."""
    internal = "internal"
    external = "external"
    integration = "integration"


class System(Base):
    """System model."""
    __tablename__ = "systems"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(SystemType), nullable=False)
    dependencies = Column(JSON, default=list)  # List of system names or IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="systems")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'name', name='uq_system_project_name'),
    )