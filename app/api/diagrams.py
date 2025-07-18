from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, database

# Το prefix περιέχει ήδη το {project_id}
router = APIRouter(prefix="/projects/{project_id}/diagrams", tags=["Diagrams"])

# Παίρνουμε το db session από το database.py
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/add", response_model=schemas.DiagramResponse)
def add_diagram(
    project_id: int,
    diagram: schemas.DiagramCreate,
    db: Session = Depends(get_db)
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_diagram = models.Diagram(
        project_id=project_id,
        title=diagram.title,
        mermaid_code=diagram.mermaid_code,
        type=diagram.type  # Πλέον str, όχι Enum
    )
    
    db.add(db_diagram)
    db.commit()
    db.refresh(db_diagram)
    return db_diagram

@router.get("/list", response_model=list[schemas.DiagramResponse])
def list_diagrams(
    project_id: int,
    db: Session = Depends(get_db)
):
    diagrams = db.query(models.Diagram).filter(models.Diagram.project_id == project_id).all()
    return diagrams

@router.get("/{diagram_id}", response_model=schemas.DiagramResponse)
def get_diagram(
    project_id: int,
    diagram_id: int,
    db: Session = Depends(get_db)
):
    diagram = db.query(models.Diagram).filter(
        models.Diagram.project_id == project_id,
        models.Diagram.id == diagram_id
    ).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    return diagram

@router.delete("/{diagram_id}/delete", response_model=dict)
def delete_diagram(
    project_id: int,
    diagram_id: int,
    db: Session = Depends(get_db)
):
    diagram = db.query(models.Diagram).filter(
        models.Diagram.project_id == project_id,
        models.Diagram.id == diagram_id
    ).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    db.delete(diagram)
    db.commit()
    return {"detail": "Diagram deleted"}
