"""Data access layer.

This package contains repository classes for data access.
Repositories are responsible for interacting with the database and providing
a clean interface for the service layer.
"""

from app.repositories.base import BaseRepository, AsyncBaseRepository, CRUDRepository
from app.repositories.project_repository import project_repository
from app.repositories.solution_outline_repository import solution_outline_repository
from app.repositories.adr_repository import adr_repository
from app.repositories.review_comment_repository import review_comment_repository
from app.repositories.team_repository import team_repository
from app.repositories.task_repository import task_repository

__all__ = [
    "BaseRepository",
    "AsyncBaseRepository",
    "CRUDRepository",

    "project_repository",
    "solution_outline_repository",
    "adr_repository",
    "review_comment_repository",
    "team_repository",
    "task_repository",
]