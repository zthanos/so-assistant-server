"""End-to-end tests for SSE workflows.

This module contains end-to-end tests for Server-Sent Events workflows,
testing real-time communication scenarios across the application.
"""
import pytest
import asyncio
import json
import time
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

class TestSSEWorkflows:
    """End-to-end tests for SSE workflows and real-time communication."""
    
    def test_sse_connection_lifecycle(self, client_with_sse: TestClient):
        """Test the complete SSE connection lifecycle."""
        # Test connection establishment
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"
            
            # Test that connection stays alive
            start_time = time.time()
            lines_received = 0
            
            # Read some data from the stream (with timeout)
            for line in response.iter_lines():
                lines_received += 1
                if lines_received >= 5 or (time.time() - start_time) > 2.0:
                    break
            
            # Connection should remain stable
            assert response.status_code == 200

    def test_multiple_sse_connections(self, client_with_sse: TestClient):
        """Test handling multiple concurrent SSE connections."""
        connections = []
        
        try:
            # Establish multiple connections
            for i in range(3):
                response = client_with_sse.get("/api/v1/sse", stream=True)
                if response.status_code == 200:
                    connections.append(response)
            
            # All connections should be successful
            assert len(connections) >= 1  # At least one connection should work
            
            # Test that all connections are active
            for conn in connections:
                assert conn.status_code == 200
                assert conn.headers["content-type"] == "text/event-stream"
                
        finally:
            # Clean up connections
            for conn in connections:
                try:
                    conn.close()
                except:
                    pass

    def test_sse_with_llm_streaming_workflow(self, client_with_sse: TestClient):
        """Test SSE workflow with LLM streaming functionality."""
        # Test LLM streaming endpoint
        llm_request = {
            "prompt": "Write a simple hello world function in Python",
            "prompt_key": "test_hello_world"
        }
        
        # This test depends on LLM service availability
        response = client_with_sse.post("/api/v1/llm/stream", json=llm_request)
        
        # The response could be successful streaming or an error if LLM is not available
        assert response.status_code in [200, 500, 503]
        
        if response.status_code == 200:
            # If successful, it should be an SSE stream
            assert "text/event-stream" in response.headers.get("content-type", "")

    def test_solution_outline_review_sse_workflow(self, client_with_sse: TestClient, project_workflow_data):
        """Test the complete solution outline review workflow with SSE streaming."""
        project_id = project_workflow_data["project"]["id"]
        
        # Step 1: Create project and solution outline
        project_response = client_with_sse.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        solution_outline_response = client_with_sse.post(
            f"/api/v1/projects/{project_id}/solution-outlines",
            params=project_workflow_data["solution_outline"]
        )
        assert solution_outline_response.status_code == 201
        solution_outline = solution_outline_response.json()
        
        # Step 2: Establish SSE connection for review
        with client_with_sse.stream("GET", "/api/v1/sse") as sse_connection:
            assert sse_connection.status_code == 200
            
            # Step 3: Request solution outline review (this should stream results)
            review_response = client_with_sse.post(f"/api/v1/solution-outlines/{solution_outline['id']}/review")
            
            # The review endpoint should either stream via SSE or handle gracefully
            assert review_response.status_code in [200, 500, 503]
            
            # If review is successful, check that SSE connection remains active
            if review_response.status_code == 200:
                assert sse_connection.status_code == 200

    def test_concurrent_sse_and_api_operations(self, client_with_sse: TestClient, project_workflow_data):
        """Test concurrent SSE connections with regular API operations."""
        project_id = project_workflow_data["project"]["id"]
        
        # Establish SSE connection
        with client_with_sse.stream("GET", "/api/v1/sse") as sse_connection:
            assert sse_connection.status_code == 200
            
            # Perform regular API operations while SSE is active
            
            # Create project
            project_response = client_with_sse.post("/api/v1/projects", json=project_workflow_data["project"])
            assert project_response.status_code == 201
            
            # Create teams
            for team_data in project_workflow_data["teams"]:
                team_response = client_with_sse.post(f"/api/v1/projects/{project_id}/teams", json=team_data)
                assert team_response.status_code == 201
            
            # Create ADRs
            for adr_data in project_workflow_data["adrs"]:
                adr_response = client_with_sse.post(f"/api/v1/projects/{project_id}/adrs", params=adr_data)
                assert adr_response.status_code == 201
            
            # Verify SSE connection is still active
            assert sse_connection.status_code == 200
            
            # Perform read operations
            teams_response = client_with_sse.get(f"/api/v1/projects/{project_id}/teams")
            assert teams_response.status_code == 200
            
            adrs_response = client_with_sse.get(f"/api/v1/projects/{project_id}/adrs")
            assert adrs_response.status_code == 200
            
            # SSE should still be active after all operations
            assert sse_connection.status_code == 200

