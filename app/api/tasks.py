from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create", response_model=schemas.TaskResponse)
def create_task(
    project_id: int = Path(..., description="ID του project"),
    task: schemas.TaskCreate = Body(...),
    db: Session = Depends(get_db)
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db_task = models.Task(
        project_id=project_id,
        description=task.description,
        assigned_to_team_id=task.assigned_to_team_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task 