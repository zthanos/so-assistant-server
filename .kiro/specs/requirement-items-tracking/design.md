# Design Document

## Overview

This design document outlines the architecture and implementation approach for adding individual requirement items with status tracking and AI-powered suggestion capabilities to the existing requirements management system. The solution extends the current domain-driven architecture while maintaining consistency with existing patterns and leveraging the established SSE streaming infrastructure.

The system will introduce a new `RequirementItem` model that works alongside the existing `RequirementDocument` model, providing granular tracking of individual requirements with lifecycle management. An AI-powered suggestion endpoint will analyze existing requirements documents and stream intelligent recommendations using the existing SSE infrastructure.

## Architecture

### High-Level Architecture

The solution follows the existing layered architecture pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                     │
├─────────────────────────────────────────────────────────────┤
│                   Service Layer                            │
├─────────────────────────────────────────────────────────────┤
│                  Repository Layer                          │
├─────────────────────────────────────────────────────────────┤
│                   Domain Models                            │
├─────────────────────────────────────────────────────────────┤
│                   Database (SQLite)                        │
└─────────────────────────────────────────────────────────────┘
```

### Component Integration

The new requirement items system integrates with existing components:

- **Projects**: Requirement items belong to projects (foreign key relationship)
- **RequirementDocuments**: Coexist with existing versioned documents
- **SSE Manager**: Used for streaming AI suggestions
- **LLM Service**: Powers the suggestion generation
- **Base Repository**: Extends existing CRUD patterns

## Components and Interfaces

### 1. Domain Model

#### RequirementItem Model

```python
class RequirementItemStatus(enum.Enum):
    """Requirement item status enum."""
    new = "new"
    accepted = "accepted"
    rejected = "rejected"

class RequirementItemPriority(enum.Enum):
    """Requirement item priority enum."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class RequirementItem(Base):
    """Individual requirement item model."""
    __tablename__ = "requirement_items"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Enum(RequirementItemPriority), default=RequirementItemPriority.medium)
    status = Column(Enum(RequirementItemStatus), default=RequirementItemStatus.new)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="requirement_items")
```

### 2. API Schemas

#### Request/Response Schemas

```python
class RequirementItemCreate(BaseModel):
    """Schema for creating requirement items."""
    project_id: str
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    priority: RequirementItemPriority = RequirementItemPriority.medium

class RequirementItemUpdate(BaseModel):
    """Schema for updating requirement items."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[RequirementItemPriority] = None
    status: Optional[RequirementItemStatus] = None

class RequirementItemResponse(BaseModel):
    """Schema for requirement item responses."""
    id: int
    project_id: str
    title: str
    description: str
    priority: RequirementItemPriority
    status: RequirementItemStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RequirementSuggestionRequest(BaseModel):
    """Schema for requirement suggestion requests."""
    project_id: str
    max_suggestions: Optional[int] = Field(default=10, ge=1, le=50)

class RequirementSuggestion(BaseModel):
    """Schema for individual requirement suggestions."""
    title: str
    description: str
    priority: RequirementItemPriority
    rationale: str  # AI explanation for the suggestion
