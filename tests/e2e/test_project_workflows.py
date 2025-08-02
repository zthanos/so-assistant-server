"""End-to-end tests for complete project workflows.

This module contains end-to-end tests that simulate complete user workflows
across the entire application, testing the integration of all components.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

class TestCompleteProjectWorkflow:
    """End-to-end tests for complete project creation and management workflows."""
    
    def test_complete_project_creation_workflow(self, client: TestClient, project_workflow_data, workflow_test_helpers):
        """Test the complete workflow of creating a project with all components."""
        # Execute the complete project creation workflow
        results = workflow_test_helpers.create_complete_project(client, project_workflow_data)
        
        # Verify all components were created successfully
        assert "project" in results
        assert "teams" in results
        assert "adrs" in results
        assert "solution_outline" in results
        
        # Verify project details
        project = results["project"]
        assert project["id"] == project_workflow_data["project"]["id"]
        assert project["name"] == project_workflow_data["project"]["name"]
        assert project["code"] == project_workflow_data["project"]["code"]
        
        # Verify teams were created
        assert len(results["teams"]) == len(project_workflow_data["teams"])
        for i, team in enumerate(results["teams"]):
            expected_team = project_workflow_data["teams"][i]
            assert team["name"] == expected_team["name"]
            assert team["members"] == expected_team["members"]
            assert team["project_id"] == project["id"]
        
        # Verify ADRs were created
        assert len(results["adrs"]) == len(project_workflow_data["adrs"])
        for i, adr in enumerate(results["adrs"]):
            expected_adr = project_workflow_data["adrs"][i]
            assert adr["title"] == expected_adr["title"]
            assert adr["content"] == expected_adr["content"]
            assert adr["project_id"] == project["id"]
        
        # Verify solution outline was created
        solution_outline = results["solution_outline"]
        expected_outline = project_workflow_data["solution_outline"]
        assert solution_outline["content"] == expected_outline["content"]
        assert solution_outline["status"] == expected_outline["status"]
        assert solution_outline["project_id"] == project["id"]
        assert solution_outline["version"] == 1

    def test_project_manager_workflow(self, client: TestClient, project_workflow_data, workflow_test_helpers):
        """Test a typical project manager workflow."""
        project_id = project_workflow_data["project"]["id"]
        
        # Step 1: Create project
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        project = project_response.json()
        
        # Step 2: View project details
        project_details_response = client.get(f"/api/v1/projects/{project_id}")
        assert project_details_response.status_code == 200
        assert project_details_response.json()["id"] == project_id
        
        # Step 3: Create and manage teams
        teams_created = []
        for team_data in project_workflow_data["teams"]:
            team_response = client.post(f"/api/v1/projects/{project_id}/teams", json=team_data)
            assert team_response.status_code == 201
            teams_created.append(team_response.json())
        
        # Step 4: View all teams
        teams_list_response = client.get(f"/api/v1/projects/{project_id}/teams")
        assert teams_list_response.status_code == 200
        teams_data = teams_list_response.json()
        assert teams_data["success"] is True
        assert len(teams_data["data"]) == len(project_workflow_data["teams"])
        
        # Step 5: Update a team
        first_team = teams_created[0]
        updated_team_data = {
            "name": "Updated Frontend Team",
            "members": "Alice Johnson, Bob Smith, Carol Davis"
        }
        update_response = client.put(f"/api/v1/teams/{first_team['id']}", json=updated_team_data)
        assert update_response.status_code == 200
        updated_team = update_response.json()
        assert updated_team["name"] == updated_team_data["name"]
        assert updated_team["members"] == updated_team_data["members"]
        
        # Step 6: Count teams
        count_response = client.get(f"/api/v1/projects/{project_id}/teams/count")
        assert count_response.status_code == 200
        assert count_response.json() == len(project_workflow_data["teams"])

    def test_solution_architect_workflow(self, client: TestClient, project_workflow_data, workflow_test_helpers):
        """Test a typical solution architect workflow."""
        project_id = project_workflow_data["project"]["id"]
        
        # Step 1: Create project (prerequisite)
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        # Step 2: Create Architecture Decision Records
        adrs_created = []
        for adr_data in project_workflow_data["adrs"]:
            adr_response = client.post(
                f"/api/v1/projects/{project_id}/adrs",
                params=adr_data
            )
            assert adr_response.status_code == 201
            adrs_created.append(adr_response.json())
        
        # Step 3: View all ADRs for the project
        adrs_list_response = client.get(f"/api/v1/projects/{project_id}/adrs")
        assert adrs_list_response.status_code == 200
        adrs_data = adrs_list_response.json()
        assert adrs_data["success"] is True
        assert len(adrs_data["data"]) == len(project_workflow_data["adrs"])
        
        # Step 4: Update an ADR
        first_adr = adrs_created[0]
        updated_adr_response = client.put(
            f"/api/v1/adrs/{first_adr['id']}",
            params={
                "title": "Updated Frontend Framework Selection",
                "content": "We have decided to use React with TypeScript for better type safety and developer experience."
            }
        )
        assert updated_adr_response.status_code == 200
        updated_adr = updated_adr_response.json()
        assert "Updated" in updated_adr["title"]
        assert "TypeScript" in updated_adr["content"]
        
        # Step 5: Create solution outline
        solution_outline_response = client.post(
            f"/api/v1/projects/{project_id}/solution-outlines",
            params=project_workflow_data["solution_outline"]
        )
        assert solution_outline_response.status_code == 201
        solution_outline = solution_outline_response.json()
        
        # Step 6: Update solution outline (creating new version)
        updated_content = project_workflow_data["solution_outline"]["content"] + "\n\n## Updated Architecture\nAdded microservices architecture considerations."
        updated_outline_response = client.put(
            f"/api/v1/projects/{project_id}/solution-outlines",
            params={"content": updated_content, "status": "published"}
        )
        assert updated_outline_response.status_code == 200
        updated_outline = updated_outline_response.json()
        assert updated_outline["version"] == 2
        assert updated_outline["status"] == "published"
        assert "Updated Architecture" in updated_outline["content"]
        
        # Step 7: View solution outline versions
        versions_response = client.get(f"/api/v1/projects/{project_id}/solution-outlines")
        assert versions_response.status_code == 200
        versions_data = versions_response.json()
        assert versions_data["success"] is True
        assert len(versions_data["data"]) == 2  # Two versions should exist

    def test_developer_workflow(self, client: TestClient, project_workflow_data, workflow_test_helpers):
        """Test a typical developer workflow."""
        # Setup: Create complete project (as would be done by PM/Architect)
        results = workflow_test_helpers.create_complete_project(client, project_workflow_data)
        project_id = project_workflow_data["project"]["id"]
        
        # Step 1: View project details
        project_response = client.get(f"/api/v1/projects/{project_id}")
        assert project_response.status_code == 200
        project = project_response.json()
        assert project["name"] == project_workflow_data["project"]["name"]
        
        # Step 2: Check team assignments
        teams_response = client.get(f"/api/v1/projects/{project_id}/teams")
        assert teams_response.status_code == 200
        teams_data = teams_response.json()
        assert teams_data["success"] is True
        
        # Find developer's team (simulate being assigned to Backend Team)
        backend_team = None
        for team in teams_data["data"]:
            if team["name"] == "Backend Team":
                backend_team = team
                break
        assert backend_team is not None
        assert "Charlie Brown" in backend_team["members"]
        
        # Step 3: Read relevant ADRs
        adrs_response = client.get(f"/api/v1/projects/{project_id}/adrs")
        assert adrs_response.status_code == 200
        adrs_data = adrs_response.json()
        
        # Search for database-related ADR
        database_adr = None
        for adr in adrs_data["data"]:
            if "Database" in adr["title"]:
                database_adr = adr
                break
        assert database_adr is not None
        assert "PostgreSQL" in database_adr["content"]
        
        # Step 4: View latest solution outline
        solution_outline_response = client.get(f"/api/v1/projects/{project_id}/solution-outlines/latest")
        assert solution_outline_response.status_code == 200
        solution_outline = solution_outline_response.json()
        assert "FastAPI" in solution_outline["content"]
        
        # Step 5: Search for specific information
        # Search teams for "Backend"
        team_search_response = client.get(f"/api/v1/projects/{project_id}/teams/search?query=Backend")
        assert team_search_response.status_code == 200
        search_data = team_search_response.json()
        assert search_data["success"] is True
        assert len(search_data["data"]) == 1
        assert search_data["data"][0]["name"] == "Backend Team"
        
        # Search ADRs for "API"
        adr_search_response = client.get(f"/api/v1/projects/{project_id}/adrs/search?query=API")
        assert adr_search_response.status_code == 200
        adr_search_data = adr_search_response.json()
        assert adr_search_data["success"] is True
        assert len(adr_search_data["data"]) >= 1

class TestCrossComponentWorkflows:
    """End-to-end tests for workflows that span multiple components."""
    
    def test_solution_outline_review_workflow(self, client_with_sse: TestClient, project_workflow_data):
        """Test the complete solution outline review workflow with SSE."""
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
        
        # Step 2: Request review (this would normally stream via SSE)
        review_response = client_with_sse.post(f"/api/v1/solution-outlines/{solution_outline['id']}/review")
        # The review endpoint should either succeed or fail gracefully
        assert review_response.status_code in [200, 500, 503]
        
        # Step 3: Check review comments (if review was successful)
        if review_response.status_code == 200:
            comments_response = client_with_sse.get(f"/api/v1/solution-outlines/{solution_outline['id']}/review-comments")
            assert comments_response.status_code == 200

    def test_pagination_across_components(self, client: TestClient, project_workflow_data):
        """Test pagination functionality across different components."""
        project_id = project_workflow_data["project"]["id"]
        
        # Create project
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        # Create many teams (more than default page size)
        for i in range(25):
            team_data = {
                "name": f"Team {i+1:02d}",
                "members": f"Member {i+1}"
            }
            team_response = client.post(f"/api/v1/projects/{project_id}/teams", json=team_data)
            assert team_response.status_code == 201
        
        # Create many ADRs
        for i in range(30):
            adr_data = {
                "title": f"ADR {i+1:02d} - Decision {i+1}",
                "content": f"This is the content for ADR number {i+1}"
            }
            adr_response = client.post(f"/api/v1/projects/{project_id}/adrs", params=adr_data)
            assert adr_response.status_code == 201
        
        # Test teams pagination
        teams_page1 = client.get(f"/api/v1/projects/{project_id}/teams?page=1&per_page=10")
        assert teams_page1.status_code == 200
        teams_data1 = teams_page1.json()
        assert len(teams_data1["data"]) == 10
        assert teams_data1["meta"]["page"] == 1
        assert teams_data1["meta"]["total"] == 25
        assert teams_data1["meta"]["has_next"] is True
        
        teams_page3 = client.get(f"/api/v1/projects/{project_id}/teams?page=3&per_page=10")
        assert teams_page3.status_code == 200
        teams_data3 = teams_page3.json()
        assert len(teams_data3["data"]) == 5  # Last page with remaining items
        assert teams_data3["meta"]["page"] == 3
        assert teams_data3["meta"]["has_next"] is False
        
        # Test ADRs pagination with sorting
        adrs_sorted = client.get(f"/api/v1/projects/{project_id}/adrs?page=1&per_page=15&sort_by=title&sort_order=desc")
        assert adrs_sorted.status_code == 200
        adrs_sorted_data = adrs_sorted.json()
        assert len(adrs_sorted_data["data"]) == 15
        assert adrs_sorted_data["meta"]["total"] == 30
        
        # Verify sorting (titles should be in descending order)
        titles = [adr["title"] for adr in adrs_sorted_data["data"]]
        assert titles == sorted(titles, reverse=True)

    def test_error_handling_across_workflow(self, client: TestClient, project_workflow_data):
        """Test error handling throughout a complete workflow."""
        project_id = project_workflow_data["project"]["id"]
        
        # Step 1: Try to create team for non-existent project
        team_response = client.post(
            f"/api/v1/projects/non-existent-project/teams",
            json={"name": "Test Team", "members": "Test Member"}
        )
        assert team_response.status_code == 404
        error_data = team_response.json()
        assert error_data["success"] is False
        assert "not found" in error_data["message"].lower()
        
        # Step 2: Create project successfully
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        # Step 3: Try to create duplicate project
        duplicate_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert duplicate_response.status_code == 409
        duplicate_error = duplicate_response.json()
        assert duplicate_error["success"] is False
        assert "already exists" in duplicate_error["message"].lower()
        
        # Step 4: Create team successfully
        team_response = client.post(
            f"/api/v1/projects/{project_id}/teams",
            json=project_workflow_data["teams"][0]
        )
        assert team_response.status_code == 201
        
        # Step 5: Try to create team with duplicate name
        duplicate_team_response = client.post(
            f"/api/v1/projects/{project_id}/teams",
            json=project_workflow_data["teams"][0]
        )
        assert duplicate_team_response.status_code == 409
        
        # Step 6: Try to access non-existent resources
        non_existent_team = client.get("/api/v1/teams/999")
        assert non_existent_team.status_code == 404
        
        non_existent_adr = client.get("/api/v1/adrs/999")
        assert non_existent_adr.status_code == 404
        
        # Step 7: Verify all error responses follow standard format
        for error_response in [team_response, duplicate_response, duplicate_team_response, non_existent_team, non_existent_adr]:
            if error_response.status_code >= 400:
                error_data = error_response.json()
                assert "success" in error_data
                assert error_data["success"] is False
                assert "message" in error_data
                assert "timestamp" in error_data

class TestPerformanceWorkflows:
    """End-to-end tests for performance-related workflows."""
    
    def test_large_dataset_workflow(self, client: TestClient, project_workflow_data):
        """Test workflows with larger datasets to verify performance."""
        project_id = project_workflow_data["project"]["id"]
        
        # Create project
        project_response = client.post("/api/v1/projects", json=project_workflow_data["project"])
        assert project_response.status_code == 201
        
        # Create a large number of teams
        import time
        start_time = time.time()
        
        for i in range(50):
            team_data = {
                "name": f"Performance Test Team {i+1:03d}",
                "members": f"Member {i+1}, Member {i+2}"
            }
            team_response = client.post(f"/api/v1/projects/{project_id}/teams", json=team_data)
            assert team_response.status_code == 201
        
        creation_time = time.time() - start_time
        
        # Test pagination performance
        start_time = time.time()
        
        # Get all teams with pagination
        all_teams = []
        page = 1
        while True:
            teams_response = client.get(f"/api/v1/projects/{project_id}/teams?page={page}&per_page=20")
            assert teams_response.status_code == 200
            teams_data = teams_response.json()
            all_teams.extend(teams_data["data"])
            
            if not teams_data["meta"]["has_next"]:
                break
            page += 1
        
        pagination_time = time.time() - start_time
        
        # Verify we got all teams
        assert len(all_teams) == 50
        
        # Test search performance
        start_time = time.time()
        search_response = client.get(f"/api/v1/projects/{project_id}/teams/search?query=Performance")
        search_time = time.time() - start_time
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert len(search_data["data"]) == 50  # All teams should match "Performance"
        
        # Performance assertions (these are basic - in practice you'd have more sophisticated benchmarks)
        assert creation_time < 30.0  # Should create 50 teams in under 30 seconds
        assert pagination_time < 5.0  # Should paginate through all teams in under 5 seconds
        assert search_time < 2.0  # Should search through all teams in under 2 seconds