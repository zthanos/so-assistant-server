from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/create", response_model=schemas.ProjectResponse, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(name=project.name, description=project.description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/list", response_model=List[schemas.ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()

@router.get("/{project_id}/outline", response_model=schemas.ProjectOutlineResponse)
def project_outline(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).options(
        joinedload(models.Project.requirements),
        joinedload(models.Project.diagrams),
        joinedload(models.Project.teams),
        joinedload(models.Project.tasks),
    ).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
