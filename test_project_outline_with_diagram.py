#!/usr/bin/env python3
"""Test the project outline endpoint with a diagram."""

from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_project_outline_with_diagram():
    """Test the project outline endpoint with a diagram."""
    print("Testing Project Outline endpoint with diagram...")
    
    # First create a project
    project_data = {
        "id": str(uuid.uuid4()),
        "name": "Test Project with Diagram",
        "description": "A test project with a diagram"
    }
    
    response = client.post("/api/v1/projects", json=project_data)
    print(f"Create project: {response.status_code}")
    
    if response.status_code == 201:
        project_id = response.json()["id"]
        print(f"Created project: {project_id}")
        
        # Add a diagram
        diagram_data = {
            "title": "System Architecture",
            "mermaid_code": "graph TD\n    A[Client] --> B[Server]",
            "type": "architecture"
        }
        response = client.post(f"/api/v1/projects/{project_id}/diagrams", json=diagram_data)
        print(f"Create diagram: {response.status_code}")
        
        # Now test the outline endpoint
        response = client.get(f"/api/v1/projects/{project_id}/outline")
        print(f"Get project outline: {response.status_code}")
        
        if response.status_code == 200:
            outline = response.json()
            print("✅ Project outline endpoint working with diagram!")
            
            # Check if related entities are included
            print(f"Requirements: {len(outline['requirements'])} items")
            print(f"Diagrams: {len(outline['diagrams'])} items")
            if outline['diagrams']:
                print(f"  - First diagram: {outline['diagrams'][0]['title']}")
            print(f"Teams: {len(outline['teams'])} items")
            print(f"Tasks: {len(outline['tasks'])} items")
                
        else:
            print(f"❌ Project outline failed: {response.text}")
            
    else:
        print(f"❌ Failed to create project: {response.text}")

if __name__ == "__main__":
    test_project_outline_with_diagram()