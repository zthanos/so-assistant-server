from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import enum

# Enums (ώστε να ταιριάζουν με τα models)
class RequirementCategory(str, enum.Enum):
    functional = "Functional"
    non_functional = "Non-Functional"

class RequirementStatus(str, enum.Enum):
    pending = "Pending"
    approved = "Approved"
    implemented = "Implemented"

class DiagramType(str, enum.Enum):
    flowchart = "Flowchart"
    sequence = "Sequence"
    gantt = "Gantt"

class TaskStatus(str, enum.Enum):
    todo = "To Do"
    in_progress = "In Progress"
    done = "Done"

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Requirement Schemas
class RequirementBase(BaseModel):
    description: str
    category: RequirementCategory

class RequirementCreate(RequirementBase):
    pass

class RequirementResponse(RequirementBase):
    id: int
    status: RequirementStatus
    class Config:
        from_attributes = True

# Diagram Schemas
class DiagramBase(BaseModel):
    title: str
    mermaid_code: str
    type: DiagramType

class DiagramCreate(DiagramBase):
    pass

class DiagramResponse(DiagramBase):
    id: int
    class Config:
        from_attributes = True

# Team Schemas
class TeamBase(BaseModel):
    name: str
    members: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamResponse(TeamBase):
    id: int
    class Config:
        from_attributes = True

# Task Schemas
class TaskBase(BaseModel):
    description: str
    assigned_to_team_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    class Config:
        from_attributes = True

# Project Outline (για το outline endpoint)
class ProjectOutlineResponse(ProjectResponse):
    requirements: List[RequirementResponse] = Field(default_factory=list)
    diagrams: List[DiagramResponse] = Field(default_factory=list)
    teams: List[TeamResponse] = Field(default_factory=list)
    tasks: List[TaskResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
