# REST API Endpoints Summary

## ✅ Projects API
Base path: `/api/v1/projects`

- **POST** `/api/v1/projects` - Create a new project
- **GET** `/api/v1/projects` - List all projects
- **GET** `/api/v1/projects/{project_id}` - Get a specific project
- **PUT** `/api/v1/projects/{project_id}` - Update a project
- **DELETE** `/api/v1/projects/{project_id}` - Delete a project
- **GET** `/api/v1/projects/{project_id}/outline` - Get project with all related entities

## ✅ Requirements API
Base path: `/api/v1/projects/{project_id}/requirements`

- **POST** `/api/v1/projects/{project_id}/requirements` - Create a requirement
- **GET** `/api/v1/projects/{project_id}/requirements` - List requirements for a project
- **GET** `/api/v1/projects/{project_id}/requirements/{requirement_id}` - Get a specific requirement
- **PUT** `/api/v1/projects/{project_id}/requirements/{requirement_id}` - Update a requirement
- **DELETE** `/api/v1/projects/{project_id}/requirements/{requirement_id}` - Delete a requirement

## ✅ Diagrams API
Base path: `/api/v1/projects/{project_id}/diagrams`

- **POST** `/api/v1/projects/{project_id}/diagrams` - Create a diagram
- **GET** `/api/v1/projects/{project_id}/diagrams` - List diagrams for a project
- **GET** `/api/v1/projects/{project_id}/diagrams/{diagram_id}` - Get a specific diagram
- **PUT** `/api/v1/projects/{project_id}/diagrams/{diagram_id}` - Update a diagram
- **DELETE** `/api/v1/projects/{project_id}/diagrams/{diagram_id}` - Delete a diagram

## Status
- ✅ **Projects API**: Fully functional (including project outline endpoint)
- ✅ **Diagrams API**: Fully functional
- ⚠️ **Requirements API**: Functional but has enum validation issue (expects "Functional"/"Non-Functional" values)

## Example Usage

### Create a Project
```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-project-123",
    "name": "My Test Project",
    "description": "A test project",
    "code": "TEST001"
  }'
```

### Create a Diagram
```bash
curl -X POST "http://localhost:8000/api/v1/projects/my-project-123/diagrams" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "System Architecture",
    "mermaid_code": "graph TD\n    A[Client] --> B[Server]",
    "type": "architecture"
  }'
```

### Create a Requirement
```bash
curl -X POST "http://localhost:8000/api/v1/projects/my-project-123/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "The system shall provide user authentication",
    "category": "Functional"
  }'
```

All endpoints follow RESTful conventions and include proper error handling, validation, and documentation.