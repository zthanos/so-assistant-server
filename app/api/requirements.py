from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(prefix="/projects/{project_id}/requirements", tags=["Requirements"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/add", response_model=schemas.RequirementResponse)
def add_requirement(
    project_id: str = Path(..., description="ID του project"),
    req: schemas.RequirementCreate = Body(...),
    db: Session = Depends(get_db)
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db_req = models.Requirement(
        project_id=project_id,
        description=req.description,
        category=req.category
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req 