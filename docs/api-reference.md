# API Reference: Requirements Versioning System

## Overview

This document provides a comprehensive reference for the Requirements Versioning and PDF Upload System API. All endpoints use RESTful conventions and return JSON responses.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not require authentication. In production environments, implement appropriate authentication mechanisms.

## Common Response Formats

### Success Response
```json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Operation completed successfully",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": { /* error details */ }
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Requirements Management Endpoints

### Create/Update Requirements (Upsert)

Creates a new requirements document or updates an existing one with automatic versioning.

```http
POST /projects/{project_id}/requirements
```

**Parameters:**
- `project_id` (path, required): Project identifier
- `content` (query, required): Markdown content of the requirements document
- `status` (query, optional): Document status (`draft`, `published`, `archived`)

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/projects/my-project/requirements" \
  -d "content=# Requirements Document\n\n1. User authentication\n2. Data storage" \
  -d "status=draft"
```

**Response (201 Created):**
```json
{
  "id": 1,
  "project_id": "my-project",
  "content": "# Requirements Document\n\n1. User authentication\n2. Data storage",
  "version": 1,
  "status": "draft",
  "source_type": "manual",
  "original_filename": null,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid content or parameters
- `404 Not Found`: Project not found
- `422 Unprocessable Entity`: Validation error

---

### Upload PDF Requirements

Uploads a PDF file and converts it to a requirements document using LLM.

```http
POST /projects/{project_id}/requirements/upload-pdf
```

**Parameters:**
- `project_id` (path, required): Project identifier
- `file` (form-data, required): PDF file (max 10MB)
- `status` (query, optional): Document status (default: `draft`)

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/projects/my-project/requirements/upload-pdf" \
  -F "file=@requirements.pdf" \
  -F "status=draft"
```

**Response (201 Created):**
```json
{
  "id": 2,
  "project_id": "my-project",
  "content": "# Requirements Document\n\n*Converted from: requirements.pdf*\n\n## Functional Requirements\n\n1. User authentication system\n2. Data storage capabilities",
  "version": 2,
  "status": "draft",
  "source_type": "pdf_upload",
  "original_filename": "requirements.pdf",
  "created_at": "2023-01-01T01:00:00Z",
  "updated_at": "2023-01-01T01:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file type or empty file
- `413 Request Entity Too Large`: File exceeds size limit
- `422 Unprocessable Entity`: PDF processing failed
- `500 Internal Server Error`: LLM conversion failed

---

### Get Latest Requirements

Retrieves the latest version of requirements for a project.

```http
GET /projects/{project_id}/requirements/latest
```

**Parameters:**
- `project_id` (path, required): Project identifier

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/projects/my-project/requirements/latest"
```

**Response (200 OK):**
```json
{
  "id": 2,
  "project_id": "my-project",
  "content": "# Requirements Document\n\n1. User authentication\n2. Data storage\n3. User management",
  "version": 2,
  "status": "published",
  "source_type": "manual",
  "original_filename": null,
  "created_at": "2023-01-01T01:00:00Z",
  "updated_at": "2023-01-01T01:00:00Z"
}
```

**Empty Response (200 OK):**
If no requirements exist, returns an empty document:
```json
{
  "id": null,
  "project_id": "my-project",
  "content": "",
  "version": 0,
  "status": "draft",
  "source_type": "manual",
  "original_filename": null,
  "created_at": null,
  "updated_at": null
}
```

**Error Responses:**
- `404 Not Found`: Project not found

---

### Get Specific Requirements Version

Retrieves a specific version of requirements document.

```http
GET /projects/{project_id}/requirements/{version}
```

**Parameters:**
- `project_id` (path, required): Project identifier
- `version` (path, required): Version number (≥ 1)

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/projects/my-project/requirements/1"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "project_id": "my-project",
  "content": "# Requirements Document\n\n1. User authentication\n2. Data storage",
  "version": 1,
  "status": "draft",
  "source_type": "manual",
  "original_filename": null,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Project or version not found
- `422 Unprocessable Entity`: Invalid version number

---

### List Requirements Versions

Lists all versions of requirements documents with pagination and filtering.

```http
GET /projects/{project_id}/requirements
```

