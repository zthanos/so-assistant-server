"""Unit tests for RequirementItem API schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.api.schemas.requirements import (
    RequirementItemCreate,
    RequirementItemUpdate,
    RequirementItemResponse,
    RequirementItemStatusUpdate,
    RequirementItemStatus,
    RequirementItemPriority,
    RequirementSuggestionRequest,
    RequirementSuggestion,
    RequirementSuggestionResponse
)


class TestRequirementItemStatus:
    """Test RequirementItemStatus enum."""
    
    def test_enum_values(self):
        """Test that enum has correct values."""
        assert RequirementItemStatus.new == "new"
        assert RequirementItemStatus.accepted == "accepted"
        assert RequirementItemStatus.rejected == "rejected"
    
    def test_enum_members(self):
        """Test that enum has correct members."""
        expected_members = {"new", "accepted", "rejected"}
        actual_members = {status.value for status in RequirementItemStatus}
        assert actual_members == expected_members


class TestRequirementItemPriority:
    """Test RequirementItemPriority enum."""
    
    def test_enum_values(self):
        """Test that enum has correct values."""
        assert RequirementItemPriority.low == "low"
        assert RequirementItemPriority.medium == "medium"
        assert RequirementItemPriority.high == "high"
        assert RequirementItemPriority.critical == "critical"
    
    def test_enum_members(self):
        """Test that enum has correct members."""
        expected_members = {"low", "medium", "high", "critical"}
        actual_members = {priority.value for priority in RequirementItemPriority}
        assert actual_members == expected_members


class TestRequirementItemCreate:
    """Test RequirementItemCreate schema."""
    
    def test_valid_creation(self):
        """Test creating a valid requirement item."""
        data = {
            "project_id": "test-project-1",
            "title": "Test Requirement",
            "description": "This is a test requirement item",
            "priority": "high"
        }
        schema = RequirementItemCreate(**data)
        
        assert schema.project_id == "test-project-1"
        assert schema.title == "Test Requirement"
        assert schema.description == "This is a test requirement item"
        assert schema.priority == RequirementItemPriority.high
    
    def test_default_priority(self):
        """Test that default priority is medium."""
        data = {
            "project_id": "test-project-1",
            "title": "Test Requirement",
            "description": "This is a test requirement item"
        }
        schema = RequirementItemCreate(**data)
        assert schema.priority == RequirementItemPriority.medium
    
    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        # Missing project_id
        with pytest.raises(ValidationError) as exc_info:
            RequirementItemCreate(
                title="Test Requirement",
                description="This is a test requirement item"
            )
        assert "project_id" in str(exc_info.value)
        
        # Missing title
        with pytest.raises(ValidationError) as exc_info:
            RequirementItemCreate(
                project_id="test-project-1",
                description="This is a test requirement item"
            )
        assert "title" in str(exc_info.value)
        
        # Missing description
        with pytest.raises(ValidationError) as exc_info:
            RequirementItemCreate(
                project_id="test-project-1",
                title="Test Requirement"
            )
        assert "description" in str(exc_info.value)
    
    def test_title_length_validation(self):
        """Test title length validation."""
        data = {
            "project_id": "test-project-1",
            "description": "This is a test requirement item"
        }
        
        # Empty title
        with pytest.raises(ValidationError) as exc_info:
            RequirementItemCreate(title="", **data)
        assert "at least 1 character" in str(exc_info.value)
        
        # Title too long (over 500 characters)
        long_title = "A" * 501
        with pytest.raises(ValidationError) as exc_info:
            RequirementItemCreate(title=long_title, **data)
        assert "at most 500 characters" in str(exc_info.value)
        
        # Valid title at max length
        max_title = "A" * 500
        schema = RequirementItemCreate(title=max_title, **data)
        assert len(schema.title) == 500
    
    def test_description_length_validation(self):
        """Test description length validation."""
        data = {
            "project_id": "test-project-1",
            "title": "Test Requirement"
        }
        
        # Empty description
        with pytest.raises(ValidationError) as exc_info:
            RequirementItemCreate(description="", **data)
        assert "at least 1 character" in str(exc_info.value)
    
    def test_invalid_priority(self):
        """Test validation fails with invalid priority."""
        data = {
            "project_id": "test-project-1",
            "title": "Test Requirement",
            "description": "This is a test requirement item",
            "priority": "invalid_priority"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RequirementItemCreate(**data)
        assert "priority" in str(exc_info.value)


class TestRequirementItemUpdate:
    """Test RequirementItemUpdate schema."""
    
    def test_valid_update(self):
        """Test creating a valid update schema."""
        data = {
            "title": "Updated Requirement",
            "description": "Updated description",
            "priority": "critical",
            "status": "accepted"
        }
        schema = RequirementItemUpdate(**data)
        
        assert schema.title == "Updated Requirement"
        assert schema.description == "Updated description"
        assert schema.priority == RequirementItemPriority.critical
        assert schema.status == RequirementItemStatus.accepted
    
    def test_partial_update(self):
        """Test that all fields are optional."""
        # Update only title
        schema = RequirementItemUpdate(title="New Title")
        assert schema.title == "New Title"
        assert schema.description is None
        assert schema.priority is None
        assert schema.status is None
        
        # Update only status
        schema = RequirementItemUpdate(status="rejected")
        assert schema.status == RequirementItemStatus.rejected
        assert schema.title is None
    
    def test_empty_update(self):
        """Test that empty update is valid."""
        schema = RequirementItemUpdate()
        assert schema.title is None
        assert schema.description is None
        assert schema.priority is None
        assert schema.status is None
    
    def test_title_validation_in_update(self):
        """Test title validation in update schema."""
        # Empty title should fail
        with pytest.raises(ValidationError):
            RequirementItemUpdate(title="")
        
        # Too long title should fail
        with pytest.raises(ValidationError):
            RequirementItemUpdate(title="A" * 501)
    
    def test_description_validation_in_update(self):
        """Test description validation in update schema."""
        # Empty description should fail
        with pytest.raises(ValidationError):
            RequirementItemUpdate(description="")


class TestRequirementItemResponse:
    """Test RequirementItemResponse schema."""
    
    def test_valid_response(self):
        """Test creating a valid response schema."""
        data = {
            "id": 1,
            "project_id": "test-project-1",
            "title": "Test Requirement",
            "description": "This is a test requirement item",
            "priority": "high",
            "status": "new",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        schema = RequirementItemResponse(**data)
        
        assert schema.id == 1
        assert schema.project_id == "test-project-1"
        assert schema.title == "Test Requirement"
        assert schema.priority == RequirementItemPriority.high
        assert schema.status == RequirementItemStatus.new
        assert isinstance(schema.created_at, datetime)
        assert isinstance(schema.updated_at, datetime)
    
    def test_json_serialization(self):
        """Test that response can be serialized to JSON."""
        data = {
            "id": 1,
            "project_id": "test-project-1",
            "title": "Test Requirement",
            "description": "This is a test requirement item",
            "priority": "medium",
            "status": "new",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        schema = RequirementItemResponse(**data)
        json_data = schema.model_dump()
        
        assert json_data["id"] == 1
        assert json_data["priority"] == "medium"
        assert json_data["status"] == "new"
        assert isinstance(json_data["created_at"], datetime)


class TestRequirementItemStatusUpdate:
    """Test RequirementItemStatusUpdate schema."""
    
    def test_valid_status_update(self):
        """Test creating a valid status update."""
        schema = RequirementItemStatusUpdate(status="accepted")
        assert schema.status == RequirementItemStatus.accepted
    
    def test_all_valid_statuses(self):
        """Test all valid status values."""
        for status in RequirementItemStatus:
            schema = RequirementItemStatusUpdate(status=status.value)
            assert schema.status == status
    
    def test_invalid_status(self):
        """Test validation fails with invalid status."""
        with pytest.raises(ValidationError) as exc_info:
            RequirementItemStatusUpdate(status="invalid_status")
        assert "status" in str(exc_info.value)
    
    def test_missing_status(self):
        """Test validation fails when status is missing."""
        with pytest.raises(ValidationError) as exc_info:
            RequirementItemStatusUpdate()
        assert "status" in str(exc_info.value)


class TestRequirementSuggestionRequest:
    """Test RequirementSuggestionRequest schema."""
    
    def test_valid_request(self):
        """Test creating a valid suggestion request."""
        schema = RequirementSuggestionRequest(project_id="test-project-1")
        assert schema.project_id == "test-project-1"
        assert schema.max_suggestions == 10  # Default value
    
    def test_custom_max_suggestions(self):
        """Test custom max_suggestions value."""
        schema = RequirementSuggestionRequest(
            project_id="test-project-1",
            max_suggestions=25
        )
        assert schema.max_suggestions == 25
    
    def test_max_suggestions_validation(self):
        """Test max_suggestions validation."""
        # Too low
        with pytest.raises(ValidationError):
            RequirementSuggestionRequest(
                project_id="test-project-1",
                max_suggestions=0
            )
        
        # Too high
        with pytest.raises(ValidationError):
            RequirementSuggestionRequest(
                project_id="test-project-1",
                max_suggestions=51
            )
        
        # Valid boundaries
        schema = RequirementSuggestionRequest(
            project_id="test-project-1",
            max_suggestions=1
        )
        assert schema.max_suggestions == 1
        
        schema = RequirementSuggestionRequest(
            project_id="test-project-1",
            max_suggestions=50
        )
        assert schema.max_suggestions == 50


class TestRequirementSuggestion:
    """Test RequirementSuggestion schema."""
    
    def test_valid_suggestion(self):
        """Test creating a valid suggestion."""
        data = {
            "title": "Suggested Requirement",
            "description": "This is a suggested requirement",
            "priority": "high",
            "rationale": "This requirement is needed because..."
        }
        schema = RequirementSuggestion(**data)
        
        assert schema.title == "Suggested Requirement"
        assert schema.description == "This is a suggested requirement"
        assert schema.priority == RequirementItemPriority.high
        assert schema.rationale == "This requirement is needed because..."
    
    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        # Missing title
        with pytest.raises(ValidationError):
            RequirementSuggestion(
                description="Description",
                priority="medium",
                rationale="Rationale"
            )
        
        # Missing rationale
        with pytest.raises(ValidationError):
            RequirementSuggestion(
                title="Title",
                description="Description",
                priority="medium"
            )


class TestRequirementSuggestionResponse:
    """Test RequirementSuggestionResponse schema."""
    
    def test_valid_response(self):
        """Test creating a valid suggestion response."""
        suggestions = [
            RequirementSuggestion(
                title="Suggestion 1",
                description="Description 1",
                priority="high",
                rationale="Rationale 1"
            ),
            RequirementSuggestion(
                title="Suggestion 2",
                description="Description 2",
                priority="medium",
                rationale="Rationale 2"
            )
        ]
        
        data = {
            "suggestions": suggestions,
            "project_id": "test-project-1",
            "generated_at": datetime.now()
        }
        schema = RequirementSuggestionResponse(**data)
        
        assert len(schema.suggestions) == 2
        assert schema.project_id == "test-project-1"
        assert isinstance(schema.generated_at, datetime)
    
    def test_empty_suggestions(self):
        """Test response with empty suggestions list."""
        data = {
            "suggestions": [],
            "project_id": "test-project-1",
            "generated_at": datetime.now()
        }
        schema = RequirementSuggestionResponse(**data)
        assert len(schema.suggestions) == 0