"""Test database connection."""
import logging
from app.core.database import init_db, get_db_context
from app.domain.models import Project, ProjectState
import uuid

logging.basicConfig(level=logging.INFO)

def main():
    """Test database connection."""
    # Initialize database
    init_db()
    
    # Create a test project
    project_id = str(uuid.uuid4())
    project = Project(
        id=project_id,
        name="Test Project",
        description="A test project",
        code="TEST",
        state=ProjectState.active
    )
    
    # Save the project to the database
    with get_db_context() as db:
        db.add(project)
        db.commit()
        logging.info(f"Created project with ID: {project_id}")
    
    # Retrieve the project from the database
    with get_db_context() as db:
        retrieved_project = db.query(Project).filter(Project.id == project_id).first()
        logging.info(f"Retrieved project: {retrieved_project.name}")
    
    logging.info("Database test completed successfully.")

if __name__ == "__main__":
    main()