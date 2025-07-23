from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app import schemas
from app.database import get_db
from app.repositories import diagrams_repository
import logging

logger = logging.getLogger("diagrams_api")

# Το prefix περιέχει ήδη το {project_id}
router = APIRouter(prefix="/projects/{project_id}/diagrams", tags=["Diagrams"])


@router.post(
    "/add", response_model=schemas.DiagramResponse, status_code=status.HTTP_201_CREATED
)
def add_diagram(
    project_id: str, diagram: schemas.DiagramCreate, db: Session = Depends(get_db)
):
    return diagrams_repository.insert_diagram(project_id, diagram, db)


@router.put(
    "/update/{diagram_id}",
    response_model=schemas.DiagramResponse,
    status_code=status.HTTP_200_OK,
)
def update_diagram_endpoint(
    project_id: str,
    diagram_id: int,
    diagram: schemas.DiagramCreate,
    db: Session = Depends(get_db),
):
    return diagrams_repository.update_diagram(diagram_id, diagram, db)


@router.get(
    "/list",
    response_model=list[schemas.DiagramResponse],
    status_code=status.HTTP_200_OK,
)
def list_diagrams_endpoint(project_id: str, db: Session = Depends(get_db)):
    return diagrams_repository.list_diagrams(project_id, db)


@router.get(
    "/{diagram_id}",
    response_model=schemas.DiagramResponse,
    status_code=status.HTTP_200_OK,
)
def get_diagram_endpoint(
    project_id: str, diagram_id: int, db: Session = Depends(get_db)
):
    return diagrams_repository.get_diagram(project_id, diagram_id, db)


@router.delete("/{diagram_id}", status_code=204)
def remove_diagram(
    project_id: str,  # Get from path
    diagram_id: int,  # Changed to int
    db: Session = Depends(get_db),
):
    return diagrams_repository.delete_diagram(db, project_id, diagram_id)


@router.post("", response_model=schemas.DiagramResponse)  # Single POST endpoint
def upsert_diagram(
    project_id: str,
    diagram_data: schemas.DiagramBase,  # Includes optional diagram_id
    db: Session = Depends(get_db),
):
    """
    Upsert a diagram:
    - If diagram_id is provided → UPDATE (if exists) or error (if not found).
    - If no diagram_id → CREATE new diagram.
    """
    return diagrams_repository.upsert_diagram(
        project_id, diagram_data.diagram_id, diagram_data, db
    )
