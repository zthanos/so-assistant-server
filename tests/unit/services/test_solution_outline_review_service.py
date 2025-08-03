"""Tests for the SolutionOutlineReviewService.

This module contains unit tests for the SolutionOutlineReviewService class.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.solution_outline_reviews import SolutionOutlineReviewService
from app.domain.models.review_comments import ReviewComment, ReviewCommentStatus
from app.api.schemas.review_comments import ReviewCommentCreate
from app.core.exceptions import NotFoundException, LLMException

class TestSolutionOutlineReviewService:
    """Test cases for the SolutionOutlineReviewService class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db = MagicMock(spec=Session)
        self.solution_outline_repository = MagicMock()
        self.review_comment_repository = MagicMock()
        self.sse_manager = MagicMock()
        self.ollama_client = MagicMock()
        
        # Create service with mocked dependencies
        self.service = SolutionOutlineReviewService(self.db, self.sse_manager, self.ollama_client)
        self.service.solution_outline_repository = self.solution_outline_repository
        self.service.review_comment_repository = self.review_comment_repository
        
        # Mock solution outline
        self.solution_outline = MagicMock()
        self.solution_outline.id = 1
        self.solution_outline.content = "Test content"
        
        # Mock review comment
        self.review_comment = MagicMock(spec=ReviewComment)
        self.review_comment.id = 1
        self.review_comment.solution_outline_id = 1
        self.review_comment.content = "Test comment"
        self.review_comment.status = ReviewCommentStatus.pending
    
    @pytest.mark.asyncio
    async def test_create_review(self):
        """Test creating a review."""
        # Arrange
        self.solution_outline_repository.get_or_404.return_value = self.solution_outline
        self.review_comment_repository.create.return_value = self.review_comment
        
        # Mock the generate_stream method to return SSE-formatted chunks
        self.ollama_client.generate_stream = AsyncMock()
        self.ollama_client.generate_stream.return_value.__aiter__.return_value = [
            'event: llm.chunk\ndata: {"content": "This is a test comment.\\n\\n", "prompt_key": "review_generation"}\n\n',
            'event: llm.chunk\ndata: {"content": "1. First issue: Something is wrong.\\n\\n", "prompt_key": "review_generation"}\n\n',
            'event: llm.chunk\ndata: {"content": "2. Second issue: Something else is wrong.", "prompt_key": "review_generation"}\n\n',
            'event: llm.complete\ndata: {"content": "", "prompt_key": "review_generation", "done": true}\n\n'
        ]
        
        # Act
        comments = []
        async for comment in self.service.create_review(1):
            comments.append(comment)
        
        # Assert
        self.solution_outline_repository.get_or_404.assert_called_once_with(self.db, 1)
        assert len(comments) > 0
        assert self.review_comment_repository.create.call_count > 0
    
    @pytest.mark.asyncio
    async def test_create_review_with_sse(self):
        """Test creating a review with SSE."""
        # Arrange
        self.solution_outline_repository.get_or_404.return_value = self.solution_outline
        self.review_comment_repository.create.return_value = self.review_comment
        
        # Mock the generate_stream method to return SSE-formatted chunks
        self.ollama_client.generate_stream = AsyncMock()
        self.ollama_client.generate_stream.return_value.__aiter__.return_value = [
            'event: llm.chunk\ndata: {"content": "This is a test comment.\\n\\n", "prompt_key": "review_generation"}\n\n',
            'event: llm.chunk\ndata: {"content": "1. First issue: Something is wrong.\\n\\n", "prompt_key": "review_generation"}\n\n',
            'event: llm.chunk\ndata: {"content": "2. Second issue: Something else is wrong.", "prompt_key": "review_generation"}\n\n',
            'event: llm.complete\ndata: {"content": "", "prompt_key": "review_generation", "done": true}\n\n'
        ]
        
        # Act
        comments = []
        async for comment in self.service.create_review(1, "test-client"):
            comments.append(comment)
        
        # Assert
        self.solution_outline_repository.get_or_404.assert_called_once_with(self.db, 1)
        assert len(comments) > 0
        assert self.review_comment_repository.create.call_count > 0
        assert self.sse_manager.send_event.call_count > 0
    
    @pytest.mark.asyncio
    async def test_create_review_solution_outline_not_found(self):
        """Test creating a review when the solution outline is not found."""
        # Arrange
        self.solution_outline_repository.get_or_404.side_effect = NotFoundException("Solution outline not found")
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            async for _ in self.service.create_review(1):
                pass
    
    @pytest.mark.asyncio
    async def test_create_review_llm_error(self):
        """Test creating a review when there's an error with the LLM."""
        # Arrange
        self.solution_outline_repository.get_or_404.return_value = self.solution_outline
        
        # Mock the generate_stream method to raise an exception
        self.ollama_client.generate_stream = AsyncMock()
        self.ollama_client.generate_stream.side_effect = LLMException("LLM error")
        
        # Act & Assert
        with pytest.raises(LLMException):
            async for _ in self.service.create_review(1, "test-client"):
                pass
        
        # Verify that an error event was sent
        self.sse_manager.send_event.assert_called_with(
            "test-client",
            "review.error",
            {
                "message": "LLM error",
                "solution_outline_id": 1,
                "error_type": "llm_error"
            }
        )
    
    def test_get_review_comments(self):
        """Test getting review comments."""
        # Arrange
        self.review_comment_repository.get_by_solution_outline.return_value = [self.review_comment]
        
        # Act
        result = self.service.get_review_comments(1)
        
        # Assert
        self.review_comment_repository.get_by_solution_outline.assert_called_once_with(
            self.db, solution_outline_id=1, skip=0, limit=100
        )
        assert result == [self.review_comment]
    
    def test_get_review_comments_by_status(self):
        """Test getting review comments by status."""
        # Arrange
        self.review_comment_repository.get_by_status.return_value = [self.review_comment]
        
        # Act
        result = self.service.get_review_comments_by_status(1, ReviewCommentStatus.pending)
        
        # Assert
        self.review_comment_repository.get_by_status.assert_called_once_with(
            self.db, solution_outline_id=1, status=ReviewCommentStatus.pending, skip=0, limit=100
        )
        assert result == [self.review_comment]
    
    def test_update_comment_status(self):
        """Test updating a comment status."""
        # Arrange
        self.review_comment_repository.get_or_404.return_value = self.review_comment
        self.review_comment_repository.update_status.return_value = self.review_comment
        
        # Act
        result = self.service.update_comment_status(1, ReviewCommentStatus.fixed)
        
        # Assert
        self.review_comment_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.review_comment_repository.update_status.assert_called_once_with(
            self.db, id=1, status=ReviewCommentStatus.fixed
        )
        assert result == self.review_comment
    
    def test_bulk_update_comment_status(self):
        """Test bulk updating comment statuses."""
        # Arrange
        self.review_comment_repository.bulk_update_status.return_value = [self.review_comment]
        
        # Act
        result = self.service.bulk_update_comment_status([1], ReviewCommentStatus.fixed)
        
        # Assert
        self.review_comment_repository.bulk_update_status.assert_called_once_with(
            self.db, ids=[1], status=ReviewCommentStatus.fixed
        )
        assert result == [self.review_comment]
    
    def test_get_status_counts(self):
        """Test getting status counts."""
        # Arrange
        expected_counts = {
            ReviewCommentStatus.pending: 1,
            ReviewCommentStatus.fixed: 2,
            ReviewCommentStatus.rejected: 0
        }
        self.review_comment_repository.get_status_counts.return_value = expected_counts
        
        # Act
        result = self.service.get_status_counts(1)
        
        # Assert
        self.review_comment_repository.get_status_counts.assert_called_once_with(self.db, solution_outline_id=1)
        assert result == expected_counts
    
    def test_process_review_chunk(self):
        """Test processing a review chunk."""
        # Arrange
        text = "This is a test comment.\n\n1. First issue: Something is wrong.\n\n2. Second issue: Something else is wrong."
        
        # Act
        remaining_text, comments = self.service._process_review_chunk(text)
        
        # Assert
        assert len(comments) > 0
        assert "This is a test comment." in comments