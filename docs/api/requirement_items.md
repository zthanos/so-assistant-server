# Requirement Items API Documentation

## Overview

The Requirement Items API provides comprehensive CRUD operations for managing individual requirement items within projects. It includes advanced features like AI-powered suggestions, status lifecycle management, bulk operations, and real-time streaming capabilities.

## Base URL

All requirement items endpoints are available under:
```
/api/v1/requirement-items
```

## Authentication

All endpoints require proper authentication. Include your authentication token in the request headers.

## Data Models

### RequirementItem

```json
{
  "id": 1,
  "project_id": "project-123",
  "title": "User Authentication",
  "description": "The system shall provide secure user authentication",
  "priority": "high",
  "status": "new",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### Enums

**Priority Levels:**
- `low` - Low priority requirement
- `medium` - Medium priority requirement (default)
- `high` - High priority requirement
- `critical` - Critical priority requirement

**Status Values:**
- `new` - Newly created requirement (default)
- `accepted` - Approved requirement
- `rejected` - Rejected requirement

## Endpoints

### 1. Create Requirement Item

Create a new requirement item for a project.

**Endpoint:** `POST /api/v1/requirement-items`

**Request Body:**
```json
{
  "project_id": "project-123",
  "title": "User Authentication",
  "description": "The system shall provide secure user authentication using email and password",
  "priority": "high"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "project_id": "project-123",
  "title": "User Authentication",
  "description": "The system shall provide secure user authentication using email and password",
  "priority": "high",
  "status": "new",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Project not found
- `422 Unprocessable Entity` - Validation errors

### 2. Get Requirement Item

Retrieve a specific requirement item by ID.

**Endpoint:** `GET /api/v1/requirement-items/{item_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "project_id": "project-123",
  "title": "User Authentication",
  "description": "The system shall provide secure user authentication using email and password",
  "priority": "high",
  "status": "accepted",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T11:45:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Requirement item not found

### 3. List Requirement Items

List requirement items with optional filtering and pagination.

**Endpoint:** `GET /api/v1/requirement-items`

**Query Parameters:**
- `project_id` (optional) - Filter by project ID
- `status` (optional) - Filter by status (new, accepted, rejected)
- `priority` (optional) - Filter by priority (low, medium, high, critical)
- `skip` (optional, default: 0) - Number of items to skip
- `limit` (optional, default: 100, max: 1000) - Maximum items to return

**Examples:**
```bash
# Get all requirement items
GET /api/v1/requirement-items

# Get items for a specific project
GET /api/v1/requirement-items?project_id=project-123

# Get accepted items for a project
GET /api/v1/requirement-items?project_id=project-123&status=accepted

# Get high priority items with pagination
GET /api/v1/requirement-items?priority=high&skip=0&limit=20
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "project_id": "project-123",
    "title": "User Authentication",
    "description": "The system shall provide secure user authentication",
    "priority": "high",
    "status": "accepted",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T11:45:00Z"
  },
  {
    "id": 2,
    "project_id": "project-123",
    "title": "Password Reset",
    "description": "The system shall allow users to reset their passwords",
    "priority": "medium",
    "status": "new",
    "created_at": "2025-01-15T10:35:00Z",
    "updated_at": "2025-01-15T10:35:00Z"
  }
]
```

### 4. Upsert Requirement Item

Create a new requirement item or update an existing one (upsert operation).

**Endpoint:** `POST /api/v1/requirement-items/upsert`

**Query Parameters:**
- `item_id` (optional) - The ID of the requirement item to update (omit for create)

**Request Body:**
```json
{
  "project_id": "project-123",
  "title": "Enhanced User Authentication",
  "description": "The system shall provide secure user authentication with multi-factor support",
  "priority": "critical",
  "status": "accepted"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "project_id": "project-123",
  "title": "Enhanced User Authentication",
  "description": "The system shall provide secure user authentication with multi-factor support",
  "priority": "critical",
  "status": "accepted",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T12:00:00Z"
}
```

**Examples:**
```bash
# Create new requirement item
POST /api/v1/requirement-items/upsert
# (omit item_id query parameter)

