# app/repositories/so_repository.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from app import models, schemas
from app.exceptions import custom_exceptions


def create_project(so_doc: schemas.SolutionOutlineDocumentCreate, db: Session) -> models.SolutionOutlineDocument:
    db_so_doc = models.SolutionOutlineDocument(
        id=so_doc.id,
        content=so_doc.content,
        status=so_doc.status,
        version= so_doc.version
    )
    db.add(db_so_doc)
    db.commit()
    db.refresh(db_so_doc)
    return db_so_doc

def get_document(project_id: str, db: Session):
    pass


