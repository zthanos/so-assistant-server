from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db
from api import projects, requirements, diagrams, teams, tasks, assistant
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (αν χρειαστεί, π.χ. cleanup)
    # pass

# Δημιουργία της FastAPI εφαρμογής
app = FastAPI(
    title="Solution Outline Assistant API",
    description="API to help architects create Solution Outlines.",
    version="0.1.0",
    lifespan=lifespan
)

# Επέτρεψε όλα τα origins (για development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ή βάλε λίστα με συγκεκριμένα origins π.χ. ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ένα απλό, αρχικό endpoint για έλεγχο
@app.get("/")
def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Welcome to the Solution Outline Assistant API!"}

# Εγγραφή router
app.include_router(projects.router)
app.include_router(requirements.router)
app.include_router(diagrams.router)
app.include_router(teams.router)
app.include_router(tasks.router)
app.include_router(assistant.router)

