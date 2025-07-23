from sqlalchemy.orm import Session
from app import models, schemas
from fastapi import HTTPException



def insert_diagram(project_id: str, diagram: schemas.DiagramCreate, db: Session):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db_diagram = models.Diagram(
        project_id=project_id,
        title=diagram.title,
        mermaid_code=diagram.mermaid_code,
        type=diagram.type
    )
    db.add(db_diagram)
    db.commit()
    db.refresh(db_diagram)
    return db_diagram

def update_diagram(diagram_id: int, diagram: schemas.DiagramCreate, db: Session):
    db_diagram = db.query(models.Diagram).filter(models.Diagram.id == diagram_id).first()
    if not db_diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    db_diagram.title = diagram.title
    db_diagram.mermaid_code = diagram.mermaid_code
    db_diagram.type = diagram.type
    db.commit()
    db.refresh(db_diagram)
    return db_diagram

def list_diagrams(project_id: str, db: Session):
    return db.query(models.Diagram).filter(models.Diagram.project_id == project_id).all()

def get_diagram(project_id: str, diagram_id: int, db: Session):
    diagram = db.query(models.Diagram).filter(
        models.Diagram.project_id == project_id,
        models.Diagram.id == diagram_id
    ).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    return diagram

def delete_diagram(project_id: str, diagram_id: int, db: Session):
    diagram = db.query(models.Diagram).filter(
        models.Diagram.project_id == project_id,
        models.Diagram.id == diagram_id
    ).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    db.delete(diagram)
    db.commit()
    return {"detail": "Diagram deleted"}

# def upsert_diagram(project_id: str, diagram_id: int, diagram: schemas.DiagramCreate, db: Session):
#     """
#     Update diagram if diagram_id exists, else insert new diagram for project_id.
#     Returns the upserted diagram object.
#     """
#     if diagram_id is not None:
#         db_diagram = db.query(models.Diagram).filter(models.Diagram.id == diagram_id).first()
#         if db_diagram:
#             db_diagram.title = diagram.title
#             db_diagram.mermaid_code = diagram.mermaid_code
#             db_diagram.type = diagram.type
#             db.commit()
#             db.refresh(db_diagram)
#             return db_diagram
#     # Insert new diagram
#     db_diagram = models.Diagram(
#         project_id=project_id,
#         title=diagram.title,
#         mermaid_code=diagram.mermaid_code,
#         type=diagram.type
#     )
#     db.add(db_diagram)
#     db.commit()
#     db.refresh(db_diagram)
#     return db_diagram    


def upsert_diagram(project_id: str, diagram_id: int, diagram: schemas.DiagramCreate, db: Session):
    # 1. Try to UPDATE if diagram_id exists
    if diagram_id is not None:
        db_diagram = db.query(models.Diagram).filter(
            models.Diagram.id == diagram_id,
            models.Diagram.project_id == project_id  # Ensure the diagram belongs to the project
        ).first()
        if db_diagram:  # Exists → UPDATE
            db_diagram.title = diagram.title
            db_diagram.mermaid_code = diagram.mermaid_code
            db_diagram.type = diagram.type
            db.commit()
            db.refresh(db_diagram)
            return db_diagram

    # 2. If not found → INSERT new diagram
    db_diagram = models.Diagram(
        project_id=project_id,
        title=diagram.title,
        mermaid_code=diagram.mermaid_code,
        type=diagram.type
    )
    db.add(db_diagram)
    db.commit()
    db.refresh(db_diagram)
    return db_diagram    