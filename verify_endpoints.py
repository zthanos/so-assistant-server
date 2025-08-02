#!/usr/bin/env python3
"""Verify that all endpoints are accessible at the correct paths."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_endpoint_paths():
    """Test that all endpoints are accessible at the correct paths."""
    print("Verifying endpoint paths...")
    
    endpoints_to_test = [
        # Projects endpoints
        ("GET", "/api/v1/projects", "List projects"),
        ("POST", "/api/v1/projects", "Create project"),
        
        # Requirements endpoints (need a project first)
        ("GET", "/api/v1/projects/test-id/requirements", "List requirements"),
        ("POST", "/api/v1/projects/test-id/requirements", "Create requirement"),
        
        # Diagrams endpoints (need a project first)
        ("GET", "/api/v1/projects/test-id/diagrams", "List diagrams"),
        ("POST", "/api/v1/projects/test-id/diagrams", "Create diagram"),
    ]
    
    for method, path, description in endpoints_to_test:
        try:
            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                # Use minimal test data
                if "requirements" in path:
                    response = client.post(path, json={"description": "test", "category": "Functional"})
                elif "diagrams" in path:
                    response = client.post(path, json={"title": "test", "mermaid_code": "test", "type": "test"})
                elif "projects" in path:
                    response = client.post(path, json={"id": "test-id", "name": "test"})
                else:
                    response = client.post(path, json={})
            
            # We expect either success or 4xx errors (not 404 for wrong path)
            if response.status_code == 404:
                print(f"❌ {description}: {method} {path} -> 404 (Path not found)")
            else:
                print(f"✅ {description}: {method} {path} -> {response.status_code} (Path exists)")
                
        except Exception as e:
            print(f"❌ {description}: {method} {path} -> Error: {e}")

if __name__ == "__main__":
    test_endpoint_paths()