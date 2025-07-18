from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(prefix="/projects/{project_id}/teams", tags=["Teams"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/assign", response_model=schemas.TeamResponse)
def assign_team(
    project_id: int = Path(..., description="ID του project"),
    team: schemas.TeamCreate = Body(...),
    db: Session = Depends(get_db)
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db_team = models.Team(
        project_id=project_id,
        name=team.name,
        members=team.members
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team 