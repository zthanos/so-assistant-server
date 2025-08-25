"""
Docker deployment configuration and utilities for the agent system.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DockerConfig:
    """Docker configuration generator for agent deployment."""
    
    def __init__(self, environment: str = "production"):
        """Initialize Docker configuration."""
        self.environment = environment
        self.logger = logging.getLogger(f"{__name__}.DockerConfig")
    
    def generate_dockerfile(self, base_image: str = "python:3.11-slim") -> str:
        """Generate Dockerfile for agent deployment."""
        
        dockerfile_content = f"""# Multi-stage build for SO Assistant Agent
FROM {base_image} as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-langchain.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-langchain.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/cache
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        return dockerfile_content
    
    def generate_docker_compose(
        self, 
        include_ollama: bool = True,
        include_postgres: bool = True,
        include_redis: bool = True
    ) -> str:
        """Generate docker-compose.yml for full stack deployment."""
        
        services = {
            "so-assistant-agent": {
                "build": ".",
                "ports": ["8000:8000"],
                "environment": self._get_app_environment(),
                "volumes": [
                    "./logs:/app/logs",
                    "./data:/app/data",
                    "./cache:/app/cache"
                ],
                "depends_on": [],
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                    "start_period": "60s"
                },
                "deploy": {
                    "resources": {
                        "limits": {
                            "cpus": "2.0",
                            "memory": "4G"
                        },
                        "reservations": {
                            "cpus": "0.5",
                            "memory": "1G"
                        }
                    }
                }
            }
        }
        
        # Add Ollama service
        if include_ollama:
            services["ollama"] = {
                "image": "ollama/ollama:latest",
                "ports": ["11434:11434"],
                "volumes": [
                    "ollama_data:/root/.ollama"
                ],
                "environment": {
                    "OLLAMA_HOST": "0.0.0.0"
                },
                "restart": "unless-stopped",
                "deploy": {
                    "resources": {
                        "limits": {
                            "cpus": "4.0",
                            "memory": "8G"
                        }
                    }
                }
            }
            services["so-assistant-agent"]["depends_on"].append("ollama")
        
        # Add PostgreSQL service
        if include_postgres:
            services["postgres"] = {
                "image": "postgres:15-alpine",
                "ports": ["5432:5432"],
                "environment": {
                    "POSTGRES_DB": "so_assistant",
                    "POSTGRES_USER": "so_user",
                    "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD:-changeme}"
                },
                "volumes": [
                    "postgres_data:/var/lib/postgresql/data",
                    "./init.sql:/docker-entrypoint-initdb.d/init.sql"
                ],
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U so_user -d so_assistant"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5
                }
            }
            services["so-assistant-agent"]["depends_on"].append("postgres")
        
        # Add Redis service
        if include_redis:
            services["redis"] = {
                "image": "redis:7-alpine",
                "ports": ["6379:6379"],
                "volumes": [
                    "redis_data:/data"
                ],
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": "10s",
                    "timeout": "3s",
                    "retries": 3
                }
            }
            services["so-assistant-agent"]["depends_on"].append("redis")
        
        # Define volumes
        volumes = {}
        if include_ollama:
            volumes["ollama_data"] = {}
        if include_postgres:
            volumes["postgres_data"] = {}
        if include_redis:
            volumes["redis_data"] = {}
        
        # Build compose file
        compose_content = {
            "version": "3.8",
            "services": services,
            "volumes": volumes,
            "networks": {
                "so-assistant-network": {
                    "driver": "bridge"
                }
            }
        }
        
        # Add network to all services
        for service in services.values():
            service["networks"] = ["so-assistant-network"]
        
        return self._dict_to_yaml(compose_content)
    
    def _get_app_environment(self) -> Dict[str, str]:
        """Get application environment variables."""
        base_env = {
            "ENVIRONMENT": self.environment,
            "LOG_LEVEL": "INFO" if self.environment == "production" else "DEBUG",
            "OLLAMA_BASE_URL": "http://ollama:11434",
            "DATABASE_URL": "postgresql://so_user:${POSTGRES_PASSWORD:-changeme}@postgres:5432/so_assistant",
            "REDIS_URL": "redis://redis:6379/0",
            "AGENT_MAX_WORKERS": "4",
            "AGENT_CACHE_TTL": "3600",
            "AGENT_PARALLEL_PROCESSING": "true",
            "SECURITY_PII_PROTECTION": "true",
            "SECURITY_AUDIT_LOGGING": "true"
        }
        
        # Environment-specific overrides
        if self.environment == "production":
            base_env.update({
                "SECURITY_LEVEL": "production",
                "AGENT_RATE_LIMIT": "100",
                "AGENT_TIMEOUT": "30"
            })
        elif self.environment == "development":
            base_env.update({
                "SECURITY_LEVEL": "development",
                "AGENT_RATE_LIMIT": "1000",
                "AGENT_TIMEOUT": "60"
            })
        
        return base_env
    
    def _dict_to_yaml(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Convert dictionary to YAML string."""
        yaml_lines = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                yaml_lines.append(f"{'  ' * indent}{key}:")
                yaml_lines.append(self._dict_to_yaml(value, indent + 1))
            elif isinstance(value, list):
                yaml_lines.append(f"{'  ' * indent}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        yaml_lines.append(f"{'  ' * (indent + 1)}-")
                        for sub_key, sub_value in item.items():
                            yaml_lines.append(f"{'  ' * (indent + 2)}{sub_key}: {sub_value}")
                    else:
                        yaml_lines.append(f"{'  ' * (indent + 1)}- {item}")
            else:
                yaml_lines.append(f"{'  ' * indent}{key}: {value}")
        
        return "\\n".join(yaml_lines)
    
    def generate_env_template(self) -> str:
        """Generate .env template file."""
        
        env_template = """# SO Assistant Agent Environment Configuration

# Environment
ENVIRONMENT=production

# Database Configuration
DATABASE_URL=postgresql://so_user:your_password_here@localhost:5432/so_assistant
POSTGRES_PASSWORD=your_secure_password_here

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2:2b

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# Security Configuration
JWT_SECRET=your_jwt_secret_here_change_this_in_production
SECURITY_LEVEL=production
SECURITY_PII_PROTECTION=true
SECURITY_AUDIT_LOGGING=true

# Agent Configuration
AGENT_MAX_WORKERS=4
AGENT_CACHE_TTL=3600
AGENT_PARALLEL_PROCESSING=true
AGENT_RATE_LIMIT=100
AGENT_TIMEOUT=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring Configuration
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30

# Vector Store Configuration (if using external vector store)
# VECTOR_STORE_URL=
# VECTOR_STORE_API_KEY=

# Optional: External monitoring
# SENTRY_DSN=
# PROMETHEUS_ENDPOINT=
"""
        
        return env_template
    
    def generate_kubernetes_manifests(self) -> Dict[str, str]:
        """Generate Kubernetes deployment manifests."""
        
        manifests = {}
        
        # Deployment
        manifests["deployment.yaml"] = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: so-assistant-agent
  labels:
    app: so-assistant-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: so-assistant-agent
  template:
    metadata:
      labels:
        app: so-assistant-agent
    spec:
      containers:
      - name: so-assistant-agent
        image: so-assistant-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: so-assistant-secrets
              key: database-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: so-assistant-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
"""
        
        # Service
        manifests["service.yaml"] = """apiVersion: v1
kind: Service
metadata:
  name: so-assistant-agent-service
spec:
  selector:
    app: so-assistant-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
"""
        
        # Ingress
        manifests["ingress.yaml"] = """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: so-assistant-agent-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: so-assistant-agent.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: so-assistant-agent-service
            port:
              number: 80
"""
        
        # ConfigMap
        manifests["configmap.yaml"] = """apiVersion: v1
kind: ConfigMap
metadata:
  name: so-assistant-config
data:
  AGENT_MAX_WORKERS: "4"
  AGENT_CACHE_TTL: "3600"
  AGENT_PARALLEL_PROCESSING: "true"
  LOG_LEVEL: "INFO"
  METRICS_ENABLED: "true"
"""
        
        # Secret template
        manifests["secret-template.yaml"] = """apiVersion: v1
kind: Secret
metadata:
  name: so-assistant-secrets
type: Opaque
data:
  # Base64 encoded values - replace with actual encoded secrets
  database-url: <base64-encoded-database-url>
  jwt-secret: <base64-encoded-jwt-secret>
  ollama-api-key: <base64-encoded-ollama-api-key>
"""
        
        return manifests


def generate_deployment_files(
    output_dir: str = "./deployment",
    environment: str = "production",
    include_kubernetes: bool = False
) -> None:
    """Generate all deployment files."""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    config = DockerConfig(environment)
    
    # Generate Docker files
    dockerfile = config.generate_dockerfile()
    with open(output_path / "Dockerfile", "w") as f:
        f.write(dockerfile)
    
    docker_compose = config.generate_docker_compose()
    with open(output_path / "docker-compose.yml", "w") as f:
        f.write(docker_compose)
    
    env_template = config.generate_env_template()
    with open(output_path / ".env.template", "w") as f:
        f.write(env_template)
    
    # Generate Kubernetes files if requested
    if include_kubernetes:
        k8s_dir = output_path / "kubernetes"
        k8s_dir.mkdir(exist_ok=True)
        
        k8s_manifests = config.generate_kubernetes_manifests()
        for filename, content in k8s_manifests.items():
            with open(k8s_dir / filename, "w") as f:
                f.write(content)
    
    logger.info(f"Deployment files generated in {output_dir}")


def create_deployment_scripts(output_dir: str = "./deployment") -> None:
    """Create deployment and management scripts."""
    
    output_path = Path(output_dir)
    scripts_dir = output_path / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    # Deploy script
    deploy_script = """#!/bin/bash
set -e

echo "Deploying SO Assistant Agent..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "Please edit .env file with your configuration before running again."
    exit 1
fi

# Build and start services
echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 30

# Check health
echo "Checking service health..."
curl -f http://localhost:8000/health || {
    echo "Health check failed. Checking logs..."
    docker-compose logs so-assistant-agent
    exit 1
}

echo "Deployment completed successfully!"
echo "Agent is available at: http://localhost:8000"
echo "Health check: http://localhost:8000/health"
"""
    
    with open(scripts_dir / "deploy.sh", "w") as f:
        f.write(deploy_script)
    
    # Stop script
    stop_script = """#!/bin/bash
echo "Stopping SO Assistant Agent..."
docker-compose down
echo "Services stopped."
"""
    
    with open(scripts_dir / "stop.sh", "w") as f:
        f.write(stop_script)
    
    # Update script
    update_script = """#!/bin/bash
set -e

echo "Updating SO Assistant Agent..."

# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo "Update completed!"
"""
    
    with open(scripts_dir / "update.sh", "w") as f:
        f.write(update_script)
    
    # Backup script
    backup_script = """#!/bin/bash
set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backup in $BACKUP_DIR..."

# Backup database
docker-compose exec -T postgres pg_dump -U so_user so_assistant > "$BACKUP_DIR/database.sql"

# Backup data volumes
docker run --rm -v so-assistant_postgres_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
docker run --rm -v so-assistant_ollama_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/ollama_data.tar.gz -C /data .

echo "Backup completed in $BACKUP_DIR"
"""
    
    with open(scripts_dir / "backup.sh", "w") as f:
        f.write(backup_script)
    
    # Make scripts executable
    for script_file in scripts_dir.glob("*.sh"):
        script_file.chmod(0o755)
    
    logger.info(f"Deployment scripts created in {scripts_dir}")


if __name__ == "__main__":
    # Generate deployment files for production
    generate_deployment_files(
        output_dir="./deployment",
        environment="production",
        include_kubernetes=True
    )
    
    # Create deployment scripts
    create_deployment_scripts("./deployment")
    
    print("Deployment configuration generated successfully!")
    print("Check the ./deployment directory for all files.")