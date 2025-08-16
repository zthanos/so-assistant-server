# Notes API Documentation

## Overview

The Notes API provides comprehensive functionality for managing project notes with upsert operations, advanced search capabilities, and full CRUD operations. Notes are associated with projects and support rich metadata including tags, descriptions, and content.

## Features

- ✅ **Upsert Operations** - Single endpoint for create and update
- ✅ **Advanced Search** - Search across title, description, and content
- ✅ **Pagination** - All list endpoints support pagination
- ✅ **Filtering** - Filter notes by various criteria
- ✅ **Tagging System** - Organize notes with tags
- ✅ **Rich Content** - Support for title, description, and detailed content
- ✅ **Conflict Detection** - Prevent duplicate titles within projects
- ✅ **DateTime Serialization** - Proper handling of timestamps

## Database Schema

### Notes Table Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Auto | Primary key |
| `project_id` | string | Yes | Associated project ID |
| `title` | string | Yes | Note title (unique per project) |
| `description` | text | No | Brief description or summary |
| `content` | text | No | Detailed content or body |
| `tags` | JSON array | No | List of tags for categorization |
| `created_at` | datetime | Auto | Creation timestamp |
| `updated_at` | datetime | Auto | Last update timestamp |

### Indexes
- Primary key on `id`
- Index on `project_id` for project-based queries
- Index on `title` for title searches
- Index on `created_at` and `updated_at` for sorting

## API Endpoints

### 1. Upsert Note (Create or Update)
**POST** `/api/v1/projects/{project_id}/notes`

Creates a new note or updates an existing one based on the presence of `note_id`.

#### Request Body
```json
{
  "title": "Note Title",
  "description": "Brief description of the note",
  "content": "Detailed content of the note with more information",
  "tags": ["tag1", "tag2", "category"],
  "note_id": 123  // Optional: if provided, updates existing note
}
```

#### Response (200 OK)
```json
{
  "id": 123,
  "project_id": "project_123",
  "title": "Note Title",
  "description": "Brief description of the note",
  "content": "Detailed content of the note with more information",
  "tags": ["tag1", "tag2", "category"],
  "created_at": "2025-08-16T14:30:00.000Z",
  "updated_at": "2025-08-16T14:30:00.000Z"
}
```

### 2. Get Note by ID
**GET** `/api/v1/notes/{note_id}`

Retrieves a specific note by its ID.

#### Response (200 OK)
```json
{
  "id": 123,
  "project_id": "project_123",
  "title": "Note Title",
  "description": "Brief description",
  "content": "Detailed content",
  "tags": ["tag1", "tag2"],
  "created_at": "2025-08-16T14:30:00.000Z",
  "updated_at": "2025-08-16T14:30:00.000Z"
}
```

### 3. Get Notes for Project (Paginated)
**GET** `/api/v1/projects/{project_id}/notes`

Retrieves all notes for a project with pagination, filtering, and search support.

