# Development Setup Guide

This guide provides step-by-step instructions for setting up the Solution Outline Assistant API development environment.

## Prerequisites

### Required Software

1. **Python 3.8 or higher**
   ```bash
   # Check Python version
   python --version
   # or
   python3 --version
   ```

2. **pip (Python package manager)**
   ```bash
   # Check pip version
   pip --version
   ```

3. **Git**
   ```bash
   # Check Git version
   git --version
   ```

4. **Virtual Environment Tool**
   - Built-in `venv` (recommended)
   - Or `conda` if you prefer

### Optional but Recommended

1. **Docker** (for containerized development)
2. **PostgreSQL** (for production-like database)
3. **Redis** (for caching, if implemented)
4. **Ollama** (for LLM functionality)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd solution-outline-assistant

# Or if you forked it
git clone https://github.com/yourusername/solution-outline-assistant.git
cd solution-outline-assistant
```

### 2. Create Virtual Environment

#### Using venv (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

#### Using conda
```bash
# Create conda environment
conda create -n solution-outline-assistant python=3.9
conda activate solution-outline-assistant
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional but recommended)
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

### 4. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit the .env file with your settings
nano .env  # or use your preferred editor
```

#### Basic .env Configuration
```bash
# Database
DATABASE_URL=sqlite:///./solution_outline_assistant.db

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Solution Outline Assistant API

# Development
DEBUG=true
LOG_LEVEL=INFO

# CORS (adjust for your frontend)
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# LLM Configuration (optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### 5. Database Setup

#### Initialize Database
```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

#### Verify Database Setup
```bash
# Check if database file was created (for SQLite)
ls -la solution_outline_assistant.db

# Or test database connection
python -c "from app.core.database import engine; print('Database connection successful')"
```

### 6. Verify Installation

```bash
# Run the application
uvicorn app.main:app --reload

# In another terminal, test the API
curl http://localhost:8000/
curl http://localhost:8000/api/v1/projects
```

### 7. Run Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test types
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/e2e/
```

## Development Tools Setup

### 1. Code Quality Tools

```bash
# Install pre-commit hooks
pre-commit install

# Run code formatting
black app/ tests/
isort app/ tests/

# Run linting
flake8 app/ tests/

# Run type checking
mypy app/
```

### 2. IDE Configuration

#### VS Code
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm
1. Set Python interpreter to `./venv/bin/python`
2. Enable Black formatter in settings
3. Configure isort for import sorting
4. Enable flake8 for linting

### 3. Database Tools

#### SQLite Browser (for SQLite development)
```bash
# Install SQLite browser (Ubuntu/Debian)
sudo apt-get install sqlitebrowser

# Or download from https://sqlitebrowser.org/
```

#### PostgreSQL Setup (Optional)
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE solution_outline_assistant;
CREATE USER dev_user WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE solution_outline_assistant TO dev_user;
\q

# Update .env file
DATABASE_URL=postgresql://dev_user:dev_password@localhost/solution_outline_assistant
```

## LLM Setup (Optional)

### Ollama Installation

#### Linux/Mac
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model (in another terminal)
ollama pull llama2
```

#### Windows
1. Download Ollama from https://ollama.ai/
2. Install and run the application
3. Pull a model: `ollama pull llama2`

#### Verify LLM Setup
```bash
# Test Ollama API
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Hello, world!",
  "stream": false
}'
```

## Docker Setup (Alternative)

### Using Docker Compose

Create `docker-compose.dev.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/solution_outline_assistant
      - DEBUG=true
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=solution_outline_assistant
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

```bash
# Run with Docker Compose
docker-compose -f docker-compose.dev.yml up --build
```

## Troubleshooting

### Common Issues

#### 1. Python Version Issues
```bash
# If python command not found, try python3
python3 --version
python3 -m venv venv

# Or create alias
alias python=python3
```

#### 2. Permission Issues (Linux/Mac)
```bash
# If permission denied for pip install
python -m pip install --user -r requirements.txt

# Or fix pip permissions
sudo chown -R $(whoami) ~/.local
```

#### 3. Virtual Environment Issues
```bash
# If virtual environment not activating
deactivate  # if already in a venv
rm -rf venv
python -m venv venv
source venv/bin/activate
```

#### 4. Database Connection Issues
```bash
# For SQLite permission issues
chmod 664 solution_outline_assistant.db
chmod 775 .  # directory permissions

# For PostgreSQL connection issues
sudo service postgresql start  # Linux
brew services start postgresql  # Mac
```

#### 5. Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows

# Or use different port
uvicorn app.main:app --reload --port 8001
```

#### 6. Import Errors
```bash
# If module not found errors
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Getting Help

If you encounter issues not covered here:

1. Check the [main documentation](README.md)
2. Look at existing GitHub issues
3. Ask team members
4. Create a new issue with:
   - Your operating system
   - Python version
   - Error messages
   - Steps to reproduce

## Next Steps

After successful setup:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Run Tests**: `python -m pytest`
3. **Read Documentation**: Check `docs/api/` and `docs/sse/`
4. **Make Changes**: Create a feature branch and start developing
5. **Contribute**: Follow the [contribution guidelines](README.md#contributing)

## Development Workflow

### Daily Development
```bash
# Start development session
source venv/bin/activate  # or conda activate
uvicorn app.main:app --reload

# Make changes, then test
python -m pytest tests/unit/
python -m pytest tests/integration/

# Before committing
black app/ tests/
isort app/ tests/
flake8 app/ tests/
python -m pytest
```

### Feature Development
```bash
# Create feature branch
git checkout -b feature/your-feature

# Develop and test
# ... make changes ...
python -m pytest

# Commit and push
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature

# Create pull request
```

This completes the development setup. You should now have a fully functional development environment for the Solution Outline Assistant API.