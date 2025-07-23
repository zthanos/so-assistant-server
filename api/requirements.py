from sqlalchemy.orm import Session
from app import models, schemas, database

from inspect import getmembers
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Path, Body
from pydantic import BaseModel
from app.logger import get_logger
from app.diagrams.generate_diagrams import generate_c4_diagram as c4_diagram
from typing import List
from app.requirements.analyze_requirements import analyze_requirements
import tempfile
import os
from app.utils.pdf_processor import process_pdf

logger = get_logger()

router = APIRouter(prefix="/projects/{project_id}/requirements", tags=["Requirements"])

class RequirementsRequest(BaseModel):
    content: str

class RequirementItem(BaseModel):
    title: str
    description: str
    functional: bool

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



@router.post("/", response_model=List[RequirementItem])
async def analyze_requirements_from_content(request: RequirementsRequest):
    # Η λογική σου για να δημιουργήσεις τη λίστα από requirements.
    # Παράδειγμα:
    requirements_response: List[RequirementItem] = []
    response = analyze_requirements(request.content)
    logger.info(f"Requirements: {response}")

    return requirements_response
    
@router.get("/list", response_model=List[RequirementItem])
async def get_requirements(project_id: str):
    # Η λογική σου για να δημιουργήσεις τη λίστα από requirements.
    # Παράδειγμα:
    requirements_response: List[RequirementItem] = []

    return requirements_response    
    
@router.post("/upload-and-process", response_model=List[RequirementItem])
async def upload_and_process_requirements(project_id: str, files: List[UploadFile] = File(...)):
    requirements_response: List[RequirementItem] = []

    for upload_file in files:
        # Αποθήκευση προσωρινά
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await upload_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Επεξεργασία PDF (χωρίς chunks)
        chunks = process_pdf(tmp_path, max_chunk_length=1000000)  # Μεγάλο όριο για να πάρεις όλο το κείμενο ως ένα chunk
        if chunks:
            full_text = chunks[0]  # Πάρε όλο το cleaned text
            reqs = analyze_requirements(full_text)
            logger.debug(reqs)
            requirements_response.extend(reqs)

        os.remove(tmp_path)

    return requirements_response
    