**Query Parameters:**
- `page` (optional): Page number (default: 1, min: 1)
- `per_page` (optional): Items per page (default: 20, min: 1, max: 100)
- `status_filter` (optional): Filter by status (`draft`, `published`, `archived`)
- `source_type_filter` (optional): Filter by source (`manual`, `pdf_upload`)

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/projects/my-project/requirements?page=1&per_page=10&status_filter=published"
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 3,
      "project_id": "my-project",
      "content": "# Requirements Document v3",
      "version": 3,
      "status": "published",
      "source_type": "pdf_upload",
      "original_filename": "requirements_v3.pdf",
      "created_at": "2023-01-01T02:00:00Z",
      "updated_at": "2023-01-01T02:00:00Z"
    },
    {
      "id": 2,
      "project_id": "my-project",
      "content": "# Requirements Document v2",
      "version": 2,
      "status": "published",
      "source_type": "manual",
      "original_filename": null,
      "created_at": "2023-01-01T01:00:00Z",
      "updated_at": "2023-01-01T01:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "per_page": 10,
  "pages": 1,
  "has_next": false,
  "has_prev": false
}
```

**Error Responses:**
- `404 Not Found`: Project not found
- `422 Unprocessable Entity`: Invalid pagination parameters

---

### Update Requirements Status

Updates the status of a specific requirements document.

```http
PATCH /projects/{project_id}/requirements/{document_id}/status
```

**Parameters:**
- `project_id` (path, required): Project identifier
- `document_id` (path, required): Document ID
- `new_status` (query, required): New status (`draft`, `published`, `archived`)

**Request Example:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/projects/my-project/requirements/1/status?new_status=published"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "project_id": "my-project",
  "content": "# Requirements Document",
  "version": 1,
  "status": "published",
  "source_type": "manual",
  "original_filename": null,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Project or document not found
- `422 Unprocessable Entity`: Invalid status value

---

### Delete Requirements Version

Deletes a specific version of requirements document.

```http
DELETE /projects/{project_id}/requirements/{version}
```

**Parameters:**
- `project_id` (path, required): Project identifier
- `version` (path, required): Version number to delete

**Request Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/projects/my-project/requirements/1"
```

**Response (204 No Content):**
No response body.

**Error Responses:**
- `404 Not Found`: Project or version not found

---

### Get Requirements Summary

Gets summary information about requirements for a project.

```http
GET /projects/{project_id}/requirements/summary
```

**Parameters:**
- `project_id` (path, required): Project identifier

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/projects/my-project/requirements/summary"
```

**Response (200 OK):**
```json
{
  "total_versions": 3,
  "latest_version": 3,
  "status_counts": {
    "draft": 1,
    "published": 2,
    "archived": 0
  },
  "source_type_counts": {
    "manual": 2,
    "pdf_upload": 1
  },
  "project": {
    "id": "my-project",
    "name": "My Project",
    "description": "Project description"
  }
}
```

**Error Responses:**
- `404 Not Found`: Project not found

## Monitoring Endpoints

### Health Check

Gets system health status and basic metrics.

```http
GET /monitoring/health
```

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/health"
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "health_score": 95.5,
  "timestamp": "2023-01-01T00:00:00Z",
  "uptime_seconds": 3600,
  "version": "1.0.0"
}
```

**Status Values:**
- `healthy`: Health score ≥ 90
- `warning`: Health score 70-89
- `degraded`: Health score 50-69
- `critical`: Health score < 50
- `error`: System error occurred

---

### Performance Metrics

Gets detailed performance metrics for all operations.

```http
GET /monitoring/metrics
```

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/metrics"
```

**Response (200 OK):**
```json
{
  "timestamp": "2023-01-01T00:00:00Z",
  "performance_metrics": {
    "upsert_requirements": {
      "count": 150,
      "avg_duration": 0.045,
      "min_duration": 0.012,
      "max_duration": 0.234,
      "recent_avg": 0.038,
      "total_calls": 150
    },
    "process_pdf_upload": {
      "count": 25,
      "avg_duration": 12.5,
      "min_duration": 8.2,
      "max_duration": 28.7,
      "recent_avg": 11.8,
      "total_calls": 25
    }
  },
  "system_info": {
    "cache_entries": 45,
    "active_operations": 3
  }
}
```

---

### System Metrics

Gets current system resource usage metrics.

```http
GET /monitoring/system
```

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/system"
```

