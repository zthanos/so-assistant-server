from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.repositories import projects_repository
from app import models, schemas
from app.database import get_db
import logging
from app.decorators.safe_route import safe_route, safe_get_route
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse
from app.utils.json_utils import _is_json
from app.exceptions.custom_exceptions import NotFoundError
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/create", response_model=schemas.ProjectResponse, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    projects_repository.create_project(
        id=project.id, name=project.name, description=project.description
    )


@router.get("/list", response_model=List[schemas.ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    try:
        response = projects_repository.list_projects(db)
        
        if response is None:
            raise HTTPException(404, detail="Resource not found")
            
        # Auto-convert to JSONResponse if serializable
        return JSONResponse(response) if _is_json(response) else response
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in GET: {e}")
        raise HTTPException(503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected GET error: {e}")
        raise HTTPException(500, detail="Internal server error")    
    except NotFoundError as e:
        logger.error(f"Unexpected GET error: {e}")
        raise HTTPException(404, detail="Resource not found")      

@router.get("/{project_id}/outline", response_model=schemas.ProjectOutlineResponse)
def project_outline(project_id: str, db: Session = Depends(get_db)):
    try:
        response =  projects_repository.get_project_outline(project_id, db)
        return JSONResponse(response) if _is_json(response) else response
    except NotFoundError as e:
        logger.error(f"Unexpected GET error: {e}")
        raise HTTPException(404, detail="Resource not found")           
    except SQLAlchemyError as e:
        logger.error(f"Database error in GET: {e}")
        raise HTTPException(503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected GET error: {e}")
        raise HTTPException(500, detail="Internal server error")   
    except HTTPException:
        raise HTTPException(500, detail="Internal server error")              
        
@router.delete("/{project_id}/delete", response_model=dict)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    projects_repository.delete(project_id, db)