#### Query Parameters
- `page` (integer, default: 1) - Page number
- `per_page` (integer, default: 20, max: 100) - Items per page
- `sort_by` (string) - Field to sort by (title, created_at, updated_at)
- `sort_order` (string) - Sort order (asc, desc)
- `search` (string) - Search term (searches title, description, content)

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Notes retrieved successfully",
  "data": [
    {
      "id": 123,
      "title": "Note Title",
      "description": "Brief description",
      "content": "Detailed content",
      "tags": ["tag1", "tag2"],
      "created_at": "2025-08-16T14:30:00.000Z",
      "updated_at": "2025-08-16T14:30:00.000Z",
      "project_id": "project_123"
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
  "timestamp": "2025-08-16T14:30:00.000Z"
}
```

### 4. Search Notes
**GET** `/api/v1/projects/{project_id}/notes/search`

Search notes by title, description, or content with pagination.

#### Query Parameters
- `query` (string, required) - Search term
- `page` (integer, default: 1) - Page number
- `per_page` (integer, default: 20) - Items per page
- `sort_by` (string) - Field to sort by
- `sort_order` (string) - Sort order

#### Response (200 OK)
Same format as paginated notes list.

### 5. Get Recent Notes
**GET** `/api/v1/projects/{project_id}/notes/recent`

Get the most recently created notes for a project.

#### Query Parameters
- `limit` (integer, default: 5) - Maximum number of notes to return

#### Response (200 OK)
```json
[
  {
    "id": 123,
    "title": "Recent Note",
    "description": "Description",
    "content": "Content",
    "tags": ["recent"],
    "created_at": "2025-08-16T14:30:00.000Z",
    "updated_at": "2025-08-16T14:30:00.000Z",
    "project_id": "project_123"
  }
]
```

### 6. Count Notes
**GET** `/api/v1/projects/{project_id}/notes/count`

Get the total number of notes for a project.

#### Response (200 OK)
```json
42
```

### 7. Delete Note
**DELETE** `/api/v1/notes/{note_id}`

Delete a specific note.

#### Response (200 OK)
Returns the deleted note data.

## Usage Examples

### Create a New Note
```bash
curl -X POST "http://localhost:8000/api/v1/projects/my-project/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Meeting Notes - Sprint Planning",
    "description": "Notes from the sprint planning meeting",
    "content": "Discussed user stories, estimated effort, and assigned tasks...",
    "tags": ["meeting", "sprint-planning", "scrum"]
  }'
```

### Update an Existing Note
```bash
curl -X POST "http://localhost:8000/api/v1/projects/my-project/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Meeting Notes - Sprint Planning",
    "description": "Updated notes with action items",
    "content": "Added action items and follow-up tasks...",
    "tags": ["meeting", "sprint-planning", "scrum", "action-items"],
    "note_id": 123
  }'
```

### Search Notes
```bash
curl "http://localhost:8000/api/v1/projects/my-project/notes/search?query=meeting&page=1&per_page=10"
```

### Get Notes with Pagination
```bash
curl "http://localhost:8000/api/v1/projects/my-project/notes?page=1&per_page=20&sort_by=created_at&sort_order=desc"
```

## Error Responses

### 404 Not Found
```json
{
  "success": false,
  "message": "Note not found",
  "error_code": "NOT_FOUND",
  "details": {
    "resource_type": "Note",
    "resource_id": 123
  },
  "timestamp": "2025-08-16T14:30:00.000Z"
}
```

### 409 Conflict
```json
{
  "success": false,
  "message": "Note with title 'Meeting Notes' already exists for project my-project",
  "error_code": "CONFLICT",
  "details": {
    "resource_type": "Note",
    "resource_id": 456
  },
  "timestamp": "2025-08-16T14:30:00.000Z"
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
      "loc": ["title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "timestamp": "2025-08-16T14:30:00.000Z"
}
```

## Database Migration

Before using the Notes API, run the database migration:

```sql
-- Apply the migration script
mysql -u username -p database_name < create_notes_table_migration.sql
```

## Testing

Test the complete Notes API functionality:

```bash
python test_notes_api.py
```

## Integration with Frontend

The Notes API is designed to work seamlessly with frontend applications:

1. **Rich Text Support** - The `content` field can store formatted text or markdown
2. **Tag-based Organization** - Use tags for filtering and categorization in the UI
3. **Real-time Search** - Implement search-as-you-type functionality
4. **Pagination** - Handle large numbers of notes efficiently
5. **Conflict Prevention** - Automatic duplicate title detection within projects

## Best Practices

1. **Use Descriptive Titles** - Make titles unique and descriptive within each project
2. **Leverage Tags** - Use consistent tagging for better organization
3. **Separate Description and Content** - Use description for summaries, content for details
4. **Implement Search** - Take advantage of the comprehensive search functionality
5. **Handle Conflicts** - Implement proper error handling for duplicate titles
6. **Pagination** - Always implement pagination for note lists in the UI