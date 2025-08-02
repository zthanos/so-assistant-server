# Developer Documentation

This document provides comprehensive information for developers working on the Solution Outline Assistant API, including setup instructions, project structure, development guidelines, and contribution processes.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Development Guidelines](#development-guidelines)
- [Testing](#testing)
- [Contributing](#contributing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**: The application is built with Python
- **pip**: Python package manager
- **Git**: Version control system
- **Virtual Environment**: For dependency isolation (venv or conda)

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd solution-outline-assistant
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize Database**
   ```bash
   python -m alembic upgrade head
   ```

6. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## Project Structure

The project follows a domain-driven design approach with clear separation of concerns:

```
solution-outline-assistant/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application setup
│   │
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   ├── v1/                   # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── router.py         # Main API router
│   │   │   └── endpoints/        # API endpoints
│   │   │       ├── __init__.py
│   │   │       ├── projects.py
│   │   │       ├── teams.py
│   │   │       ├── adrs.py
│   │   │       ├── solution_outlines.py
│   │   │       ├── solution_outline_reviews.py
│   │   │       ├── llm.py
│   │   │       └── sse.py
│   │   └── schemas/              # Pydantic schemas
│   │       ├── __init__.py
│   │       ├── common.py         # Common response schemas
│   │       ├── projects.py
│   │       ├── teams.py
│   │       ├── adrs.py
│   │       └── solution_outlines.py
│   │
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── database.py           # Database configuration
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── events.py             # SSE event management
│   │   ├── sse_utils.py          # SSE utilities
│   │   ├── security.py           # Security utilities
│   │   └── middleware/           # Custom middleware
│   │       ├── __init__.py
│   │       ├── error_middleware.py
│   │       └── sse_middleware.py
│   │
│   ├── domain/                   # Domain layer
│   │   ├── __init__.py
│   │   └── models/               # SQLAlchemy models
│   │       ├── __init__.py
│   │       ├── projects.py
│   │       ├── teams.py
│   │       ├── adrs.py
│   │       ├── solution_outlines.py
│   │       └── review_comments.py
│   │
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py               # Base repository
│   │   ├── project_repository.py
│   │   ├── team_repository.py
│   │   ├── adr_repository.py
│   │   ├── solution_outline_repository.py
│   │   └── review_comment_repository.py
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── projects.py
│   │   ├── teams.py
│   │   ├── adrs.py
│   │   ├── solution_outlines.py
│   │   ├── solution_outline_reviews.py
│   │   └── llm/                  # LLM integration
│   │       ├── __init__.py
│   │       ├── client.py         # Ollama client
│   │       └── streaming.py      # Streaming utilities
│   │
│   └── utils/                    # Utility modules
│       ├── __init__.py
│       ├── pagination.py         # Pagination utilities
│       ├── filtering.py          # Filtering utilities
│       ├── response_utils.py     # Response formatting
│       └── llm_response_utils.py # LLM response utilities
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Test configuration
│   ├── unit/                     # Unit tests
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   ├── services/
│   │   └── utils/
│   ├── integration/              # Integration tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_teams_api.py
│   │   ├── test_adrs_api.py
│   │   └── test_sse_functionality.py
│   └── e2e/                      # End-to-end tests
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_project_workflows.py
│       ├── test_sse_workflows.py
│       └── test_data_consistency.py
│
├── docs/                         # Documentation
│   ├── README.md                 # Main documentation
│   ├── api/                      # API documentation
│   ├── sse/                      # SSE documentation
│   └── developer/                # Developer documentation
│
├── alembic/                      # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables example
├── .gitignore                    # Git ignore rules
├── alembic.ini                   # Alembic configuration
└── README.md                     # Project README
```

### Key Directories Explained

#### `/app` - Main Application
- **`main.py`**: FastAPI application setup, middleware configuration, and startup logic
- **`api/`**: API layer with endpoints, dependencies, and schemas
- **`core/`**: Core functionality including database, exceptions, and utilities
- **`domain/`**: Domain models representing business entities
- **`repositories/`**: Data access layer with database operations
- **`services/`**: Business logic layer with domain operations
- **`utils/`**: Utility functions and helpers

#### `/tests` - Test Suite
- **`unit/`**: Unit tests for individual components
- **`integration/`**: Integration tests for API endpoints and components
- **`e2e/`**: End-to-end tests for complete workflows

#### `/docs` - Documentation
- **`api/`**: API endpoint documentation
- **`sse/`**: Server-Sent Events documentation
- **`developer/`**: Development and contribution guidelines

## Development Setup

### Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
# Database
DATABASE_URL=sqlite:///./solution_outline_assistant.db

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Solution Outline Assistant API

# Development
DEBUG=true
LOG_LEVEL=INFO

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### Database Setup

The application uses SQLAlchemy with Alembic for database migrations.

#### Initialize Database
```bash
# Create migration environment (first time only)
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

#### Common Database Commands
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Development Tools

#### Code Quality Tools
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Architecture Overview

### Layered Architecture

The application follows a layered architecture pattern:

```
┌─────────────────────────────────────┐
│           API Layer                 │
│  (FastAPI endpoints, dependencies)  │
├─────────────────────────────────────┤
│         Service Layer               │
│     (Business logic)                │
├─────────────────────────────────────┤
│       Repository Layer              │
│     (Data access)                   │
├─────────────────────────────────────┤
│        Domain Layer                 │
│   (Models, entities)                │
└─────────────────────────────────────┘
```

### Key Architectural Patterns

#### 1. Repository Pattern
- Abstracts data access logic
- Provides consistent interface for data operations
- Enables easy testing with mock repositories

#### 2. Service Pattern
- Contains business logic
- Orchestrates operations across multiple repositories
- Handles complex business rules and validations

#### 3. Dependency Injection
- Uses FastAPI's dependency injection system
- Enables loose coupling between components
- Facilitates testing and mocking

#### 4. Domain-Driven Design
- Organizes code around business domains
- Clear separation of concerns
- Models reflect business concepts

### Data Flow

```
Request → API Endpoint → Service → Repository → Database
                ↓
Response ← Response Schema ← Service ← Repository ← Database
```

### SSE Architecture

```
Client ←→ SSE Endpoint ←→ SSE Manager ←→ LLM Service
                              ↓
                         Event Broadcasting
```

## Development Guidelines

### Code Style

#### Python Style Guide
- Follow PEP 8 style guidelines
- Use Black for code formatting
- Use isort for import sorting
- Maximum line length: 88 characters (Black default)

#### Naming Conventions
- **Classes**: PascalCase (`UserService`, `ProjectRepository`)
- **Functions/Methods**: snake_case (`get_user`, `create_project`)
- **Variables**: snake_case (`user_id`, `project_name`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_PAGE_SIZE`, `DEFAULT_TIMEOUT`)
- **Files/Modules**: snake_case (`user_service.py`, `project_repository.py`)

#### Documentation
- Use docstrings for all classes and functions
- Follow Google docstring format
- Include type hints for all function parameters and return values

```python
def create_project(
    self, 
    project_data: ProjectCreate, 
    user_id: str
) -> Project:
    """Create a new project.
    
    Args:
        project_data: Project creation data
        user_id: ID of the user creating the project
        
    Returns:
        The created project
        
    Raises:
        ConflictException: If project with same ID already exists
        ValidationException: If project data is invalid
    """
    # Implementation here
```

### Error Handling

#### Custom Exceptions
Use custom exceptions for different error scenarios:

```python
# Good
raise NotFoundException(
    f"Project with ID {project_id} not found",
    resource_type="Project",
    resource_id=project_id
)

# Avoid
raise Exception("Project not found")
```

#### Exception Hierarchy
```python
AppException
├── NotFoundException
├── ConflictException
├── ValidationException
├── UnauthorizedException
├── ForbiddenException
└── DatabaseException
```

### Database Guidelines

#### Model Design
- Use descriptive table and column names
- Include created_at and updated_at timestamps
- Use appropriate data types and constraints
- Define relationships clearly

```python
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    teams = relationship("Team", back_populates="project", cascade="all, delete-orphan")
```

#### Migration Guidelines
- Always review generated migrations before applying
- Use descriptive migration messages
- Test migrations on sample data
- Include both upgrade and downgrade operations

### API Design

#### Endpoint Design
- Follow RESTful principles
- Use appropriate HTTP methods
- Include proper status codes
- Implement consistent error responses

```python
@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    service: ProjectService = Depends(get_project_service)
):
    """Create a new project."""
    try:
        project = service.create_project(project_data)
        return project
    except ConflictException as e:
        raise HTTPException(status_code=409, detail=e.message)
```

#### Response Format
All responses should follow the standardized format:

```python
{
    "success": true,
    "message": "Operation completed successfully",
    "data": { /* response data */ },
    "timestamp": "2023-01-01T00:00:00Z"
}
```

### Testing Guidelines

#### Test Structure
- Organize tests by component type (unit, integration, e2e)
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

```python
def test_create_project_success(self, client, sample_project_data):
    """Test successful project creation."""
    # Arrange
    project_data = sample_project_data
    
    # Act
    response = client.post("/api/v1/projects", json=project_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == project_data["name"]
```

#### Test Coverage
- Aim for >80% code coverage
- Test both happy path and error scenarios
- Include edge cases and boundary conditions
- Mock external dependencies

#### Test Data
- Use fixtures for reusable test data
- Keep test data minimal and focused
- Use factories for complex object creation

## Testing

### Running Tests

#### All Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run with verbose output
python -m pytest -v
```

#### Specific Test Types
```bash
# Unit tests only
python -m pytest tests/unit/

# Integration tests only
python -m pytest tests/integration/

# End-to-end tests only
python -m pytest tests/e2e/

# Specific test file
python -m pytest tests/unit/services/test_project_service.py

# Specific test function
python -m pytest tests/unit/services/test_project_service.py::test_create_project
```

#### Test Configuration
```bash
# Run tests in parallel
python -m pytest -n auto

# Stop on first failure
python -m pytest -x

# Run only failed tests from last run
python -m pytest --lf

# Show test durations
python -m pytest --durations=10
```

### Test Environment

#### Test Database
Tests use an in-memory SQLite database for isolation:

```python
# tests/conftest.py
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    # ... rest of setup
```

#### Test Client
Integration tests use FastAPI's TestClient:

```python
@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
```

### Writing Tests

#### Unit Tests
Focus on testing individual components in isolation:

```python
class TestProjectService:
    def test_create_project(self, mock_repository):
        # Test service logic without database
        service = ProjectService(mock_repository)
        result = service.create_project(project_data)
        assert result.name == project_data.name
```

#### Integration Tests
Test component interactions with real dependencies:

```python
def test_create_project_api(client, db_session):
    # Test full API endpoint with database
    response = client.post("/api/v1/projects", json=project_data)
    assert response.status_code == 201
    
    # Verify in database
    project = db_session.query(Project).first()
    assert project.name == project_data["name"]
```

#### End-to-End Tests
Test complete user workflows:

```python
def test_complete_project_workflow(client, project_workflow_data):
    # Create project
    project_response = client.post("/api/v1/projects", json=project_data)
    
    # Add teams
    team_response = client.post(f"/api/v1/projects/{project_id}/teams", json=team_data)
    
    # Create solution outline
    outline_response = client.post(f"/api/v1/projects/{project_id}/solution-outlines", params=outline_data)
    
    # Verify complete workflow
    assert all responses successful
```

## Contributing

### Getting Started

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/yourusername/solution-outline-assistant.git
   cd solution-outline-assistant
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Workflow

1. **Make Changes**
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation as needed

2. **Test Changes**
   ```bash
   # Run tests
   python -m pytest
   
   # Check code quality
   black app/ tests/
   isort app/ tests/
   flake8 app/ tests/
   mypy app/
   ```

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Commit Message Format

Use conventional commit format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

**Examples:**
```
feat(api): add pagination support to teams endpoint
fix(sse): resolve connection cleanup issue
docs(api): update endpoint documentation
test(services): add unit tests for project service
```

### Pull Request Guidelines

#### Before Submitting
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New functionality includes tests
- [ ] Documentation is updated
- [ ] Commit messages follow convention

#### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass
```

### Code Review Process

1. **Automated Checks**: CI runs tests and code quality checks
2. **Peer Review**: At least one team member reviews the code
3. **Address Feedback**: Make requested changes
4. **Approval**: PR approved by reviewer
5. **Merge**: PR merged to main branch

## Deployment

### Local Development
```bash
# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with specific environment
ENV=development uvicorn app.main:app --reload
```

### Production Deployment

#### Environment Setup
```bash
# Production environment variables
DATABASE_URL=postgresql://user:password@localhost/dbname
DEBUG=false
LOG_LEVEL=WARNING
```

#### Using Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Using Gunicorn
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Database Migration in Production
```bash
# Apply migrations
alembic upgrade head

# Backup database before migrations
pg_dump dbname > backup.sql
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connection
python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"

# Reset database
rm solution_outline_assistant.db
alembic upgrade head
```

#### Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Install in development mode
pip install -e .
```

#### SSE Connection Issues
```bash
# Check SSE endpoint
curl -N -H "Accept: text/event-stream" http://localhost:8000/api/v1/sse

# Check browser console for CORS issues
# Verify server logs for connection errors
```

#### Test Failures
```bash
# Run specific failing test
python -m pytest tests/path/to/test.py::test_name -v

# Run with debugging
python -m pytest tests/path/to/test.py::test_name -s --pdb

# Clear test cache
python -m pytest --cache-clear
```

### Debugging

#### Enable Debug Mode
```python
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

#### Database Debugging
```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### API Debugging
```python
# Use FastAPI's automatic documentation
# Visit http://localhost:8000/docs for interactive API docs
```

### Performance Issues

#### Database Performance
- Add database indexes for frequently queried fields
- Use database query profiling
- Implement connection pooling

#### API Performance
- Use async/await for I/O operations
- Implement caching where appropriate
- Monitor response times

#### Memory Issues
- Profile memory usage with memory_profiler
- Check for memory leaks in long-running processes
- Monitor SSE connection cleanup

### Getting Help

#### Internal Resources
- Check existing documentation
- Review similar implementations in codebase
- Ask team members for guidance

#### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

#### Reporting Issues
When reporting issues, include:
- Steps to reproduce
- Expected vs actual behavior
- Error messages and stack traces
- Environment information (Python version, OS, etc.)
- Relevant code snippets

For more information, see the [API Documentation](../api/README.md) and [SSE Documentation](../sse/README.md).