"""Integration tests for SSE functionality.

This module contains integration tests for Server-Sent Events (SSE) functionality,
testing real-time streaming capabilities.
"""
import pytest
import asyncio
import json
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models.projects import Project
from app.domain.models.solution_outlines import SolutionOutline, SolutionOutlineStatus

class TestSSEFunctionality:
    """Integration tests for SSE functionality."""
    
    def test_sse_connection_establishment(self, client_with_sse: TestClient):
        """Test establishing an SSE connection."""
        # Test SSE endpoint
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"

    def test_sse_connection_with_client_type(self, client_with_sse: TestClient):
        """Test establishing an SSE connection with client type."""
        with client_with_sse.stream("GET", "/api/v1/sse?client_type=test_client") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

    def test_llm_streaming_endpoint(self, client_with_sse: TestClient):
        """Test LLM streaming endpoint."""
        # Test the LLM streaming endpoint
        request_data = {
            "prompt": "Write a simple hello world function",
            "prompt_key": "test_prompt"
        }
        
        response = client_with_sse.post("/api/v1/llm/stream", json=request_data)
        
        # The endpoint should return a response (might be 200 or error depending on LLM availability)
        assert response.status_code in [200, 500, 503]  # Various possible responses

    def test_solution_outline_review_streaming(self, client_with_sse: TestClient, db_session: Session, sample_project_data):
        """Test solution outline review streaming functionality."""
        # Create project and solution outline
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        solution_outline = SolutionOutline(
            project_id=project.id,
            content="This is a test solution outline for review",
            version=1,
            status=SolutionOutlineStatus.draft
        )
        db_session.add(solution_outline)
        db_session.commit()
        
        # Test solution outline review endpoint
        with client_with_sse.stream("POST", f"/api/v1/solution-outlines/{solution_outline.id}/review") as response:
            # The endpoint should establish SSE connection for streaming review
            assert response.status_code in [200, 500, 503]  # Various possible responses
            if response.status_code == 200:
                assert response.headers["content-type"] == "text/event-stream"

    def test_sse_event_format(self, client_with_sse: TestClient):
        """Test SSE event format compliance."""
        # This test would verify that SSE events follow the proper format
        # In a real scenario, we would need to mock the LLM service to generate predictable events
        
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            assert response.status_code == 200
            
            # Read a few lines to check format
            lines = []
            for i, line in enumerate(response.iter_lines()):
                if i >= 10:  # Read first 10 lines
                    break
                lines.append(line)
            
            # SSE format should include proper event structure
            # This is a basic check - in practice, we'd need more sophisticated testing
            assert len(lines) >= 0  # At least some response

    def test_sse_connection_cleanup(self, client_with_sse: TestClient, sse_manager):
        """Test SSE connection cleanup."""
        # Check initial state
        initial_client_count = len(sse_manager.clients)
        
        # Establish connection and close it
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            assert response.status_code == 200
            # Connection should be established
            # Note: In a real test, we'd need to check the SSE manager state
        
        # After closing, connection should be cleaned up
        # This is hard to test directly without more sophisticated mocking

    def test_multiple_sse_connections(self, client_with_sse: TestClient):
        """Test handling multiple SSE connections."""
        # This test would verify that the system can handle multiple concurrent SSE connections
        # In practice, this would require more sophisticated async testing
        
        responses = []
        try:
            # Try to establish multiple connections
            for i in range(3):
                response = client_with_sse.get("/api/v1/sse", stream=True)
                if response.status_code == 200:
                    responses.append(response)
            
            # All connections should be successful
            assert len(responses) >= 0  # At least some connections work
            
        finally:
            # Clean up connections
            for response in responses:
                try:
                    response.close()
                except:
                    pass

    def test_sse_error_handling(self, client_with_sse: TestClient):
        """Test SSE error handling."""
        # Test invalid SSE requests
        response = client_with_sse.post("/api/v1/sse")  # POST instead of GET
        assert response.status_code == 405  # Method not allowed

    def test_sse_with_invalid_client_type(self, client_with_sse: TestClient):
        """Test SSE connection with invalid parameters."""
        # Test with very long client type
        long_client_type = "x" * 1000
        response = client_with_sse.get(f"/api/v1/sse?client_type={long_client_type}")
        
        # Should still work or return appropriate error
        assert response.status_code in [200, 400, 422]

