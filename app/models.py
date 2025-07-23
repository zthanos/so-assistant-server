from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship, declarative_base
import enum
from datetime import datetime

from starlette.responses import Content

Base = declarative_base()

class RequirementCategory(enum.Enum):
    functional = "Functional"
    non_functional = "Non-Functional"

class RequirementStatus(enum.Enum):
    pending = "Pending"
    approved = "Approved"
    implemented = "Implemented"

class DiagramType(enum.Enum):
    flowchart = "Flowchart"
    sequence = "Sequence"
    gantt = "Gantt"

class TaskStatus(enum.Enum):
    todo = "To Do"
    in_progress = "In Progress"
    done = "Done"

class SoStatus(enum.Enum):
    not_started = "Not Started"
    in_progress = "In Progress"
    in_review = "In Review"
    rejected = "Rejected"
    done = "Done"


class Project(Base):
    __tablename__ = "projects"
    id = Column(String(255), primary_key=True, index=True, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    diagrams = relationship("Diagram", back_populates="project", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(RequirementCategory), nullable=False)
    status = Column(Enum(RequirementStatus), default=RequirementStatus.pending)

    project = relationship("Project", back_populates="requirements")

class Diagram(Base):
    __tablename__ = "diagrams"
    # id = Column(Integer, primary_key=True, index=True)
    # project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    # title = Column(String(255), nullable=False)
    # mermaid_code = Column(Text, nullable=False)
    # type = Column(Enum(DiagramType), nullable=False)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    mermaid_code: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    project = relationship("Project", back_populates="diagrams")

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    members = Column(Text)  # comma-separated names

    project = relationship("Project", back_populates="teams")
    tasks = relationship("Task", back_populates="assigned_team")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    description = Column(Text, nullable=False)
    assigned_to_team_id = Column(Integer, ForeignKey("teams.id"))
    status = Column(Enum(TaskStatus), default=TaskStatus.todo)

    project = relationship("Project", back_populates="tasks")
    assigned_team = relationship("Team", back_populates="tasks")


class SolutionOutlineDocument(Base):
    __tablename__ = "solution_outline_documents"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status = Column(Enum(SoStatus), default=SoStatus.not_started)
    version: Mapped[int] = mapped_column(Integer, default=0)