```

### 3. Repository Layer

#### RequirementItemRepository

```python
class RequirementItemRepository(CRUDRepository[RequirementItem, RequirementItemCreate, RequirementItemUpdate]):
    """Repository for requirement items."""
    
    def __init__(self, db: Session):
        super().__init__(RequirementItem)
        self.db = db
    
    def get_by_project(
        self, 
        project_id: str, 
        status: Optional[RequirementItemStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[RequirementItem]:
        """Get requirement items by project with optional status filtering."""
        
    def get_by_project_and_status(
        self, 
        project_id: str, 
        statuses: List[RequirementItemStatus],
        skip: int = 0, 
        limit: int = 100
    ) -> List[RequirementItem]:
        """Get requirement items by project and multiple statuses."""
        
    def count_by_project_and_status(
        self, 
        project_id: str, 
        status: Optional[RequirementItemStatus] = None
    ) -> int:
        """Count requirement items by project and status."""
        
    def update_status(
        self, 
        item_id: int, 
        status: RequirementItemStatus
    ) -> RequirementItem:
        """Update requirement item status."""
```

### 4. Service Layer

#### RequirementItemService

```python
class RequirementItemService:
    """Service for requirement item operations."""
    
    def __init__(
        self, 
        repository: RequirementItemRepository,
        project_repository: ProjectRepository
    ):
        self.repository = repository
        self.project_repository = project_repository
    
    def create_requirement_item(self, item_data: RequirementItemCreate) -> RequirementItem:
        """Create a new requirement item with project validation."""
        
    def get_requirement_item(self, item_id: int) -> RequirementItem:
        """Get requirement item by ID."""
        
    def list_requirement_items(
        self, 
        project_id: Optional[str] = None,
        status: Optional[RequirementItemStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[RequirementItem]:
        """List requirement items with filtering."""
        
    def update_requirement_item(
        self, 
        item_id: int, 
        item_data: RequirementItemUpdate
    ) -> RequirementItem:
        """Update requirement item."""
        
    def delete_requirement_item(self, item_id: int) -> None:
        """Delete requirement item."""
        
    def update_status(
        self, 
        item_id: int, 
        status: RequirementItemStatus
    ) -> RequirementItem:
        """Update requirement item status."""
```

#### RequirementSuggestionService

```python
class RequirementSuggestionService:
    """Service for AI-powered requirement suggestions."""
    
    def __init__(
        self,
        llm_streaming_service: LLMStreamingService,
        requirement_document_repository: RequirementDocumentRepository,
        project_repository: ProjectRepository,
        config: Config
    ):
        self.llm_streaming_service = llm_streaming_service
        self.requirement_document_repository = requirement_document_repository
        self.project_repository = project_repository
        self.config = config
    
    async def stream_requirement_suggestions(
        self,
        client_id: str,
        project_id: str,
        max_suggestions: int = 10
    ) -> None:
        """Stream requirement suggestions using SSE with REQUIREMENTS_LLM_MODEL."""
        
    def _build_suggestion_prompt(
        self, 
        requirements_content: str, 
        max_suggestions: int
    ) -> str:
        """Build the LLM prompt for requirement suggestions."""
        
    def _parse_suggestion_response(self, response: str) -> List[RequirementSuggestion]:
        """Parse LLM response into structured suggestions."""
```

### 5. API Layer

#### RequirementItems Endpoints

```python
@router.post("/requirement-items", response_model=RequirementItemResponse)
def create_requirement_item(item_data: RequirementItemCreate, service: RequirementItemService)

@router.get("/requirement-items", response_model=List[RequirementItemResponse])
def list_requirement_items(
    project_id: Optional[str] = None,
    status: Optional[RequirementItemStatus] = None,
    skip: int = 0,
    limit: int = 100,
    service: RequirementItemService
)

@router.get("/requirement-items/{item_id}", response_model=RequirementItemResponse)
def get_requirement_item(item_id: int, service: RequirementItemService)

@router.put("/requirement-items/{item_id}", response_model=RequirementItemResponse)
def update_requirement_item(
    item_id: int, 
    item_data: RequirementItemUpdate, 
    service: RequirementItemService
)

@router.delete("/requirement-items/{item_id}")
def delete_requirement_item(item_id: int, service: RequirementItemService)

@router.patch("/requirement-items/{item_id}/status", response_model=RequirementItemResponse)
def update_requirement_item_status(
    item_id: int, 
    status: RequirementItemStatus, 
    service: RequirementItemService
)
```

#### Suggestion Endpoint

```python
@router.get("/projects/{project_id}/requirement-suggestions")
async def stream_requirement_suggestions(
    request: Request,
    project_id: str,
    max_suggestions: int = Query(default=10, ge=1, le=50),
    sse_manager: SSEManager = Depends(get_sse_manager),
    suggestion_service: RequirementSuggestionService = Depends(get_suggestion_service)
) -> EventSourceResponse:
    """Stream AI-powered requirement suggestions via SSE."""
```

## Data Models

### Database Schema

#### requirement_items Table

```sql
CREATE TABLE requirement_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'new',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
);

CREATE INDEX idx_requirement_items_project_id ON requirement_items (project_id);
CREATE INDEX idx_requirement_items_status ON requirement_items (status);
CREATE INDEX idx_requirement_items_project_status ON requirement_items (project_id, status);
```

### Relationships

- **RequirementItem** → **Project**: Many-to-One (project_id foreign key)
- **Project** → **RequirementItem**: One-to-Many (back_populates relationship)

### Data Validation Rules

1. **Title**: Required, 1-500 characters
2. **Description**: Required, minimum 1 character
3. **Project ID**: Must reference existing project
4. **Status**: Must be one of: new, accepted, rejected
5. **Priority**: Must be one of: low, medium, high, critical

## Error Handling

### Exception Types

1. **ValidationException**: Invalid input data
2. **NotFoundException**: Resource not found (project, requirement item)
3. **DatabaseException**: Database operation failures
4. **LLMException**: AI service failures
5. **SSEException**: Streaming connection issues

### Error Response Format

```python
{
    "error": {
        "type": "ValidationException",
        "message": "Invalid requirement item data",
        "details": {
            "field": "title",
            "issue": "Title cannot be empty"
        }
    }
}
```

### Status Code Mapping

- **200**: Successful operations
- **201**: Resource created
- **204**: Resource deleted
- **400**: Validation errors
- **404**: Resource not found
- **422**: Unprocessable entity
- **500**: Internal server error

## Testing Strategy

### Unit Tests

1. **Model Tests**
   - RequirementItem model validation
   - Enum value constraints
   - Relationship integrity

2. **Repository Tests**
   - CRUD operations
   - Filtering and pagination
   - Project association validation

3. **Service Tests**
   - Business logic validation
   - Error handling scenarios
   - Status transition rules

4. **Schema Tests**
   - Request/response serialization
   - Validation rules
   - Field constraints

### Integration Tests

1. **API Endpoint Tests**
   - Full CRUD workflow
   - Error response validation
   - Authentication/authorization

2. **Database Integration**
   - Transaction handling
   - Constraint enforcement
   - Performance with large datasets

3. **SSE Streaming Tests**
   - Connection establishment
   - Event streaming
   - Error handling during streaming

### End-to-End Tests

1. **Complete Workflow Tests**
   - Create project → Add requirement items → Update statuses
   - Generate suggestions → Review → Accept/Reject

2. **Performance Tests**
   - Large dataset handling
   - Concurrent request processing
   - SSE connection limits

### Test Data Strategy

- **Fixtures**: Predefined projects and requirement items
- **Factories**: Dynamic test data generation
- **Mocking**: LLM service responses for consistent testing

## AI Integration Details

### LLM Model Configuration

The system will use the `REQUIREMENTS_LLM_MODEL` defined in `config.py` for all requirement suggestion operations. This ensures consistency with other requirement-related LLM interactions in the system.

### LLM Prompt Design

The suggestion system will use structured prompts to generate relevant requirement items:

```
System: You are an expert business analyst specializing in requirements engineering.

User: Based on the following requirements document, suggest additional individual requirement items that might be missing or would complement the existing requirements.

Requirements Document:
{requirements_content}

Please suggest up to {max_suggestions} requirement items in the following JSON format:
[
  {
    "title": "Brief descriptive title",
    "description": "Detailed description of the requirement",
    "priority": "low|medium|high|critical",
    "rationale": "Explanation of why this requirement is suggested"
  }
]

Focus on:
1. Functional requirements that might be implied but not explicitly stated
2. Non-functional requirements (performance, security, usability)
3. Edge cases and error handling scenarios
4. Integration and compatibility requirements
5. Compliance and regulatory requirements
```

### Response Processing

The system will:
1. Use the `REQUIREMENTS_LLM_MODEL` from config for all requirement-related LLM interactions
2. Parse JSON responses from the LLM
3. Validate suggestion structure
4. Stream individual suggestions as they're parsed
5. Handle malformed responses gracefully
6. Provide fallback suggestions if LLM fails

### SSE Event Types

- **suggestion.start**: Suggestion generation started
- **suggestion.item**: Individual suggestion streamed
- **suggestion.complete**: All suggestions generated
- **suggestion.error**: Error during generation

## Performance Considerations

### Database Optimization

1. **Indexes**: Project ID, status, and composite indexes
2. **Pagination**: Limit result sets for large projects
3. **Connection Pooling**: Efficient database connection management

### Caching Strategy

1. **Project Validation**: Cache project existence checks
2. **Suggestion Prompts**: Cache formatted prompts for similar requests
3. **LLM Responses**: Optional caching for identical suggestion requests

### Scalability

1. **Async Processing**: Non-blocking operations for SSE streaming
2. **Background Tasks**: Cleanup and maintenance operations
3. **Resource Limits**: Maximum suggestions per request, connection limits

## Security Considerations

### Input Validation

1. **SQL Injection Prevention**: Parameterized queries
2. **XSS Protection**: Input sanitization
3. **Data Size Limits**: Prevent oversized requests

### Access Control

1. **Project Authorization**: Verify user access to projects
2. **Rate Limiting**: Prevent abuse of suggestion endpoint
3. **SSE Security**: Secure connection establishment

### Data Privacy

1. **Sensitive Data**: Avoid logging sensitive requirement content
2. **LLM Privacy**: Ensure requirements data is handled securely
3. **Audit Trail**: Track requirement item modifications

## Migration Strategy

### Database Migration

```sql
-- Create requirement_items table
CREATE TABLE requirement_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'new',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_requirement_items_project_id ON requirement_items (project_id);
CREATE INDEX idx_requirement_items_status ON requirement_items (status);
CREATE INDEX idx_requirement_items_project_status ON requirement_items (project_id, status);

-- Update projects table to add relationship
-- (This is handled by SQLAlchemy relationships, no schema change needed)
```

### Backward Compatibility

1. **Existing APIs**: No changes to current requirement document APIs
2. **Data Coexistence**: RequirementItem and RequirementDocument work independently
3. **Gradual Adoption**: Teams can adopt item-level tracking incrementally

## Monitoring and Observability

### Metrics

1. **API Metrics**: Request counts, response times, error rates
2. **Business Metrics**: Items created, status transitions, suggestion usage
3. **Performance Metrics**: Database query times, SSE connection counts

### Logging

1. **Structured Logging**: JSON format with correlation IDs
2. **Error Tracking**: Detailed error context and stack traces
3. **Audit Logging**: Requirement item lifecycle events

### Health Checks

1. **Database Connectivity**: Verify database operations
2. **LLM Service**: Check AI service availability
3. **SSE Infrastructure**: Monitor streaming capabilities