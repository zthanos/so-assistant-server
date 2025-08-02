"""Tests for the Solution Outline Review API endpoints.

This module contains unit tests for the Solution Outline Review API endpoints.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, BackgroundTasks
from sse_starlette.sse import EventSourceResponse

from app.api.v1.endpoints.solution_outline_reviews import router
from app.domain.models.review_comments import ReviewCommentStatus
from app.core.exceptions import NotFoundException, LLMException

# Create a test FastAPI app
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Mock service and dependencies
mock_service = MagicMock()
mock_client_id = "test-client-id"
mock_sse = MagicMock(spec=EventSourceResponse)

# Mock review comment
mock_review_comment = {
    "id": 1,
    "solution_outline_id": 1,
    "content": "Test comment",
    "status": ReviewCommentStatus.pending,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
}

# Override dependencies
@pytest.fixture(autouse=True)
def override_dependencies():
    """Override dependencies for testing."""
    with patch("app.api.v1.endpoints.solution_outline_reviews.get_solution_outline_review_service", return_value=mock_service), \
         patch("app.api.v1.endpoints.solution_outline_reviews.get_sse_connection", return_value=(mock_client_id, mock_sse)):
        yield

class TestSolutionOutlineReviewEndpoints:
    """Test cases for the Solution Outline Review API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset mocks
        mock_service.reset_mock()
        mock_sse.reset_mock()
    
    def test_get_review_comments(self):
        """Test getting review comments."""
        # Arrange
        mock_service.get_review_comments.return_value = [mock_review_comment]
        
        # Act
        response = client.get("/solution-outlines/1/review-comments")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_review_comments.assert_called_once_with(1, 0, 100)
        assert response.json() == [mock_review_comment]
    
    def test_get_review_comments_with_status(self):
        """Test getting review comments with status filter."""
        # Arrange
        mock_service.get_review_comments_by_status.return_value = [mock_review_comment]
        
        # Act
        response = client.get("/solution-outlines/1/review-comments?status=pending")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_review_comments_by_status.assert_called_once_with(1, ReviewCommentStatus.pending, 0, 100)
        assert response.json() == [mock_review_comment]
    
    def test_update_comment_status(self):
        """Test updating a comment status."""
        # Arrange
        mock_service.update_comment_status.return_value = mock_review_comment
        
        # Act
        response = client.patch(
            "/review-comments/1/status",
            json={"status": "fixed"}
        )
        
        # Assert
        assert response.status_code == 200
        mock_service.update_comment_status.assert_called_once_with(1, ReviewCommentStatus.fixed)
        assert response.json() == mock_review_comment
    
    def test_update_comment_status_not_found(self):
        """Test updating a comment status when the comment is not found."""
        # Arrange
        mock_service.update_comment_status.side_effect = NotFoundException("Comment not found")
        
        # Act
        response = client.patch(
            "/review-comments/1/status",
            json={"status": "fixed"}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Comment not found"
    
    def test_bulk_update_comment_status(self):
        """Test bulk updating comment statuses."""
        # Arrange
        mock_service.bulk_update_comment_status.return_value = [mock_review_comment]
        
        # Act
        response = client.patch(
            "/solution-outlines/1/review-comments/bulk-status?comment_ids=1&comment_ids=2&status=fixed"
        )
        
        # Assert
        assert response.status_code == 200
        mock_service.bulk_update_comment_status.assert_called_once_with([1, 2], ReviewCommentStatus.fixed)
        assert response.json() == [mock_review_comment]
    
    def test_get_status_counts(self):
        """Test getting status counts."""
        # Arrange
        mock_service.get_status_counts.return_value = {
            ReviewCommentStatus.pending: 1,
            ReviewCommentStatus.fixed: 2,
            ReviewCommentStatus.rejected: 0
        }
        
        # Act
        response = client.get("/solution-outlines/1/review-comments/status-counts")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_status_counts.assert_called_once_with(1)
        assert response.json() == {
            "pending": 1,
            "fixed": 2,
            "rejected": 0
        }