**Response (200 OK):**
```json
{
  "timestamp": "2023-01-01T00:00:00Z",
  "uptime_seconds": 3600,
  "psutil_available": true,
  "cpu": {
    "percent": 15.2,
    "count": 8
  },
  "memory": {
    "rss_bytes": 134217728,
    "vms_bytes": 268435456,
    "percent": 12.5,
    "available_bytes": 8589934592
  },
  "disk": {
    "total_bytes": 1099511627776,
    "used_bytes": 549755813888,
    "free_bytes": 549755813888,
    "percent": 50.0
  },
  "network": {
    "connections": 12
  }
}
```

---

### Cache Statistics

Gets cache performance statistics and hit rates.

```http
GET /monitoring/cache
```

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/cache"
```

**Response (200 OK):**
```json
{
  "statistics": {
    "total_entries": 45,
    "estimated_size_bytes": 1048576,
    "hit_rate": 0.85
  },
  "performance_counters": {
    "cache_hit": 850,
    "cache_miss": 150,
    "cache_set": 200,
    "cache_delete": 25,
    "cache_expired": 75,
    "cache_cleanup": 10
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

---

### Recent Alerts

Gets recent performance alerts and warnings.

```http
GET /monitoring/alerts
```

**Query Parameters:**
- `minutes` (optional): Number of minutes to look back (default: 60, min: 1, max: 1440)

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/alerts?minutes=120"
```

**Response (200 OK):**
```json
{
  "alerts": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "alert_type": "memory_usage",
      "severity": "WARNING",
      "message": "High memory usage: 85.2%",
      "metrics": {
        "memory_percent": 85.2
      },
      "threshold_exceeded": "80.0%"
    }
  ],
  "total_alerts": 1,
  "time_range_minutes": 120,
  "query_timestamp": "2023-01-01T00:00:00Z"
}
```

**Severity Levels:**
- `DEBUG`: Informational messages
- `INFO`: Normal operation events
- `WARNING`: Warning conditions
- `ERROR`: Error conditions
- `CRITICAL`: Critical conditions

---

### Dashboard Data

Gets comprehensive monitoring dashboard data.

```http
GET /monitoring/dashboard
```

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/dashboard"
```

**Response (200 OK):**
```json
{
  "timestamp": "2023-01-01T00:00:00Z",
  "health_score": 95.5,
  "system_metrics": {
    "timestamp": "2023-01-01T00:00:00Z",
    "uptime_seconds": 3600,
    "cpu": { "percent": 15.2, "count": 8 },
    "memory": { "percent": 12.5, "rss_bytes": 134217728 }
  },
  "performance_metrics": {
    "upsert_requirements": {
      "count": 150,
      "avg_duration": 0.045
    }
  },
  "cache_statistics": {
    "total_entries": 45,
    "hit_rate": 0.85
  },
  "recent_alerts": [],
  "error_rates": {
    "total_errors_per_minute": 0,
    "total_operations_per_minute": 25
  }
}
```

---

### PDF Processing Status

Gets current PDF processing queue status and statistics.

```http
GET /monitoring/pdf-processing
```