# Update existing requirement item
POST /api/v1/requirement-items/upsert?item_id=1
```

### 4b. Upsert Requirement Item by ID

Update a specific requirement item using path parameter.

**Endpoint:** `POST /api/v1/requirement-items/upsert/{item_id}`

**Request Body:**
```json
{
  "project_id": "project-123",
  "title": "Enhanced User Authentication",
  "description": "The system shall provide secure user authentication with multi-factor support",
  "priority": "critical",
  "status": "accepted"
}
```

**Response:** `200 OK` (same as above)

### 5. Batch Upsert Requirement Items

Create or update multiple requirement items in a single operation.

**Endpoint:** `POST /api/v1/requirement-items/batch-upsert`

**Request Body:**
```json
{
  "items": [
    {
      "id": 1,
      "project_id": "project-123",
      "title": "First Requirement",
      "description": "This is the first requirement",
      "priority": "high",
      "status": "new"
    },
    {
      "id": 2,
      "project_id": "project-123",
      "title": "Second Requirement",
      "description": "This is the second requirement",
      "priority": "medium"
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "success_count": 2,
  "error_count": 0,
  "results": [
    {
      "id": 1,
      "status": "success",
      "item": {
        "id": 1,
        "project_id": "project-123",
        "title": "First Requirement",
        "description": "This is the first requirement",
        "priority": "high",
        "status": "new",
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T10:30:00Z"
      }
    },
    {
      "id": 2,
      "status": "success",
      "item": {
        "id": 2,
        "project_id": "project-123",
        "title": "Second Requirement",
        "description": "This is the second requirement",
        "priority": "medium",
        "status": "new",
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T10:30:00Z"
      }
    }
  ]
}
```

**Features:**
- Process up to 100 items in a single request
- Individual error handling - some items can succeed while others fail
- Detailed results for each item with success/error status
- Atomic operations per item (each item is processed independently)

### 6. Delete Requirement Item

Delete a requirement item.

**Endpoint:** `DELETE /api/v1/requirement-items/{item_id}`

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found` - Requirement item not found

### 7. Update Status

Update only the status of a requirement item.

**Endpoint:** `PATCH /api/v1/requirement-items/{item_id}/status`

**Request Body:**
```json
{
  "status": "accepted"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "project_id": "project-123",
  "title": "User Authentication",
  "description": "The system shall provide secure user authentication",
  "priority": "high",
  "status": "accepted",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T12:15:00Z"
}
```

### 8. Bulk Status Update

Update the status of multiple requirement items at once.

**Endpoint:** `PATCH /api/v1/requirement-items/bulk/status`

**Request Body:**
```json
{
  "item_ids": [1, 2, 3],
  "status": "accepted"
}
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "project_id": "project-123",
    "title": "User Authentication",
    "description": "The system shall provide secure user authentication",
    "priority": "high",
    "status": "accepted",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T12:20:00Z"
  },
  {
    "id": 2,
    "project_id": "project-123",
    "title": "Password Reset",
    "description": "The system shall allow users to reset their passwords",
    "priority": "medium",
    "status": "accepted",
    "created_at": "2025-01-15T10:35:00Z",
    "updated_at": "2025-01-15T12:20:00Z"
  }
]
```

### 9. Search Requirement Items

Search requirement items by title within a project.

**Endpoint:** `GET /api/v1/requirement-items/projects/{project_id}/search`

**Query Parameters:**
- `q` (required) - Search term
- `skip` (optional, default: 0) - Number of items to skip
- `limit` (optional, default: 100, max: 1000) - Maximum items to return

**Example:**
```bash
GET /api/v1/requirement-items/projects/project-123/search?q=authentication
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "project_id": "project-123",
    "title": "User Authentication",
    "description": "The system shall provide secure user authentication",
    "priority": "high",
    "status": "accepted",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T11:45:00Z"
  }
]
```

### 10. Get Project Status Summary

Get a summary of requirement items by status for a project.

**Endpoint:** `GET /api/v1/requirement-items/projects/{project_id}/summary`

**Response:** `200 OK`
```json
{
  "new": 5,
  "accepted": 12,
  "rejected": 2
}
```

### 11. Get Items by Multiple Statuses

Get requirement items filtered by multiple statuses.

**Endpoint:** `GET /api/v1/requirement-items/projects/{project_id}/by-status`

**Query Parameters:**
- `statuses` (required, multiple) - List of statuses to filter by
- `skip` (optional, default: 0) - Number of items to skip
- `limit` (optional, default: 100, max: 1000) - Maximum items to return

**Example:**
```bash
GET /api/v1/requirement-items/projects/project-123/by-status?statuses=new&statuses=accepted
```

### 12. AI-Powered Suggestions (SSE)

Stream AI-generated requirement suggestions based on existing requirements document.

**Endpoint:** `GET /api/v1/requirement-items/projects/{project_id}/suggestions`

**Query Parameters:**
- `max_suggestions` (optional, default: 10, range: 1-50) - Maximum suggestions to generate

**Response:** Server-Sent Events (SSE) stream

**Event Types:**
- `suggestion.start` - Suggestion generation started
- `suggestion.item` - Individual suggestion received
- `suggestion.complete` - All suggestions generated
- `suggestion.error` - Error occurred

**Example SSE Events:**
```
event: suggestion.start
data: {"message": "Starting requirement suggestions generation", "project_id": "project-123", "max_suggestions": 10}

event: suggestion.item
data: {"suggestion": {"title": "Session Timeout", "description": "The system shall automatically log out users after 30 minutes of inactivity", "priority": "medium", "rationale": "Essential for security to prevent unauthorized access"}, "project_id": "project-123"}

event: suggestion.complete
data: {"message": "Requirement suggestions generation complete", "project_id": "project-123", "total_suggestions": 5}
```

### 13. System Health

Get health status and performance metrics.

**Endpoint:** `GET /api/v1/requirement-items/health`

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "health_metrics": {
    "status": "healthy",
    "total_operations": 1250,
    "error_rate_percent": 0.8,
    "slow_operations": 2,
    "active_projects_24h": 15
  },
  "performance_analysis": {
    "statistics": {
      "total_items": 2500,
      "unique_projects": 25,
      "new_items": 150,
      "accepted_items": 2200,
      "rejected_items": 150
    },
    "performance_issues": [],
    "recommendations": ["Performance appears optimal for current data size"]
  },
  "timestamp": "2025-01-15T12:30:00Z"
}
```

## Usage Examples

### JavaScript/TypeScript

```typescript
// Create a requirement item
const createRequirementItem = async (projectId: string, itemData: any) => {
  const response = await fetch('/api/v1/requirement-items', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_TOKEN'
    },
    body: JSON.stringify({
      project_id: projectId,
      ...itemData
    })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
};

// Get requirement items for a project
const getProjectRequirements = async (projectId: string, status?: string) => {
  const params = new URLSearchParams({ project_id: projectId });
  if (status) params.append('status', status);
  
  const response = await fetch(`/api/v1/requirement-items?${params}`, {
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN'
    }
  });
  
  return await response.json();
};

