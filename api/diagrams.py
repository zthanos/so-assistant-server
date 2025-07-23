from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app import schemas, database
from typing import Optional
from app.diagrams.diagrams_repository import (
    insert_diagram,
    update_diagram,
    list_diagrams,
    get_diagram,
    delete_diagram,
    upsert_diagram,
)
import logging
from app.decorators.safe_route import safe_route

logger = logging.getLogger("diagrams_api")

# Το prefix περιέχει ήδη το {project_id}
router = APIRouter(prefix="/projects/{project_id}/diagrams", tags=["Diagrams"])


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/add", response_model=schemas.DiagramResponse, status_code=status.HTTP_201_CREATED
)
def add_diagram(
    project_id: str, diagram: schemas.DiagramCreate, db: Session = Depends(get_db)
):
    try:
        created = insert_diagram(project_id, diagram, db)
        return created
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
    try:
        updated = update_diagram(diagram_id, diagram, db)
        return updated
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/list",
    response_model=list[schemas.DiagramResponse],
    status_code=status.HTTP_200_OK,
)
def list_diagrams_endpoint(project_id: str, db: Session = Depends(get_db)):
    try:
        return list_diagrams(project_id, db)
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{diagram_id}",
    response_model=schemas.DiagramResponse,
    status_code=status.HTTP_200_OK,
)
def get_diagram_endpoint(
    project_id: str, diagram_id: int, db: Session = Depends(get_db)
):
    try:
        return get_diagram(project_id, diagram_id, db)
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{diagram_id}", status_code=204)
@safe_route
def remove_diagram(
    project_id: str,  # Get from path
    diagram_id: int,  # Changed to int
    db: Session = Depends(get_db),
):
    delete_diagram(db, project_id, diagram_id)





@router.post("", response_model=schemas.Diagram)  # Single POST endpoint
@safe_route
def upsert_diagram(
    project_id: str,
    diagram_data: schemas.DiagramUpsert,  # Includes optional diagram_id
    db: Session = Depends(get_db)
):
    """
    Upsert a diagram:
    - If diagram_id is provided → UPDATE (if exists) or error (if not found).
    - If no diagram_id → CREATE new diagram.
    """
    return upsert_diagram(project_id, diagram_data.diagram_id, diagram_data, db)



    # @router.delete("/{diagram_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
# def delete_diagram_endpoint(
#     project_id: str,
#     diagram_id: int,
#     db: Session = Depends(get_db)
# ):
#     try:
#         delete_diagram(project_id, diagram_id, db)
#         return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
#     except HTTPException as e:
#         raise e
#     except SQLAlchemyError as e:
#         logger.error(f"Database error: {e}")
#         raise HTTPException(status_code=500, detail="Database error")
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")