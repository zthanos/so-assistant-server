# Contributing to Solution Outline Assistant API

Thank you for your interest in contributing to the Solution Outline Assistant API! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team. All complaints will be reviewed and investigated promptly and fairly.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.8 or higher
- Git
- Basic understanding of FastAPI, SQLAlchemy, and async Python
- Familiarity with REST API design principles

### Development Setup

1. **Fork and Clone**
   ```bash
   # Fork the repository on GitHub
   git clone https://github.com/yourusername/solution-outline-assistant.git
   cd solution-outline-assistant
   ```

2. **Set Up Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Initialize Database**
   ```bash
   alembic upgrade head
   ```

5. **Verify Setup**
   ```bash
   python -m pytest
   uvicorn app.main:app --reload
   ```

For detailed setup instructions, see [docs/developer/SETUP.md](docs/developer/SETUP.md).

## Development Process

### Workflow Overview

1. **Create Issue**: For new features or bugs
2. **Create Branch**: From main branch
3. **Develop**: Implement changes with tests
4. **Test**: Run all tests locally
5. **Document**: Update relevant documentation
6. **Submit PR**: Create pull request
7. **Review**: Address feedback
8. **Merge**: After approval

### Branch Naming

Use descriptive branch names with prefixes:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

Examples:
- `feature/add-pagination-to-teams`
- `fix/sse-connection-cleanup`
- `docs/update-api-documentation`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

**Examples:**
```
feat(api): add pagination support to teams endpoint

- Implement PaginationParams model
- Add pagination to TeamService
- Update team endpoints to use pagination
- Add pagination tests

Closes #123
```

```
fix(sse): resolve connection cleanup issue

The SSE manager was not properly cleaning up disconnected clients,
causing memory leaks over time.

Fixes #456
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Maximum line length: 88 characters (Black default)

### Code Quality Tools

Run these tools before submitting:

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/

# Run all quality checks
pre-commit run --all-files
```

### Naming Conventions

- **Classes**: PascalCase (`ProjectService`, `TeamRepository`)
- **Functions/Methods**: snake_case (`get_project`, `create_team`)
- **Variables**: snake_case (`project_id`, `team_name`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_PAGE_SIZE`, `DEFAULT_TIMEOUT`)
- **Files/Modules**: snake_case (`project_service.py`, `team_repository.py`)

### Documentation Standards

#### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def create_project(
    self, 
    project_data: ProjectCreate, 
    user_id: str
) -> Project:
    """Create a new project.
    
    Args:
        project_data: Project creation data containing name, description, etc.
        user_id: ID of the user creating the project
        
    Returns:
        The created project instance
        
    Raises:
        ConflictException: If project with same ID already exists
        ValidationException: If project data is invalid
        
    Example:
        >>> service = ProjectService(db)
        >>> project_data = ProjectCreate(name="My Project", description="...")
        >>> project = service.create_project(project_data, "user123")
    """
```

#### Type Hints

Use type hints for all function parameters and return values:

```python
from typing import List, Optional, Dict, Any

def get_projects(
    self, 
    skip: int = 0, 
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None
) -> List[Project]:
    """Get projects with pagination and filtering."""
```

### Error Handling

#### Custom Exceptions

Use appropriate custom exceptions:

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

#### Exception Handling in Endpoints

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
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=e.message)
```

## Testing Guidelines

### Test Structure

Organize tests by type:

```
tests/
├── unit/           # Unit tests (isolated components)
├── integration/    # Integration tests (component interactions)
└── e2e/           # End-to-end tests (complete workflows)
```

### Test Naming

Use descriptive test names that explain the scenario:

```python
def test_create_project_with_valid_data_returns_project():
    """Test that creating a project with valid data returns the project."""

def test_create_project_with_duplicate_id_raises_conflict_exception():
    """Test that creating a project with duplicate ID raises ConflictException."""

