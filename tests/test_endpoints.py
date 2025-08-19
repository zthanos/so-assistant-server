import requests
import json

base_url = "http://127.0.0.1:8000/api/v1"

def test_projects_endpoint():
    try:
        response = requests.get(f"{base_url}/projects/")
        print(f"Projects endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error connecting to server: {e}")

def test_create_project():
    try:
        project_data = {
            "id": "test-project-1",
            "name": "Test Project",
            "description": "A test project",
            "code": "TP001",
            "state": "active"
        }
        response = requests.post(f"{base_url}/projects/", json=project_data)
        print(f"Create project status: {response.status_code}")
        if response.status_code == 201:
            print(f"Created project: {response.json()}")
            return response.json()
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error creating project: {e}")

def test_project_outline(project_id):
    try:
        response = requests.get(f"{base_url}/projects/{project_id}/outline")
        print(f"Project outline status: {response.status_code}")
        if response.status_code == 200:
            print(f"Project outline: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error getting project outline: {e}")

if __name__ == "__main__":
    print("Testing new REST API endpoints...")
    test_projects_endpoint()
    project = test_create_project()
    if project:
        test_project_outline(project["id"])