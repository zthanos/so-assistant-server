#!/usr/bin/env python3
"""Test the project outline endpoint specifically."""

from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_project_outline():
    """Test the project outline endpoint."""
    print("Testing Project Outline endpoint...")
    
    # First create a project
    project_data = {
        "id": str(uuid.uuid4()),
        "name": "Test Project for Outline",
        "description": "A test project for outline testing"
    }
    
    response = client.post("/api/v1/projects", json=project_data)
    print(f"Create project: {response.status_code}")
    
    if response.status_code == 201:
        project_id = response.json()["id"]
        print(f"Created project: {project_id}")
        
        # Test the outline endpoint
        response = client.get(f"/api/v1/projects/{project_id}/outline")
        print(f"Get project outline: {response.status_code}")
        
        if response.status_code == 200:
            outline = response.json()
            print("✅ Project outline endpoint working!")
            print(f"Project outline keys: {list(outline.keys())}")
            
            # Check if related entities are included
            if 'requirements' in outline:
                print(f"Requirements: {len(outline['requirements'])} items")
            if 'diagrams' in outline:
                print(f"Diagrams: {len(outline['diagrams'])} items")
            if 'teams' in outline:
                print(f"Teams: {len(outline['teams'])} items")
            if 'tasks' in outline:
                print(f"Tasks: {len(outline['tasks'])} items")
                
        else:
            print(f"❌ Project outline failed: {response.text}")
            
    else:
        print(f"❌ Failed to create project: {response.text}")

if __name__ == "__main__":
    test_project_outline()