def test_get_projects_with_pagination_returns_paginated_results():
    """Test that getting projects with pagination returns paginated results."""
```

### Test Structure (AAA Pattern)

Follow the Arrange-Act-Assert pattern:

```python
def test_create_team_success(self, client, sample_project_data):
    """Test successful team creation."""
    # Arrange
    project_response = client.post("/api/v1/projects", json=sample_project_data)
    project_id = project_response.json()["id"]
    team_data = {"name": "Test Team", "members": "Alice, Bob"}
    
    # Act
    response = client.post(f"/api/v1/projects/{project_id}/teams", json=team_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == team_data["name"]
    assert response.json()["project_id"] == project_id
```

### Test Coverage

- Aim for >80% code coverage
- Test both success and failure scenarios
- Include edge cases and boundary conditions
- Mock external dependencies

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test types
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/e2e/

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Run specific test
python -m pytest tests/unit/services/test_project_service.py::test_create_project
```

### Test Data

Use fixtures for reusable test data:

```python
@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "id": "test-project-1",
        "name": "Test Project",
        "description": "A test project",
        "code": "TP001",
        "state": "active"
    }

@pytest.fixture
def sample_team_data():
    """Sample team data for testing."""
    return {
        "name": "Test Team",
        "members": "Alice Johnson, Bob Smith"
    }
```

## Documentation

### API Documentation

- Update OpenAPI schemas when adding/modifying endpoints
- Include request/response examples
- Document error responses
- Add usage examples

### Code Documentation

- Document all public APIs
- Include examples in docstrings
- Update README files when adding features
- Keep documentation in sync with code

### Documentation Structure

```
docs/
├── README.md           # Main documentation
├── api/               # API documentation
│   └── README.md
├── sse/               # SSE documentation
│   └── README.md
└── developer/         # Developer documentation
    ├── README.md
    └── SETUP.md
```

## Pull Request Process

### Before Submitting

Ensure your PR meets these requirements:

- [ ] Code follows style guidelines
- [ ] Tests pass locally (`python -m pytest`)
- [ ] Code coverage is maintained or improved
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] Branch is up to date with main

### PR Description Template

Use this template for your PR description:

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues
Closes #123
Fixes #456

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] End-to-end tests added/updated
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

### Review Process

1. **Automated Checks**: CI runs tests and code quality checks
2. **Code Review**: Team members review the code
3. **Address Feedback**: Make requested changes
4. **Approval**: PR approved by reviewers
5. **Merge**: PR merged to main branch

### Review Criteria

Reviewers will check for:

- Code quality and style compliance
- Test coverage and quality
- Documentation completeness
- Performance implications
- Security considerations
- Breaking changes

## Issue Reporting

### Bug Reports

When reporting bugs, include:

- **Description**: Clear description of the issue
- **Steps to Reproduce**: Detailed steps to reproduce the bug
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: OS, Python version, dependencies
- **Screenshots**: If applicable
- **Additional Context**: Any other relevant information

### Feature Requests

When requesting features, include:

- **Problem Description**: What problem does this solve?
- **Proposed Solution**: How should this be implemented?
- **Alternatives**: Other solutions you've considered
- **Additional Context**: Any other relevant information

### Issue Labels

We use these labels to categorize issues:

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements or additions to documentation
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention is needed
- `question` - Further information is requested

## Community

### Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and discussions
- **Pull Requests**: For code contributions

### Getting Help

If you need help:

1. Check existing documentation
2. Search existing issues and discussions
3. Ask questions in GitHub Discussions
4. Reach out to maintainers

### Recognition

Contributors are recognized in:

- GitHub contributors list
- Release notes for significant contributions
- Project documentation

## Development Resources

### Useful Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)

### Learning Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Async/Await in Python](https://docs.python.org/3/library/asyncio.html)
- [REST API Design](https://restfulapi.net/)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

Thank you for contributing to the Solution Outline Assistant API! Your contributions help make this project better for everyone.