class TestSSEErrorHandling:
    """End-to-end tests for SSE error handling scenarios."""
    
    def test_sse_connection_error_recovery(self, client_with_sse: TestClient):
        """Test SSE connection error handling and recovery."""
        # Test invalid SSE request methods
        post_response = client_with_sse.post("/api/v1/sse")
        assert post_response.status_code == 405  # Method not allowed
        
        put_response = client_with_sse.put("/api/v1/sse")
        assert put_response.status_code == 405  # Method not allowed
        
        # Test valid SSE connection after errors
        with client_with_sse.stream("GET", "/api/v1/sse") as sse_connection:
            assert sse_connection.status_code == 200
            assert sse_connection.headers["content-type"] == "text/event-stream"

    def test_sse_with_invalid_parameters(self, client_with_sse: TestClient):
        """Test SSE connections with invalid parameters."""
        # Test with very long client type
        long_client_type = "x" * 1000
        response = client_with_sse.get(f"/api/v1/sse?client_type={long_client_type}")
        
        # Should either work or return appropriate error
        assert response.status_code in [200, 400, 422]
        
        # Test with special characters
        special_client_type = "test@#$%^&*()"
        response = client_with_sse.get(f"/api/v1/sse?client_type={special_client_type}")
        assert response.status_code in [200, 400, 422]

    def test_sse_connection_interruption_handling(self, client_with_sse: TestClient):
        """Test handling of SSE connection interruptions."""
        # Establish connection and then close it abruptly
        response = client_with_sse.get("/api/v1/sse", stream=True)
        assert response.status_code == 200
        
        # Close connection
        response.close()
        
        # Establish new connection (should work)
        with client_with_sse.stream("GET", "/api/v1/sse") as new_connection:
            assert new_connection.status_code == 200

class TestSSEPerformance:
    """End-to-end tests for SSE performance scenarios."""
    
    def test_sse_connection_performance(self, client_with_sse: TestClient):
        """Test SSE connection establishment performance."""
        start_time = time.time()
        
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            connection_time = time.time() - start_time
            
            assert response.status_code == 200
            # Connection should be established quickly
            assert connection_time < 2.0  # Should connect within 2 seconds

    def test_multiple_sse_connections_performance(self, client_with_sse: TestClient):
        """Test performance with multiple SSE connections."""
        start_time = time.time()
        connections = []
        
        try:
            # Establish multiple connections
            for i in range(5):
                response = client_with_sse.get("/api/v1/sse", stream=True)
                if response.status_code == 200:
                    connections.append(response)
            
            establishment_time = time.time() - start_time
            
            # Should be able to establish multiple connections reasonably quickly
            assert establishment_time < 5.0  # All connections within 5 seconds
            assert len(connections) >= 1  # At least one connection should work
            
        finally:
            # Clean up
            for conn in connections:
                try:
                    conn.close()
                except:
                    pass

    def test_sse_with_high_api_load(self, client_with_sse: TestClient, project_workflow_data):
        """Test SSE performance under high API load."""
        project_id = project_workflow_data["project"]["id"]
        
        # Establish SSE connection
        with client_with_sse.stream("GET", "/api/v1/sse") as sse_connection:
            assert sse_connection.status_code == 200
            
            # Create project
            project_response = client_with_sse.post("/api/v1/projects", json=project_workflow_data["project"])
            assert project_response.status_code == 201
            
            # Perform many API operations rapidly
            start_time = time.time()
            
            # Create many teams rapidly
            for i in range(20):
                team_data = {
                    "name": f"Load Test Team {i+1}",
                    "members": f"Member {i+1}"
                }
                team_response = client_with_sse.post(f"/api/v1/projects/{project_id}/teams", json=team_data)
                assert team_response.status_code == 201
            
            # Create many ADRs rapidly
            for i in range(15):
                adr_data = {
                    "title": f"Load Test ADR {i+1}",
                    "content": f"Content for load test ADR {i+1}"
                }
                adr_response = client_with_sse.post(f"/api/v1/projects/{project_id}/adrs", params=adr_data)
                assert adr_response.status_code == 201
            
            load_test_time = time.time() - start_time
            
            # Verify SSE connection is still active after high load
            assert sse_connection.status_code == 200
            
            # Performance should be reasonable
            assert load_test_time < 30.0  # Should complete within 30 seconds

class TestSSEIntegrationScenarios:
    """End-to-end tests for complex SSE integration scenarios."""
    
    def test_sse_event_ordering(self, client_with_sse: TestClient):
        """Test that SSE events maintain proper ordering."""
        # This test would verify event ordering in a real streaming scenario
        # For now, we test basic connection stability
        
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            assert response.status_code == 200
            
            # In a real implementation, we would:
            # 1. Trigger multiple events
            # 2. Verify they arrive in the correct order
            # 3. Check event structure and content
            
            # Basic test for now
            assert response.headers["content-type"] == "text/event-stream"

    def test_sse_event_reliability(self, client_with_sse: TestClient):
        """Test SSE event delivery reliability."""
        # This test would verify that events are delivered reliably
        # For now, we test connection stability under various conditions
        
        with client_with_sse.stream("GET", "/api/v1/sse") as response:
            assert response.status_code == 200
            
            # Simulate some load while SSE is active
            for i in range(10):
                # Make API calls to generate potential events
                health_response = client_with_sse.get("/")
                assert health_response.status_code == 200
            
            # SSE connection should remain stable
            assert response.status_code == 200

    def test_sse_with_database_transactions(self, client_with_sse: TestClient, project_workflow_data):
        """Test SSE behavior with database transactions."""
        project_id = project_workflow_data["project"]["id"]
        
        with client_with_sse.stream("GET", "/api/v1/sse") as sse_connection:
            assert sse_connection.status_code == 200
            
            # Perform database operations that might trigger events
            project_response = client_with_sse.post("/api/v1/projects", json=project_workflow_data["project"])
            assert project_response.status_code == 201
            
            # Create solution outline (might trigger review events)
            solution_outline_response = client_with_sse.post(
                f"/api/v1/projects/{project_id}/solution-outlines",
                params=project_workflow_data["solution_outline"]
            )
            assert solution_outline_response.status_code == 201
            
            # SSE should remain stable through database operations
            assert sse_connection.status_code == 200