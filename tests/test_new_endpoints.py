#!/usr/bin/env python3
"""Test script for the new REST API endpoints."""

import requests
import json
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_projects_api():
    """Test Projects API endpoints."""
    print("Testing Projects API...")
    
    # Create a project
    project_data = {
        "id": str(uuid.uuid4()),
        "name": "Test Project",
        "description": "A test project for API validation",
        "code": "TEST001"
    }
    
    try:
        # Test create project
        response = requests.post(f"{BASE_URL}/projects/", json=project_data)
        print(f"Create Project: {response.status_code}")
        if response.status_code == 201:
            project = response.json()
            project_id = project["id"]
            print(f"Created project: {project_id}")
            
            # Test get project
            response = requests.get(f"{BASE_URL}/projects/{project_id}")
            print(f"Get Project: {response.status_code}")
            
            # Test list projects
            response = requests.get(f"{BASE_URL}/projects/")
            print(f"List Projects: {response.status_code}")
            
            # Test project outline
            response = requests.get(f"{BASE_URL}/projects/{project_id}/outline")
            print(f"Get Project Outline: {response.status_code}")
            
            # Test update project
            update_data = {"name": "Updated Test Project"}
            response = requests.put(f"{BASE_URL}/projects/{project_id}", json=update_data)
            print(f"Update Project: {response.status_code}")
            
            # Test delete project
            response = requests.delete(f"{BASE_URL}/projects/{project_id}")
            print(f"Delete Project: {response.status_code}")
            
        else:
            print(f"Failed to create project: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Server not running. Please start the server first.")
    except Exception as e:
        print(f"Error testing projects API: {e}")

def test_requirements_api():
    """Test Requirements API endpoints."""
    print("\nTesting Requirements API...")
    
    # First create a project
    project_data = {
        "id": str(uuid.uuid4()),
        "name": "Test Project for Requirements",
        "description": "A test project for requirements API validation"
    }
    
    try:
        # Create project first
        response = requests.post(f"{BASE_URL}/projects/", json=project_data)
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # Create a requirement
            requirement_data = {
                "description": "The system shall provide user authentication",
                "category": "functional"
            }
            
            response = requests.post(f"{BASE_URL}/projects/{project_id}/requirements", json=requirement_data)
            print(f"Create Requirement: {response.status_code}")
            
            if response.status_code == 201:
                requirement = response.json()
                requirement_id = requirement["id"]
                
                # Test get requirement
                response = requests.get(f"{BASE_URL}/projects/{project_id}/requirements/{requirement_id}")
                print(f"Get Requirement: {response.status_code}")
                
                # Test list requirements
                response = requests.get(f"{BASE_URL}/projects/{project_id}/requirements")
                print(f"List Requirements: {response.status_code}")
                
                # Test update requirement
                update_data = {"description": "Updated requirement description"}
                response = requests.put(f"{BASE_URL}/projects/{project_id}/requirements/{requirement_id}", json=update_data)
                print(f"Update Requirement: {response.status_code}")
                
                # Test delete requirement
                response = requests.delete(f"{BASE_URL}/projects/{project_id}/requirements/{requirement_id}")
                print(f"Delete Requirement: {response.status_code}")
            
            # Clean up project
            requests.delete(f"{BASE_URL}/projects/{project_id}")
            
    except requests.exceptions.ConnectionError:
        print("Server not running. Please start the server first.")
    except Exception as e:
        print(f"Error testing requirements API: {e}")

def test_diagrams_api():
    """Test Diagrams API endpoints."""
    print("\nTesting Diagrams API...")
    
    # First create a project
    project_data = {
        "id": str(uuid.uuid4()),
        "name": "Test Project for Diagrams",
        "description": "A test project for diagrams API validation"
    }
    
    try:
        # Create project first
        response = requests.post(f"{BASE_URL}/projects/", json=project_data)
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # Create a diagram
            diagram_data = {
                "title": "System Architecture",
                "mermaid_code": "graph TD\n    A[Client] --> B[Server]\n    B --> C[Database]",
                "type": "architecture"
            }
            
            response = requests.post(f"{BASE_URL}/projects/{project_id}/diagrams", json=diagram_data)
            print(f"Create Diagram: {response.status_code}")
            
            if response.status_code == 201:
                diagram = response.json()
                diagram_id = diagram["id"]
                
                # Test get diagram
                response = requests.get(f"{BASE_URL}/projects/{project_id}/diagrams/{diagram_id}")
                print(f"Get Diagram: {response.status_code}")
                
                # Test list diagrams
                response = requests.get(f"{BASE_URL}/projects/{project_id}/diagrams")
                print(f"List Diagrams: {response.status_code}")
                
                # Test update diagram
                update_data = {"title": "Updated System Architecture"}
                response = requests.put(f"{BASE_URL}/projects/{project_id}/diagrams/{diagram_id}", json=update_data)
                print(f"Update Diagram: {response.status_code}")
                
                # Test delete diagram
                response = requests.delete(f"{BASE_URL}/projects/{project_id}/diagrams/{diagram_id}")
                print(f"Delete Diagram: {response.status_code}")
            
            # Clean up project
            requests.delete(f"{BASE_URL}/projects/{project_id}")
            
    except requests.exceptions.ConnectionError:
        print("Server not running. Please start the server first.")
    except Exception as e:
        print(f"Error testing diagrams API: {e}")

if __name__ == "__main__":
    print("Testing new REST API endpoints...")
    print("Make sure the server is running on http://localhost:8000")
    print("=" * 50)
    
    test_projects_api()
    test_requirements_api()
    test_diagrams_api()
    
    print("\n" + "=" * 50)
    print("Testing complete!")