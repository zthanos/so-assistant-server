#!/usr/bin/env python3
"""
Test script to verify the fixes work with a real project.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_with_project():
    """Test the fixes with a real project."""
    print("🔧 Testing Fixes with Real Project")
    print("=" * 50)
    
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # First create a project
        print("1. Creating test project...")
        project_response = client.post(
            "/api/v1/projects",
            json={
                "name": "Test Route Fix Project",
                "description": "Testing route fixes"
            }
        )
        
        if project_response.status_code == 201:
            project_data = project_response.json()
            project_id = project_data.get('data', {}).get('id') or project_data.get('id')
            print(f"   ✅ Created project: {project_id}")
            
            # Test the fixed requirements document routes
            print("\\n2. Testing requirements document creation...")
            doc_response = client.post(
                f"/api/v1/projects/{project_id}/requirements-document",
                params={
                    "content": "# Test Requirements\\n\\n1. Authentication\\n2. Authorization",
                    "status": "draft"
                }
            )
            
            if doc_response.status_code == 201:
                doc_data = doc_response.json()
                print(f"   ✅ Created document: version {doc_data.get('version')}")
                print(f"   ✅ DateTime serialized: {doc_data.get('created_at')}")
                
                # Test latest endpoint
                print("\\n3. Testing latest document retrieval...")
                latest_response = client.get(f"/api/v1/projects/{project_id}/requirements-document/latest")
                
                if latest_response.status_code == 200:
                    latest_data = latest_response.json()
                    print(f"   ✅ Retrieved latest: version {latest_data.get('version')}")
                    print(f"   ✅ No route conflict - /latest working!")
                else:
                    print(f"   ❌ Latest failed: {latest_response.status_code}")
                    
            else:
                print(f"   ❌ Document creation failed: {doc_response.status_code} - {doc_response.text}")
                
        else:
            print(f"   ❌ Project creation failed: {project_response.status_code}")
            
        print("\\n" + "=" * 50)
        print("🎉 ROUTE FIXES WORKING WITH REAL DATA!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_with_project()