**Request Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/pdf-processing"
```

**Response (200 OK):**
```json
{
  "processor_status": {
    "max_concurrent": 3,
    "active_uploads": 1,
    "available_slots": 2
  },
  "performance_statistics": {
    "process_pdf_upload": {
      "count": 25,
      "avg_duration": 12.5,
      "recent_avg": 11.8
    }
  },
  "counters": {
    "pdf_upload_started": 25,
    "pdf_upload_completed": 24,
    "pdf_upload_failed": 1,
    "pdf_upload_timeout": 0
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

---

### Clear Cache

Clears all cached data (use with caution).

```http
POST /monitoring/cache/clear
```

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/cache/clear"
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Cache cleared successfully",
  "entries_cleared": 45,
  "timestamp": "2023-01-01T00:00:00Z"
}
```

---

### Trigger Cleanup

Triggers cleanup of expired cache entries and temporary data.

```http
POST /monitoring/cleanup
```

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/cleanup"
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Cleanup completed successfully",
  "results": {
    "cache_cleaned": 15,
    "gc_collected": 42
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Error Codes

### HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET, PATCH requests |
| 201 | Created | Successful POST requests |
| 204 | No Content | Successful DELETE requests |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Resource not found |
| 413 | Request Entity Too Large | File too large |
| 422 | Unprocessable Entity | Validation errors |
| 500 | Internal Server Error | Server errors |

### Application Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `VALIDATION_ERROR` | Input validation failed | Check request parameters |
| `PROJECT_NOT_FOUND` | Project does not exist | Verify project ID |
| `VERSION_NOT_FOUND` | Version does not exist | Check version number |
| `DOCUMENT_NOT_FOUND` | Document does not exist | Verify document ID |
| `PDF_PROCESSING_ERROR` | PDF processing failed | Check file format and size |
| `LLM_CONVERSION_ERROR` | LLM conversion failed | Check LLM service status |
| `CACHE_ERROR` | Cache operation failed | Check system resources |
| `DATABASE_ERROR` | Database operation failed | Check database connectivity |

## Rate Limiting

Currently, no rate limiting is implemented. In production environments, consider implementing rate limiting based on:

- Requests per minute per IP
- PDF uploads per hour per project
- Concurrent operations per user

## Pagination

All list endpoints support pagination with the following parameters:

- `page`: Page number (1-based, default: 1)
- `per_page`: Items per page (default: 20, max: 100)

Pagination responses include:
- `total`: Total number of items
- `page`: Current page number
- `per_page`: Items per page
- `pages`: Total number of pages
- `has_next`: Whether there is a next page
- `has_prev`: Whether there is a previous page

## Content Types

### Request Content Types
- `application/x-www-form-urlencoded`: Form parameters
- `multipart/form-data`: File uploads
- `application/json`: JSON payloads (where supported)

### Response Content Types
- `application/json`: All API responses
- `text/plain`: Health check responses (optional)

## Examples

### Complete Workflow Example

```bash
#!/bin/bash

PROJECT_ID="example-project"
BASE_URL="http://localhost:8000/api/v1"

# 1. Create initial requirements
echo "Creating initial requirements..."
curl -X POST "${BASE_URL}/projects/${PROJECT_ID}/requirements" \
  -d "content=# Initial Requirements\n\n1. User authentication\n2. Data storage" \
  -d "status=draft"

# 2. Upload PDF requirements
echo "Uploading PDF requirements..."
curl -X POST "${BASE_URL}/projects/${PROJECT_ID}/requirements/upload-pdf" \
  -F "file=@requirements.pdf" \
  -F "status=draft"

# 3. Get latest requirements
echo "Getting latest requirements..."
curl "${BASE_URL}/projects/${PROJECT_ID}/requirements/latest"

# 4. List all versions
echo "Listing all versions..."
curl "${BASE_URL}/projects/${PROJECT_ID}/requirements?page=1&per_page=10"

# 5. Get summary
echo "Getting summary..."
curl "${BASE_URL}/projects/${PROJECT_ID}/requirements/summary"

# 6. Check system health
echo "Checking system health..."
curl "${BASE_URL}/monitoring/health"
```

### Python Client Example

```python
import requests
import json

class RequirementsClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def create_requirements(self, project_id, content, status="draft"):
        """Create or update requirements."""
        response = requests.post(
            f"{self.base_url}/projects/{project_id}/requirements",
            params={"content": content, "status": status}
        )
        response.raise_for_status()
        return response.json()
    
    def upload_pdf(self, project_id, pdf_path, status="draft"):
        """Upload PDF requirements."""
        with open(pdf_path, "rb") as pdf_file:
            response = requests.post(
                f"{self.base_url}/projects/{project_id}/requirements/upload-pdf",
                files={"file": pdf_file},
                params={"status": status}
            )
        response.raise_for_status()
        return response.json()
    
    def get_latest(self, project_id):
        """Get latest requirements."""
        response = requests.get(
            f"{self.base_url}/projects/{project_id}/requirements/latest"
        )
        response.raise_for_status()
        return response.json()
    
    def list_versions(self, project_id, page=1, per_page=20, **filters):
        """List all versions with optional filtering."""
        params = {"page": page, "per_page": per_page}
        params.update(filters)
        
        response = requests.get(
            f"{self.base_url}/projects/{project_id}/requirements",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_health(self):
        """Get system health."""
        response = requests.get(f"{self.base_url}/monitoring/health")
        response.raise_for_status()
        return response.json()

# Usage example
client = RequirementsClient()

# Create requirements
doc = client.create_requirements(
    "my-project", 
    "# My Requirements\n\n1. Authentication\n2. Storage"
)
print(f"Created version {doc['version']}")

# Get health status
health = client.get_health()
print(f"System health: {health['status']} ({health['health_score']})")
```

This API reference provides comprehensive documentation for all endpoints in the Requirements Versioning and PDF Upload System. Use this reference to integrate with the system and build client applications.