"""Task schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum

class TaskStatus(str, enum.Enum):
    """Task status enum."""
    todo = "To Do"
    in_progress = "In Progress"
    done = "Done"

class TaskBase(BaseModel):
    """Base Task schema."""
    description: str
    assigned_to_team_id: Optional[int] = None

class TaskCreate(TaskBase):
    """Task creation schema."""
    project_id: str

class TaskUpdate(TaskBase):
    """Task update schema."""
    description: Optional[str] = None
    assigned_to_team_id: Optional[int] = None
    status: Optional[TaskStatus] = None

class TaskResponse(TaskBase):
    """Task response schema."""
    id: int
    project_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True