// Upsert (create or update) requirement item
const upsertRequirementItem = async (itemData: any, itemId?: number) => {
  const url = itemId 
    ? `/api/v1/requirement-items/upsert?item_id=${itemId}`
    : '/api/v1/requirement-items/upsert';
    
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_TOKEN'
    },
    body: JSON.stringify(itemData)
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
};

// Batch upsert multiple requirement items
const batchUpsertRequirementItems = async (items: any[]) => {
  const response = await fetch('/api/v1/requirement-items/batch-upsert', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_TOKEN'
    },
    body: JSON.stringify({ items })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
};

// Update requirement status
const updateRequirementStatus = async (itemId: number, status: string) => {
  const response = await fetch(`/api/v1/requirement-items/${itemId}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_TOKEN'
    },
    body: JSON.stringify({ status })
  });
  
  return await response.json();
};

// Listen to AI suggestions via SSE
const listenToSuggestions = (projectId: string, maxSuggestions: number = 10) => {
  const eventSource = new EventSource(
    `/api/v1/requirement-items/projects/${projectId}/suggestions?max_suggestions=${maxSuggestions}`
  );
  
  eventSource.addEventListener('suggestion.start', (event) => {
    console.log('Suggestion generation started:', JSON.parse(event.data));
  });
  
  eventSource.addEventListener('suggestion.item', (event) => {
    const data = JSON.parse(event.data);
    console.log('New suggestion:', data.suggestion);
    // Handle individual suggestion
  });
  
  eventSource.addEventListener('suggestion.complete', (event) => {
    console.log('Suggestions complete:', JSON.parse(event.data));
    eventSource.close();
  });
  
  eventSource.addEventListener('suggestion.error', (event) => {
    console.error('Suggestion error:', JSON.parse(event.data));
    eventSource.close();
  });
  
  return eventSource;
};
```

### Python

```python
import requests
import json
from typing import List, Dict, Any, Optional

class RequirementItemsClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_requirement_item(self, project_id: str, title: str, 
                              description: str, priority: str = 'medium') -> Dict[str, Any]:
        """Create a new requirement item."""
        data = {
            'project_id': project_id,
            'title': title,
            'description': description,
            'priority': priority
        }
        
        response = requests.post(
            f'{self.base_url}/api/v1/requirement-items',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_requirement_items(self, project_id: Optional[str] = None, 
                            status: Optional[str] = None,
                            skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get requirement items with optional filtering."""
        params = {'skip': skip, 'limit': limit}
        if project_id:
            params['project_id'] = project_id
        if status:
            params['status'] = status
        
        response = requests.get(
            f'{self.base_url}/api/v1/requirement-items',
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def upsert_requirement_item(self, item_data: Dict[str, Any], item_id: Optional[int] = None) -> Dict[str, Any]:
        """Create or update a requirement item (upsert operation)."""
        if item_id:
            url = f'{self.base_url}/api/v1/requirement-items/upsert?item_id={item_id}'
        else:
            url = f'{self.base_url}/api/v1/requirement-items/upsert'
        
        response = requests.post(
            url,
            headers=self.headers,
            json=item_data
        )
        response.raise_for_status()
        return response.json()
    
    def update_requirement_status(self, item_id: int, status: str) -> Dict[str, Any]:
        """Update requirement item status."""
        data = {'status': status}
        
        response = requests.patch(
            f'{self.base_url}/api/v1/requirement-items/{item_id}/status',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def batch_upsert_requirement_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch upsert multiple requirement items."""
        data = {'items': items}
        
        response = requests.post(
            f'{self.base_url}/api/v1/requirement-items/batch-upsert',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def bulk_update_status(self, item_ids: List[int], status: str) -> List[Dict[str, Any]]:
        """Bulk update requirement item statuses."""
        data = {
            'item_ids': item_ids,
            'status': status
        }
        
        response = requests.patch(
            f'{self.base_url}/api/v1/requirement-items/bulk/status',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def search_requirements(self, project_id: str, search_term: str,
                          skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Search requirement items by title."""
        params = {
            'q': search_term,
            'skip': skip,
            'limit': limit
        }
        
        response = requests.get(
            f'{self.base_url}/api/v1/requirement-items/projects/{project_id}/search',
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_project_summary(self, project_id: str) -> Dict[str, int]:
        """Get project requirement items status summary."""
        response = requests.get(
            f'{self.base_url}/api/v1/requirement-items/projects/{project_id}/summary',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = RequirementItemsClient('http://localhost:8000', 'your-token')

# Create a requirement item using upsert
item = client.upsert_requirement_item({
    'project_id': 'project-123',
    'title': 'User Authentication',
    'description': 'The system shall provide secure user authentication',
    'priority': 'high'
})

# Update a requirement item using upsert
updated_item = client.upsert_requirement_item({
    'project_id': 'project-123',
    'title': 'Enhanced User Authentication',
    'description': 'The system shall provide secure user authentication with MFA',
    'priority': 'critical',
    'status': 'accepted'
}, item_id=item['id'])

# Get all items for a project
items = client.get_requirement_items(project_id='project-123')

# Update status only
status_updated_item = client.update_requirement_status(item['id'], 'accepted')

# Get project summary
summary = client.get_project_summary('project-123')
print(f"Project has {summary['accepted']} accepted requirements")
```

### cURL Examples

```bash
# Create a requirement item (upsert without item_id)
curl -X POST "http://localhost:8000/api/v1/requirement-items/upsert" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "project-123",
    "title": "User Authentication",
    "description": "The system shall provide secure user authentication",
    "priority": "high"
  }'

# Update a requirement item (upsert with item_id)
curl -X POST "http://localhost:8000/api/v1/requirement-items/upsert?item_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "project-123",
    "title": "Enhanced User Authentication",
    "description": "The system shall provide secure user authentication with MFA",
    "priority": "critical",
    "status": "accepted"
  }'

# Get requirement items for a project
curl -X GET "http://localhost:8000/api/v1/requirement-items?project_id=project-123" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update requirement status
curl -X PATCH "http://localhost:8000/api/v1/requirement-items/1/status" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "accepted"}'

# Bulk update statuses
curl -X PATCH "http://localhost:8000/api/v1/requirement-items/bulk/status" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": [1, 2, 3],
    "status": "accepted"
  }'

# Batch upsert multiple requirement items
curl -X POST "http://localhost:8000/api/v1/requirement-items/batch-upsert" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "id": 1,
        "project_id": "project-123",
        "title": "First Requirement",
        "description": "This is the first requirement",
        "priority": "high"
      },
      {
        "id": 2,
        "project_id": "project-123",
        "title": "Second Requirement",
        "description": "This is the second requirement",
        "priority": "medium"
      }
    ]
  }'

# Search requirements
curl -X GET "http://localhost:8000/api/v1/requirement-items/projects/project-123/search?q=authentication" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get project summary
curl -X GET "http://localhost:8000/api/v1/requirement-items/projects/project-123/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get system health
curl -X GET "http://localhost:8000/api/v1/requirement-items/health" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Error Handling

All endpoints return standardized error responses:

```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_TYPE",
  "details": {
    "field": "specific_field",
    "issue": "validation_issue"
  }
}
```

Common HTTP status codes:
- `200 OK` - Successful operation
- `201 Created` - Resource created successfully
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server error

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- Standard endpoints: 1000 requests per hour per user
- AI suggestions endpoint: 10 requests per hour per project
- Bulk operations: 100 requests per hour per user

## Best Practices

1. **Use pagination** for large result sets to improve performance
2. **Filter by project** when possible to reduce response size
3. **Use bulk operations** for updating multiple items efficiently
4. **Handle SSE connections properly** by listening for all event types
5. **Implement retry logic** for transient errors
6. **Cache frequently accessed data** to reduce API calls
7. **Use specific error handling** based on HTTP status codes
8. **Monitor API health** using the health endpoint for production systems