# Solution Outline Assistant API Documentation

Welcome to the Solution Outline Assistant API documentation. This API helps architects create and manage solution outlines with real-time LLM assistance, versioned documents, Architecture Decision Records (ADRs), and team management capabilities.

## Documentation Structure

- [API Reference](api/README.md) - Complete API endpoint documentation
- [SSE Documentation](sse/README.md) - Server-Sent Events functionality
- [Developer Guide](developer/README.md) - Setup and development guidelines

## Quick Start

### Base URL
```
http://localhost:8000
```

### Authentication
Currently, the API does not require authentication. This may change in future versions.

### Response Format
All API responses follow a standardized format:

```json
{
  "success": true,
  "message": "Success message",
  "data": { /* response data */ },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

For paginated responses:
```json
{
  "success": true,
  "message": "Success message", 
  "data": [ /* array of items */ ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Error Format
Error responses follow this format:
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "details": { /* additional error details */ },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Core Concepts

### Projects
Projects are the main organizational unit. They contain teams, ADRs, and solution outlines.

### Teams
Teams represent groups of people working on a project. They can be assigned to tasks and have members.

### Architecture Decision Records (ADRs)
ADRs document important architectural decisions made during the project lifecycle.

### Solution Outlines
Solution outlines are versioned documents that describe the overall solution architecture and implementation plan.

### Server-Sent Events (SSE)
Real-time communication for streaming LLM responses and live updates.

## Getting Started

1. **Create a Project**: Start by creating a project to organize your work
2. **Add Teams**: Create teams and assign members
3. **Document Decisions**: Create ADRs for important architectural decisions
4. **Create Solution Outline**: Develop your solution outline with LLM assistance
5. **Review and Iterate**: Use the review functionality to improve your documents

## API Features

- **RESTful Design**: Clean, predictable REST API endpoints
- **Pagination**: All list endpoints support pagination, sorting, and filtering
- **Search**: Full-text search across teams, ADRs, and solution outlines
- **Versioning**: Solution outlines support automatic versioning
- **Real-time Updates**: SSE support for streaming LLM responses
- **Error Handling**: Comprehensive error handling with detailed messages
- **Data Validation**: Input validation with clear error messages

## Next Steps

- [Explore the API Reference](api/README.md) for detailed endpoint documentation
- [Learn about SSE functionality](sse/README.md) for real-time features
- [Read the Developer Guide](developer/README.md) for setup instructions