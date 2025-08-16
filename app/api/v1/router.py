"""API router for version 1."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

# Import and include all endpoint routers here
from app.api.v1.endpoints import sse, llm, solution_outlines, solution_outline_reviews, adrs, notes, teams, tasks, projects, diagrams, requirement_documents, requirement_items, systems, monitoring
router.include_router(sse.router)
router.include_router(llm.router)
router.include_router(solution_outlines.router)
router.include_router(solution_outline_reviews.router)
router.include_router(adrs.router)
router.include_router(notes.router)
router.include_router(teams.router)
router.include_router(tasks.router)
router.include_router(projects.router, tags=["Projects"])
router.include_router(diagrams.router, tags=["Diagrams"])
router.include_router(requirement_documents.router, tags=["Requirement Documents"])
router.include_router(requirement_items.router, tags=["Requirement Items"])
router.include_router(systems.router, tags=["Systems"])
router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])

# These will be uncommented as they are implemented
# from app.api.v1.endpoints import assistant
# router.include_router(assistant.router)