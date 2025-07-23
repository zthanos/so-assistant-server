# app/repositories/projects_repository.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from app import models, schemas
from app.exceptions import custom_exceptions


def create_project(project: schemas.ProjectCreate, db: Session) -> models.Project:
    db_project = models.Project(
        id=project.id,
        name=project.name,
        description=project.description
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def list_projects(db: Session) -> list[models.Project]:
    projects = db.query(models.Project).all()
    if not projects:
        # αν θέλεις να είναι 204 No Content αντί για 404, μπορείς να το χειριστείς στον decorator
        raise custom_exceptions.ProjectNotFoundError("No projects found")
    return projects

def get_project_outline(project_id: str, db: Session) -> models.Project:
    project = db.query(models.Project).options(
        joinedload(models.Project.requirements),
        joinedload(models.Project.diagrams),
        joinedload(models.Project.teams),
        joinedload(models.Project.tasks),
    ).filter(models.Project.id == project_id).first()
    if not project:
        raise custom_exceptions.ProjectNotFoundError(f"Project {project_id} not found")
    return project

def delete_project(project_id: str, db: Session) -> bool:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return False
    db.delete(project)
    db.commit()
    return True
