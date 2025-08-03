# API Reference

This document provides comprehensive documentation for all API endpoints in the Solution Outline Assistant API.

## Table of Contents

- [Projects API](#projects-api)
- [Teams API](#teams-api)
- [Architecture Decision Records (ADRs) API](#adrs-api)
- [Solution Outlines API](#solution-outlines-api)
- [Solution Outline Reviews API](#solution-outline-reviews-api)
- [LLM Integration API](#llm-integration-api)
- [Server-Sent Events API](#server-sent-events-api)

## Common Parameters

### Pagination Parameters
All list endpoints support these pagination parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-based) |
| `per_page` | integer | 20 | Items per page (1-100) |
| `sort_by` | string | null | Field to sort by |
| `sort_order` | string | "asc" | Sort order ("asc" or "desc") |

### Search Parameters
Many endpoints support search functionality:

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search term to filter results |

### Filter Parameters
Advanced filtering using the format `field__operator=value`:

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equal (default) | `name=John` |
| `ne` | Not equal | `status__ne=archived` |
| `gt` | Greater than | `created_at__gt=2023-01-01` |
| `gte` | Greater than or equal | `version__gte=2` |
| `lt` | Less than | `updated_at__lt=2023-12-31` |
| `lte` | Less than or equal | `priority__lte=5` |
| `like` | Contains (case-sensitive) | `title__like=database` |
| `ilike` | Contains (case-insensitive) | `content__ilike=API` |
| `in` | In list | `status__in=draft,published` |
| `not_in` | Not in list | `type__not_in=archived,deleted` |

---

## Projects API

### Create Project
Create a new project.

**Endpoint:** `POST /api/v1/projects`

**Request Body:**
```json
{
  "id": "my-project-id",
  "name": "My Project",
  "description": "Project description",
  "code": "MP001",
  "state": "active"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Project created successfully",
  "data": {
    "id": "my-project-id",
    "name": "My Project",
    "description": "Project description",
    "code": "MP001",
    "state": "active",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Get Project
Retrieve a specific project by ID.

**Endpoint:** `GET /api/v1/projects/{project_id}`

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Project retrieved successfully",
  "data": {
    "id": "my-project-id",
    "name": "My Project",
    "description": "Project description",
    "code": "MP001",
    "state": "active",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Update Project
Update an existing project.

**Endpoint:** `PUT /api/v1/projects/{project_id}`

**Request Body:**
```json
{
  "name": "Updated Project Name",
  "description": "Updated description",
  "code": "UP001",
  "state": "active"
}
```

**Response:** `200 OK` (same format as Get Project)

### Delete Project
Delete a project and all related data.

**Endpoint:** `DELETE /api/v1/projects/{project_id}`

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Project deleted successfully",
  "data": {
    "id": "my-project-id",
    "name": "My Project"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

---

## Teams API

### Create Team
Create a new team for a project.

**Endpoint:** `POST /api/v1/projects/{project_id}/teams`

**Request Body:**
```json
{
  "name": "Frontend Team",
  "members": "Alice Johnson, Bob Smith"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Team created successfully",
  "data": {
    "id": 1,
    "project_id": "my-project-id",
    "name": "Frontend Team",
    "members": "Alice Johnson, Bob Smith",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Get Team
Retrieve a specific team by ID.

**Endpoint:** `GET /api/v1/teams/{team_id}`

**Response:** `200 OK` (same format as Create Team response)

### Get Teams for Project
Retrieve all teams for a project with pagination and filtering.

**Endpoint:** `GET /api/v1/projects/{project_id}/teams`

**Query Parameters:**
- Standard pagination parameters
- `search` - Search in team names and members
- Filter parameters: `name`, `members`, `created_at`, `updated_at`

**Example:** `GET /api/v1/projects/my-project/teams?page=1&per_page=10&search=frontend&sort_by=name`

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Teams retrieved successfully",
  "data": [
    {
      "id": 1,
      "project_id": "my-project-id",
      "name": "Frontend Team",
      "members": "Alice Johnson, Bob Smith",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 1,
    "pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Update Team
Update an existing team.

**Endpoint:** `PUT /api/v1/teams/{team_id}`

**Request Body:**
```json
{
  "name": "Updated Frontend Team",
  "members": "Alice Johnson, Bob Smith, Carol Davis"
}
```

**Response:** `200 OK` (same format as Get Team response)

### Delete Team
Delete a team.

**Endpoint:** `DELETE /api/v1/teams/{team_id}`

**Response:** `200 OK`

### Search Teams
Search teams within a project.

**Endpoint:** `GET /api/v1/projects/{project_id}/teams/search`

**Query Parameters:**
- `query` (required) - Search term
- Standard pagination parameters

**Response:** `200 OK` (same format as Get Teams for Project)

### Count Teams
Get the total number of teams for a project.

**Endpoint:** `GET /api/v1/projects/{project_id}/teams/count`

**Response:** `200 OK`
```json
5
```

---

## ADRs API

### Create ADR
Create a new Architecture Decision Record for a project.

**Endpoint:** `POST /api/v1/projects/{project_id}/adrs`

**Query Parameters:**
- `title` (required) - ADR title
- `content` (required) - ADR content

**Example:** `POST /api/v1/projects/my-project/adrs?title=Database%20Selection&content=We%20chose%20PostgreSQL`

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "ADR created successfully",
  "data": {
    "id": 1,
    "project_id": "my-project-id",
    "title": "Database Selection",
    "content": "We chose PostgreSQL for its reliability and features.",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Get ADR
Retrieve a specific ADR by ID.

**Endpoint:** `GET /api/v1/adrs/{adr_id}`

**Response:** `200 OK` (same format as Create ADR response)

### Get ADRs for Project
Retrieve all ADRs for a project with pagination and filtering.

**Endpoint:** `GET /api/v1/projects/{project_id}/adrs`

**Query Parameters:**
- Standard pagination parameters
- `search` - Search in ADR titles and content
- Filter parameters: `title`, `content`, `created_at`, `updated_at`

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "ADRs retrieved successfully",
  "data": [
    {
      "id": 1,
      "project_id": "my-project-id",
      "title": "Database Selection",
      "content": "We chose PostgreSQL for its reliability and features.",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Update ADR
Update an existing ADR.

**Endpoint:** `PUT /api/v1/adrs/{adr_id}`

**Query Parameters:**
- `title` (optional) - New ADR title
- `content` (optional) - New ADR content

**Response:** `200 OK` (same format as Get ADR response)

### Delete ADR
Delete an ADR.

**Endpoint:** `DELETE /api/v1/adrs/{adr_id}`

**Response:** `200 OK`

### Search ADRs
Search ADRs within a project.

**Endpoint:** `GET /api/v1/projects/{project_id}/adrs/search`

**Query Parameters:**
- `query` (required) - Search term
- Standard pagination parameters

**Response:** `200 OK` (same format as Get ADRs for Project)

### Get Recent ADRs
Get recent ADRs for a project.

**Endpoint:** `GET /api/v1/projects/{project_id}/adrs/recent`

**Query Parameters:**
- `limit` (optional, default: 5) - Number of recent ADRs to return

**Response:** `200 OK`
```json
[
  {
    "id": 3,
    "project_id": "my-project-id",
    "title": "Latest ADR",
    "content": "Most recent decision...",
    "created_at": "2023-01-03T00:00:00Z",
    "updated_at": "2023-01-03T00:00:00Z"
  }
]
```

### Count ADRs
Get the total number of ADRs for a project.

**Endpoint:** `GET /api/v1/projects/{project_id}/adrs/count`

**Response:** `200 OK`
```json
10
```

---

## Solution Outlines API

### Create or Update Solution Outline (Upsert)
Create a new solution outline or update an existing one with automatic versioning using upsert logic.

**Endpoint:** `POST /api/v1/projects/{project_id}/solution-outlines`

**Behavior:**
- If no solution outline exists for the project: Creates version 1
- If solution outline already exists: Creates a new version with incremented version number

**Query Parameters:**
- `content` (required) - Solution outline content
- `status` (optional, default: "draft") - Status: "draft", "published", "archived"

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Solution outline created/updated successfully",
  "data": {
    "id": 2,
    "project_id": "my-project-id",
    "content": "# Updated Solution Outline\n\nThis is the updated content...",
    "version": 2,
    "status": "draft",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T01:00:00Z"
  },
  "timestamp": "2023-01-01T01:00:00Z"
}
```


### Get Latest Solution Outline
Get the latest version of a solution outline for a project.

**Endpoint:** `GET /api/v1/projects/{project_id}/solution-outlines/latest`

**Response:** `200 OK` (same format as Create Solution Outline response)

### Get Solution Outline by Version
Get a specific version of a solution outline.

**Endpoint:** `GET /api/v1/projects/{project_id}/solution-outlines/{version}`

**Response:** `200 OK` (same format as Create Solution Outline response)

### Get Solution Outline Versions
Get all versions of a solution outline for a project.

**Endpoint:** `GET /api/v1/projects/{project_id}/solution-outlines`

**Query Parameters:**
- Standard pagination parameters
- `search` - Search in solution outline content
- Filter parameters: `version`, `status`, `created_at`, `updated_at`

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Solution outline versions retrieved successfully",
  "data": [
    {
      "id": 2,
      "project_id": "my-project-id",
      "content": "# Updated Solution Outline...",
      "version": 2,
      "status": "published",
      "created_at": "2023-01-02T00:00:00Z",
      "updated_at": "2023-01-02T00:00:00Z"
    },
    {
      "id": 1,
      "project_id": "my-project-id",
      "content": "# Solution Outline...",
      "version": 1,
      "status": "draft",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 2,
    "pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "timestamp": "2023-01-02T00:00:00Z"
}
```

### Update Solution Outline Status
Update the status of a specific solution outline version.

**Endpoint:** `PATCH /api/v1/solution-outlines/{id}/status`

**Query Parameters:**
- `status` (required) - New status: "draft", "published", "archived"

**Response:** `200 OK`

### Delete Solution Outline
Delete a specific solution outline version.

**Endpoint:** `DELETE /api/v1/solution-outlines/{id}`

**Response:** `200 OK`

---

## Solution Outline Reviews API

### Request Solution Outline Review
Request an LLM review of a solution outline (streams via SSE).

**Endpoint:** `POST /api/v1/solution-outlines/{solution_outline_id}/review`

**Response:** `200 OK` (Server-Sent Events stream)
```
Content-Type: text/event-stream

event: start
data: {"message": "Starting review process"}

event: chunk
data: {"content": "The solution outline shows..."}

event: complete
data: {"message": "Review completed"}
```

### Get Review Comments
Get all review comments for a solution outline.

**Endpoint:** `GET /api/v1/solution-outlines/{solution_outline_id}/review-comments`

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Review comments retrieved successfully",
  "data": [
    {
      "id": 1,
      "solution_outline_id": 1,
      "content": "Consider adding more details about the database schema.",
      "status": "pending",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Update Review Comment Status
Update the status of a review comment.

**Endpoint:** `PUT /api/v1/review-comments/{comment_id}`

**Request Body:**
```json
{
  "status": "fixed"
}
```

**Response:** `200 OK`

---

## LLM Integration API

### Stream LLM Response
Stream an LLM response via Server-Sent Events.

**Endpoint:** `POST /api/v1/llm/stream`

**Request Body:**
```json
{
  "prompt": "Write a hello world function in Python",
  "prompt_key": "hello_world_example"
}
```

**Response:** `200 OK` (Server-Sent Events stream)
```
Content-Type: text/event-stream

event: start
data: {"message": "Starting LLM processing"}

event: chunk
data: {"content": "def hello_world():"}

event: chunk
data: {"content": "\n    print(\"Hello, World!\")"}

event: complete
data: {"message": "LLM processing complete"}
```

---

## Server-Sent Events API

### Establish SSE Connection
Establish a Server-Sent Events connection for real-time updates.

**Endpoint:** `GET /api/v1/sse`

**Query Parameters:**
- `client_type` (optional) - Type of client for categorization

**Response:** `200 OK` (Server-Sent Events stream)
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: connected
data: {"client_id": "uuid-string", "message": "Connected successfully"}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "success": false,
  "message": "Invalid request data",
  "error_code": "BAD_REQUEST",
  "details": {
    "field": "validation error details"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### 404 Not Found
```json
{
  "success": false,
  "message": "Resource not found",
  "error_code": "NOT_FOUND",
  "details": {
    "resource_type": "Project",
    "resource_id": "non-existent-id"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### 409 Conflict
```json
{
  "success": false,
  "message": "Resource already exists",
  "error_code": "CONFLICT",
  "details": {
    "resource_type": "Team",
    "conflict_field": "name"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### 422 Validation Error
```json
{
  "success": false,
  "message": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "details": [
    {
      "field": "name",
      "message": "This field is required"
    }
  ],
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "message": "Internal server error",
  "error_code": "INTERNAL_SERVER_ERROR",
  "details": {
    "path": "/api/v1/projects",
    "method": "POST"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Rate Limiting

Currently, there are no rate limits implemented. This may change in future versions.

## Versioning

The API is currently at version 1 (`/api/v1/`). Future versions will be released with new version paths to maintain backward compatibility.