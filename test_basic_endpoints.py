#!/usr/bin/env python3
"""Basic test for the new REST API endpoints focusing on core functionality."""

from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_projects_basic():
    """Test basic projects functionality."""
    print("Testing Projects API (basic functionality)...")
    
    # Test list projects
    response = client.get("/api/v1/projects/")
    print(f"✅ List projects: {response.status_code}")
    
    if response.status_code == 200:
        projects = response.json()
        print(f"Found {len(projects)} existing projects")
        
        # Test creating a project
        project_data = {
            "id": str(uuid.uuid4()),
            "name": "Test Project Basic",
            "description": "A basic test project"
        }
        
        response = client.post("/api/v1/projects/", json=project_data)
        print(f"✅ Create project: {response.status_code}")
        
        if response.status_code == 201:
            project = response.json()
            project_id = project["id"]
            print(f"Created project: {project_id}")
            
            # Test get project
            response = client.get(f"/api/v1/projects/{project_id}")
            print(f"✅ Get project: {response.status_code}")
            
            # Test update project
            update_data = {"name": "Updated Test Project Basic"}
            response = client.put(f"/api/v1/projects/{project_id}", json=update_data)
            print(f"✅ Update project: {response.status_code}")
            
            return project_id
        else:
            print(f"❌ Failed to create project: {response.text}")
            return None
    else:
        print(f"❌ Failed to list projects: {response.text}")
        return None

def test_requirements_basic(project_id):
    """Test basic requirements functionality."""
    if not project_id:
        print("❌ Skipping requirements test - no project available")
        return
        
    print("\nTesting Requirements API (basic functionality)...")
    
    # Test create requirement
    requirement_data = {
        "description": "The system shall provide user authentication",
        "category": "Functional"
    }
    
    response = client.post(f"/api/v1/projects/{project_id}/requirements", json=requirement_data)
    print(f"✅ Create requirement: {response.status_code}")
    
    if response.status_code == 201:
        requirement = response.json()
        requirement_id = requirement["id"]
        print(f"Created requirement: {requirement_id}")
        
        # Test list requirements
        response = client.get(f"/api/v1/projects/{project_id}/requirements")
        print(f"✅ List requirements: {response.status_code}")
        
        # Test get requirement
        response = client.get(f"/api/v1/projects/{project_id}/requirements/{requirement_id}")
        print(f"✅ Get requirement: {response.status_code}")
        
        return requirement_id
    else:
        print(f"❌ Failed to create requirement: {response.text}")
        return None

def test_diagrams_basic(project_id):
    """Test basic diagrams functionality."""
    if not project_id:
        print("❌ Skipping diagrams test - no project available")
        return
        
    print("\nTesting Diagrams API (basic functionality)...")
    
    # Test create diagram
    diagram_data = {
        "title": "Basic System Architecture",
        "mermaid_code": "graph TD\n    A[Client] --> B[Server]",
        "type": "architecture"
    }
    
    response = client.post(f"/api/v1/projects/{project_id}/diagrams", json=diagram_data)
    print(f"✅ Create diagram: {response.status_code}")
    
    if response.status_code == 201:
        diagram = response.json()
        diagram_id = diagram["id"]
        print(f"Created diagram: {diagram_id}")
        
        # Test list diagrams
        response = client.get(f"/api/v1/projects/{project_id}/diagrams")
        print(f"✅ List diagrams: {response.status_code}")
        
        # Test get diagram
        response = client.get(f"/api/v1/projects/{project_id}/diagrams/{diagram_id}")
        print(f"✅ Get diagram: {response.status_code}")
        
        return diagram_id
    else:
        print(f"❌ Failed to create diagram: {response.text}")
        return None

if __name__ == "__main__":
    print("Testing basic REST API functionality...")
    print("=" * 60)
    
    try:
        # Test projects first
        project_id = test_projects_basic()
        
        # Test requirements and diagrams if project creation succeeded
        requirement_id = test_requirements_basic(project_id)
        diagram_id = test_diagrams_basic(project_id)
        
        print("\n" + "=" * 60)
        print("✅ Basic endpoint tests completed!")
        
        if project_id:
            print(f"Test project created: {project_id}")
        if requirement_id:
            print(f"Test requirement created: {requirement_id}")
        if diagram_id:
            print(f"Test diagram created: {diagram_id}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()