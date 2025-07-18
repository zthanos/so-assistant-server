from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class RequirementCategory(enum.Enum):
    functional = "Functional"
    non_functional = "Non-Functional"

class RequirementStatus(enum.Enum):
    pending = "Pending"
    approved = "Approved"
    implemented = "Implemented"



class TaskStatus(enum.Enum):
    todo = "To Do"
    in_progress = "In Progress"
    done = "Done"

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan", lazy='joined')
    diagrams = relationship("Diagram", back_populates="project", cascade="all, delete-orphan", lazy='joined')
    teams = relationship("Team", back_populates="project", cascade="all, delete-orphan", lazy='joined')
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan", lazy='joined')

class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(RequirementCategory), nullable=False)
    status = Column(Enum(RequirementStatus), default=RequirementStatus.pending)

    project = relationship("Project", back_populates="requirements")

class Diagram(Base):
    __tablename__ = "diagrams"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    mermaid_code = Column(Text, nullable=False)
    type = Column(Text, nullable=False)

    project = relationship("Project", back_populates="diagrams")

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    members = Column(Text)  # comma-separated names

    project = relationship("Project", back_populates="teams")
    tasks = relationship("Task", back_populates="assigned_team", lazy='selectin')

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    description = Column(Text, nullable=False)
    assigned_to_team_id = Column(Integer, ForeignKey("teams.id"))
    status = Column(Enum(TaskStatus), default=TaskStatus.todo)

    project = relationship("Project", back_populates="tasks")
    assigned_team = relationship("Team", back_populates="tasks")