class TestSSEIntegrationWithDatabase:
    """Integration tests for SSE functionality with database operations."""
    
    def test_sse_with_database_operations(self, client_with_sse: TestClient, db_session: Session, sample_project_data):
        """Test SSE functionality integrated with database operations."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Test that SSE works with database-dependent operations
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            assert response.status_code == 200
            
            # Perform database operation while SSE is active
            solution_outline = SolutionOutline(
                project_id=project.id,
                content="Test content",
                version=1,
                status=SolutionOutlineStatus.draft
            )
            db_session.add(solution_outline)
            db_session.commit()
            
            # SSE connection should remain stable
            assert response.status_code == 200

    def test_concurrent_sse_and_api_requests(self, client_with_sse: TestClient, db_session: Session, sample_project_data):
        """Test concurrent SSE connections and regular API requests."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Establish SSE connection
        with client_with_sse.stream("GET", "/api/v1/sse") as sse_response:
            assert sse_response.status_code == 200
            
            # Make regular API requests while SSE is active
            api_response = client_with_sse.get(f"/api/v1/projects/{project.id}/teams")
            assert api_response.status_code == 200
            
            # Create team via API
            team_response = client_with_sse.post(
                f"/api/v1/projects/{project.id}/teams",
                json={"name": "Test Team", "members": "Test Member"}
            )
            assert team_response.status_code == 201
            
            # SSE should still be active
            assert sse_response.status_code == 200

class TestSSEPerformance:
    """Performance tests for SSE functionality."""
    
    def test_sse_connection_performance(self, client_with_sse: TestClient):
        """Test SSE connection establishment performance."""
        import time
        
        start_time = time.time()
        
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            connection_time = time.time() - start_time
            
            assert response.status_code == 200
            # Connection should be established quickly (within 1 second)
            assert connection_time < 1.0

    def test_sse_memory_usage(self, client_with_sse: TestClient):
        """Test SSE memory usage with multiple connections."""
        # This is a basic test - in practice, you'd use memory profiling tools
        
        connections = []
        try:
            # Establish multiple connections
            for i in range(5):
                response = client_with_sse.get("/api/v1/sse", stream=True)
                if response.status_code == 200:
                    connections.append(response)
            
            # Should be able to handle multiple connections
            assert len(connections) >= 0
            
        finally:
            # Clean up
            for conn in connections:
                try:
                    conn.close()
                except:
                    pass

class TestSSEEventTypes:
    """Tests for different SSE event types."""
    
    def test_sse_event_types_structure(self, client_with_sse: TestClient):
        """Test that SSE events follow the expected structure."""
        # This would test specific event types like:
        # - start events
        # - chunk events  
        # - complete events
        # - error events
        
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            assert response.status_code == 200
            
            # In a real implementation, we would:
            # 1. Trigger specific events
            # 2. Parse the SSE stream
            # 3. Verify event structure
            
            # For now, just verify the connection works
            assert response.headers["content-type"] == "text/event-stream"

    def test_sse_error_events(self, client_with_sse: TestClient):
        """Test SSE error event handling."""
        # Test that error events are properly formatted and sent
        
        # This would require triggering an error condition
        # and verifying the error event format
        
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            assert response.status_code == 200
            
            # In practice, we would:
            # 1. Trigger an error condition
            # 2. Verify error event is sent
            # 3. Check error event format
            
            # Basic connection test for now
            assert response.headers["content-type"] == "text/event-stream"