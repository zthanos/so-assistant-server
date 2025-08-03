"""End-to-end tests for data consistency workflows.

This module contains end-to-end tests that verify data consistency
across different operations and components of the application.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

class TestDataConsistencyWorkflows:
    """End-to-end tests for data consistency across operations."""
    
    def test_project_deletion_cascade(self, client: TestClient, project_workflow_data, workflow_test_helpers):
        """Test that deleting a project properly cascades to related entities."""
        # Create complete project with all related entities
        results = workflow_test_helpers.create_complete_project(client, project_workflow_data)
        project_id = project_workflow_data["project"]["id"]
        
        # Verify all entities exist
        verification = workflow_test_helpers.verify_project_completeness(client, project_id)
        assert verification["project_exists"] is True
        assert verification["teams_count"] > 0
        assert verification["adrs_count"] > 0
        assert verification["solution_outline_exists"] is True
        
        # Delete the project
        delete_response = client.delete(f"/api/v1/projects/{project_id}")
        assert delete_response.status_code == 200
        
        # Verify project is deleted
        project_response = client.get(f"/api/v1/projects/{project_id}")
        assert project_response.status_code == 404
        
        # Verify related entities are also deleted (cascade)
        teams_response = client.get(f"/api/v1/projects/{project_id}/teams")
        assert teams_response.status_code == 404  # Project not found
        
        adrs_response = client.get(f"/api/v1/projects/{project_id}/adrs")
        assert adrs_response.status_code == 404  # Project not found
        
        solution_outline_response = client.get(f"/api/v1/projects/{project_id}/solution-outlines/latest")
        assert solution_outline_response.status_code == 404  # Project not found

    def test_solution_outline_versioning_consistency(self, client: TestClient, project_workflow_data):
        """Test that solution outline versioning maintains data consistency."""
        project_id = project_workflow_data["project"]["id"]
        
        # Create project
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        # Create initial solution outline (version 1)
        initial_content = "Initial solution outline content"
        initial_response = client.post(
            f"/api/v1/projects/{project_id}/solution-outlines",
            params={"content": initial_content, "status": "draft"}
        )
        assert initial_response.status_code == 201
        initial_outline = initial_response.json()
        assert initial_outline["version"] == 1
        assert initial_outline["content"] == initial_content
        
        # Update solution outline (should create version 2)
        updated_content = "Updated solution outline content"
        update_response = client.post(
            f"/api/v1/projects/{project_id}/solution-outlines",
            params={"content": updated_content, "status": "published"}
        )
        assert update_response.status_code == 200
        updated_outline = update_response.json()
        assert updated_outline["version"] == 2
        assert updated_outline["content"] == updated_content
        assert updated_outline["status"] == "published"
        
        # Verify both versions exist
        versions_response = client.get(f"/api/v1/projects/{project_id}/solution-outlines")
        assert versions_response.status_code == 200
        versions_data = versions_response.json()
        assert len(versions_data["data"]) == 2
        
        # Verify version 1 still exists with original content
        version1_response = client.get(f"/api/v1/projects/{project_id}/solution-outlines/1")
        assert version1_response.status_code == 200
        version1_data = version1_response.json()
        assert version1_data["version"] == 1
        assert version1_data["content"] == initial_content
        assert version1_data["status"] == "draft"
        
        # Verify version 2 has updated content
        version2_response = client.get(f"/api/v1/projects/{project_id}/solution-outlines/2")
        assert version2_response.status_code == 200
        version2_data = version2_response.json()
        assert version2_data["version"] == 2
        assert version2_data["content"] == updated_content
        assert version2_data["status"] == "published"
        
        # Verify latest returns version 2
        latest_response = client.get(f"/api/v1/projects/{project_id}/solution-outlines/latest")
        assert latest_response.status_code == 200
        latest_data = latest_response.json()
        assert latest_data["version"] == 2
        assert latest_data["content"] == updated_content

    def test_team_member_consistency(self, client: TestClient, project_workflow_data):
        """Test consistency of team member data across operations."""
        project_id = project_workflow_data["project"]["id"]
        
        # Create project
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        # Create team with specific members
        original_members = "Alice Johnson, Bob Smith, Carol Davis"
        team_data = {
            "name": "Development Team",
            "members": original_members
        }
        team_response = client.post(f"/api/v1/projects/{project_id}/teams", json=team_data)
        assert team_response.status_code == 201
        team = team_response.json()
        team_id = team["id"]
        
        # Verify team members
        assert team["members"] == original_members
        
        # Update team members
        updated_members = "Alice Johnson, Bob Smith, Carol Davis, David Wilson"
        update_response = client.put(
            f"/api/v1/teams/{team_id}",
            json={"name": "Development Team", "members": updated_members}
        )
        assert update_response.status_code == 200
        updated_team = update_response.json()
        assert updated_team["members"] == updated_members
        
        # Verify consistency across different retrieval methods
        
        # Get team directly
        direct_response = client.get(f"/api/v1/teams/{team_id}")
        assert direct_response.status_code == 200
        direct_team = direct_response.json()
        assert direct_team["members"] == updated_members
        
        # Get team through project teams list
        teams_list_response = client.get(f"/api/v1/projects/{project_id}/teams")
        assert teams_list_response.status_code == 200
        teams_data = teams_list_response.json()
        project_team = teams_data["data"][0]
        assert project_team["members"] == updated_members
        
        # Search for team
        search_response = client.get(f"/api/v1/projects/{project_id}/teams/search?query=Development")
        assert search_response.status_code == 200
        search_data = search_response.json()
        search_team = search_data["data"][0]
        assert search_team["members"] == updated_members

    def test_adr_title_uniqueness_consistency(self, client: TestClient, project_workflow_data):
        """Test that ADR title uniqueness is maintained consistently."""
        project_id = project_workflow_data["project"]["id"]
        
        # Create project
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        # Create first ADR
        adr_title = "Database Selection Decision"
        adr1_response = client.post(
            f"/api/v1/projects/{project_id}/adrs",
            params={"title": adr_title, "content": "We chose PostgreSQL"}
        )
        assert adr1_response.status_code == 201
        adr1 = adr1_response.json()
        
        # Try to create second ADR with same title (should fail)
        adr2_response = client.post(
            f"/api/v1/projects/{project_id}/adrs",
            params={"title": adr_title, "content": "Different content"}
        )
        assert adr2_response.status_code == 409
        error_data = adr2_response.json()
        assert "already exists" in error_data["message"].lower()
        
        # Update first ADR to different title
        new_title = "Updated Database Selection Decision"
        update_response = client.put(
            f"/api/v1/adrs/{adr1['id']}",
            params={"title": new_title, "content": "Updated content"}
        )
        assert update_response.status_code == 200
        updated_adr = update_response.json()
        assert updated_adr["title"] == new_title
        
        # Now should be able to create ADR with original title
        adr3_response = client.post(
            f"/api/v1/projects/{project_id}/adrs",
            params={"title": adr_title, "content": "New ADR with original title"}
        )
        assert adr3_response.status_code == 201
        adr3 = adr3_response.json()
        assert adr3["title"] == adr_title
        
        # Verify both ADRs exist with different titles
        adrs_response = client.get(f"/api/v1/projects/{project_id}/adrs")
        assert adrs_response.status_code == 200
        adrs_data = adrs_response.json()
        assert len(adrs_data["data"]) == 2
        
        titles = [adr["title"] for adr in adrs_data["data"]]
        assert new_title in titles
        assert adr_title in titles

    def test_pagination_consistency_across_operations(self, client: TestClient, project_workflow_data):
        """Test that pagination remains consistent across different operations."""
        project_id = project_workflow_data["project"]["id"]
        
        # Create project
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        # Create 25 teams
        created_teams = []
        for i in range(25):
            team_data = {
                "name": f"Team {i+1:02d}",
                "members": f"Member {i+1}"
            }
            team_response = client.post(f"/api/v1/projects/{project_id}/teams", json=team_data)
            assert team_response.status_code == 201
            created_teams.append(team_response.json())
        
        # Test pagination consistency
        page1_response = client.get(f"/api/v1/projects/{project_id}/teams?page=1&per_page=10")
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        assert len(page1_data["data"]) == 10
        assert page1_data["meta"]["total"] == 25
        assert page1_data["meta"]["pages"] == 3
        
        # Update a team (should not affect pagination counts)
        first_team = created_teams[0]
        update_response = client.put(
            f"/api/v1/teams/{first_team['id']}",
            json={"name": "Updated Team 01", "members": "Updated Member 1"}
        )
        assert update_response.status_code == 200
        
        # Verify pagination is still consistent
        page1_after_update = client.get(f"/api/v1/projects/{project_id}/teams?page=1&per_page=10")
        assert page1_after_update.status_code == 200
        page1_after_data = page1_after_update.json()
        assert len(page1_after_data["data"]) == 10
        assert page1_after_data["meta"]["total"] == 25  # Count should remain same
        assert page1_after_data["meta"]["pages"] == 3
        
        # Delete a team
        delete_response = client.delete(f"/api/v1/teams/{first_team['id']}")
        assert delete_response.status_code == 200
        
        # Verify pagination reflects the deletion
        page1_after_delete = client.get(f"/api/v1/projects/{project_id}/teams?page=1&per_page=10")
        assert page1_after_delete.status_code == 200
        page1_delete_data = page1_after_delete.json()
        assert len(page1_delete_data["data"]) == 10
        assert page1_delete_data["meta"]["total"] == 24  # Count should decrease
        assert page1_delete_data["meta"]["pages"] == 3  # Still 3 pages (24 items, 10 per page)
        
        # Verify last page has correct count
        page3_response = client.get(f"/api/v1/projects/{project_id}/teams?page=3&per_page=10")
        assert page3_response.status_code == 200
        page3_data = page3_response.json()
        assert len(page3_data["data"]) == 4  # 24 total - 20 in first two pages = 4 in last page

class TestTransactionConsistency:
    """End-to-end tests for transaction consistency."""
    
    def test_atomic_project_creation(self, client: TestClient, project_workflow_data):
        """Test that project creation with related entities is atomic."""
        project_id = project_workflow_data["project"]["id"]
        
        # Create project
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        # Create team successfully
        team_response = client.post(
            f"/api/v1/projects/{project_id}/teams",
            json=project_workflow_data["teams"][0]
        )
        assert team_response.status_code == 201
        team = team_response.json()
        
        # Try to create team with invalid data (should fail without affecting existing data)
        invalid_team_response = client.post(
            f"/api/v1/projects/{project_id}/teams",
            json={"name": "", "members": ""}  # Invalid empty name
        )
        assert invalid_team_response.status_code == 422
        
        # Verify original team still exists and is unchanged
        team_check_response = client.get(f"/api/v1/teams/{team['id']}")
        assert team_check_response.status_code == 200
        team_check = team_check_response.json()
        assert team_check["name"] == project_workflow_data["teams"][0]["name"]
        assert team_check["members"] == project_workflow_data["teams"][0]["members"]
        
        # Verify project still exists
        project_check_response = client.get(f"/api/v1/projects/{project_id}")
        assert project_check_response.status_code == 200

    def test_concurrent_operations_consistency(self, client: TestClient, project_workflow_data):
        """Test consistency under concurrent-like operations."""
        project_id = project_workflow_data["project"]["id"]
        
        # Create project
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        # Simulate concurrent operations by performing multiple operations rapidly
        operations_results = []
        
        # Rapid team creation
        for i in range(5):
            team_data = {
                "name": f"Concurrent Team {i+1}",
                "members": f"Member {i+1}"
            }
            team_response = client.post(f"/api/v1/projects/{project_id}/teams", json=team_data)
            operations_results.append(("create_team", team_response.status_code))
        
        # Rapid ADR creation
        for i in range(5):
            adr_data = {
                "title": f"Concurrent ADR {i+1}",
                "content": f"Content for concurrent ADR {i+1}"
            }
            adr_response = client.post(f"/api/v1/projects/{project_id}/adrs", params=adr_data)
            operations_results.append(("create_adr", adr_response.status_code))
        
        # All operations should succeed
        for operation, status_code in operations_results:
            assert status_code == 201, f"Operation {operation} failed with status {status_code}"
        
        # Verify final state consistency
        teams_response = client.get(f"/api/v1/projects/{project_id}/teams")
        assert teams_response.status_code == 200
        teams_data = teams_response.json()
        assert len(teams_data["data"]) == 5
        
        adrs_response = client.get(f"/api/v1/projects/{project_id}/adrs")
        assert adrs_response.status_code == 200
        adrs_data = adrs_response.json()
        assert len(adrs_data["data"]) == 5

class TestReferentialIntegrity:
    """End-to-end tests for referential integrity."""
    
    def test_foreign_key_constraints(self, client: TestClient, project_workflow_data):
        """Test that foreign key constraints are properly enforced."""
        # Try to create team for non-existent project
        team_response = client.post(
            "/api/v1/projects/non-existent-project/teams",
            json={"name": "Test Team", "members": "Test Member"}
        )
        assert team_response.status_code == 404
        
        # Try to create ADR for non-existent project
        adr_response = client.post(
            "/api/v1/projects/non-existent-project/adrs",
            params={"title": "Test ADR", "content": "Test content"}
        )
        assert adr_response.status_code == 404
        
        # Try to create solution outline for non-existent project
        solution_response = client.post(
            "/api/v1/projects/non-existent-project/solution-outlines",
            params={"content": "Test content", "status": "draft"}
        )
        assert solution_response.status_code == 404

    def test_data_integrity_after_updates(self, client: TestClient, project_workflow_data, workflow_test_helpers):
        """Test that data integrity is maintained after updates."""
        # Create complete project
        results = workflow_test_helpers.create_complete_project(client, project_workflow_data)
        project_id = project_workflow_data["project"]["id"]
        
        # Update project details
        updated_project_data = {
            "name": "Updated Project Name",
            "description": "Updated project description",
            "code": "UPD001",
            "state": "active"
        }
        project_update_response = client.put(f"/api/v1/projects/{project_id}", json=updated_project_data)
        assert project_update_response.status_code == 200
        
        # Verify all related entities still reference the correct project
        teams_response = client.get(f"/api/v1/projects/{project_id}/teams")
        assert teams_response.status_code == 200
        teams_data = teams_response.json()
        for team in teams_data["data"]:
            assert team["project_id"] == project_id
        
        adrs_response = client.get(f"/api/v1/projects/{project_id}/adrs")
        assert adrs_response.status_code == 200
        adrs_data = adrs_response.json()
        for adr in adrs_data["data"]:
            assert adr["project_id"] == project_id
        
        solution_outline_response = client.get(f"/api/v1/projects/{project_id}/solution-outlines/latest")
        assert solution_outline_response.status_code == 200
        solution_outline = solution_outline_response.json()
        assert solution_outline["project_id"] == project_id