"""Task API endpoints.

This module provides API endpoints for managing tasks.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.dependencies import get_task_service
from app.services.tasks import TaskService
from app.api.schemas.tasks import TaskBase, TaskCreate, TaskUpdate, TaskResponse, TaskStatus
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException

router = APIRouter(tags=["Tasks"])

@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new task for a project."
)
def create_task(
    project_id: str = Path(..., description="The ID of the project"),
    task_data: TaskBase = Body(..., description="The task data"),
    service: TaskService = Depends(get_task_service)
):
    """Create a new task.
    
    Args:
        project_id: The ID of the project.
        task_data: The task data.
        service: The task service.
        
    Returns:
        The created task.
        
    Raises:
        NotFoundException: If the project or team is not found.
        BadRequestException: If the description is empty or team validation fails.
    """
    try:
        return service.create_task(
            project_id, 
            task_data.description, 
            task_data.assigned_to_team_id
        )
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a task by ID",
    description="Get a task by its ID."
)
def get_task(
    task_id: int = Path(..., description="The ID of the task"),
    service: TaskService = Depends(get_task_service)
):
    """Get a task by ID.
    
    Args:
        task_id: The ID of the task.
        service: The task service.
        
    Returns:
        The task.
        
    Raises:
        NotFoundException: If the task is not found.
    """
    try:
        return service.get_task(task_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/tasks",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all tasks for a project",
    description="Get all tasks for a project with optional filtering."
)
def get_tasks_for_project(
    project_id: str = Path(..., description="The ID of the project"),
    skip: int = Query(0, description="The number of records to skip"),
    limit: int = Query(100, description="The maximum number of records to return"),
    status_filter: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    team_id: Optional[int] = Query(None, description="Filter by assigned team ID"),
    service: TaskService = Depends(get_task_service)
):
    """Get all tasks for a project.
    
    Args:
        project_id: The ID of the project.
        skip: The number of records to skip.
        limit: The maximum number of records to return.
        status_filter: Optional status filter.
        team_id: Optional team filter.
        service: The task service.
        
    Returns:
        A list of tasks for the project.
        
    Raises:
        NotFoundException: If the project is not found.
        BadRequestException: If team validation fails.
    """
    try:
        return service.get_tasks_for_project(
            project_id, skip, limit, status_filter, team_id
        )
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/teams/{team_id}/tasks",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all tasks for a team",
    description="Get all tasks assigned to a team."
)
def get_tasks_for_team(
    team_id: int = Path(..., description="The ID of the team"),
    skip: int = Query(0, description="The number of records to skip"),
    limit: int = Query(100, description="The maximum number of records to return"),
    status_filter: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    service: TaskService = Depends(get_task_service)
):
    """Get all tasks for a team.
    
    Args:
        team_id: The ID of the team.
        skip: The number of records to skip.
        limit: The maximum number of records to return.
        status_filter: Optional status filter.
        service: The task service.
        
    Returns:
        A list of tasks assigned to the team.
        
    Raises:
        NotFoundException: If the team is not found.
    """
    try:
        return service.get_tasks_for_team(team_id, skip, limit, status_filter)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a task",
    description="Update a task."
)
def update_task(
    task_id: int = Path(..., description="The ID of the task"),
    task_data: TaskUpdate = Body(..., description="The task update data"),
    service: TaskService = Depends(get_task_service)
):
    """Update a task.
    
    Args:
        task_id: The ID of the task.
        task_data: The task update data.
        service: The task service.
        
    Returns:
        The updated task.
        
    Raises:
        NotFoundException: If the task or team is not found.
        BadRequestException: If no update fields are provided or validation fails.
    """
    try:
        return service.update_task(
            task_id,
            task_data.description,
            task_data.assigned_to_team_id,
            task_data.status
        )
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.patch(
    "/tasks/{task_id}/status",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task status",
    description="Update the status of a task."
)
def update_task_status(
    task_id: int = Path(..., description="The ID of the task"),
    status_update: TaskStatus = Body(..., description="The new status"),
    service: TaskService = Depends(get_task_service)
):
    """Update task status.
    
    Args:
        task_id: The ID of the task.
        status_update: The new status.
        service: The task service.
        
    Returns:
        The updated task.
        
    Raises:
        NotFoundException: If the task is not found.
    """
    try:
        return service.update_task_status(task_id, status_update)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.patch(
    "/tasks/{task_id}/assign",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign task to team",
    description="Assign a task to a team or unassign it."
)
def assign_task_to_team(
    task_id: int = Path(..., description="The ID of the task"),
    team_assignment: Optional[int] = Body(None, description="The team ID to assign to, or null to unassign"),
    service: TaskService = Depends(get_task_service)
):
    """Assign task to team.
    
    Args:
        task_id: The ID of the task.
        team_assignment: The team ID to assign to, or None to unassign.
        service: The task service.
        
    Returns:
        The updated task.
        
    Raises:
        NotFoundException: If the task or team is not found.
        BadRequestException: If team validation fails.
    """
    try:
        return service.assign_task_to_team(task_id, team_assignment)
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.delete(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a task",
    description="Delete a task."
)
def delete_task(
    task_id: int = Path(..., description="The ID of the task"),
    service: TaskService = Depends(get_task_service)
):
    """Delete a task.
    
    Args:
        task_id: The ID of the task.
        service: The task service.
        
    Returns:
        The deleted task.
        
    Raises:
        NotFoundException: If the task is not found.
    """
    try:
        return service.delete_task(task_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

class BulkStatusUpdate(BaseModel):
    """Bulk status update request model."""
    task_ids: List[int]
    status: TaskStatus

class BulkTeamAssignment(BaseModel):
    """Bulk team assignment request model."""
    task_ids: List[int]
    team_id: Optional[int] = None

@router.patch(
    "/tasks/bulk-status-update",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Bulk update task status",
    description="Update the status of multiple tasks."
)
def bulk_update_task_status(
    request_data: BulkStatusUpdate = Body(..., description="The bulk status update data"),
    service: TaskService = Depends(get_task_service)
):
    """Bulk update task status.
    
    Args:
        request_data: The bulk status update data.
        service: The task service.
        
    Returns:
        The updated tasks.
        
    Raises:
        BadRequestException: If no task IDs are provided.
        NotFoundException: If any task is not found.
    """
    try:
        return service.bulk_update_status(request_data.task_ids, request_data.status)
    except (BadRequestException, NotFoundException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.patch(
    "/tasks/bulk-team-assignment",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Bulk assign tasks to team",
    description="Assign multiple tasks to a team or unassign them."
)
def bulk_assign_tasks_to_team(
    request_data: BulkTeamAssignment = Body(..., description="The bulk team assignment data"),
    service: TaskService = Depends(get_task_service)
):
    """Bulk assign tasks to team.
    
    Args:
        request_data: The bulk team assignment data.
        service: The task service.
        
    Returns:
        The updated tasks.
        
    Raises:
        BadRequestException: If no task IDs are provided or team validation fails.
        NotFoundException: If any task or the team is not found.
    """
    try:
        return service.bulk_assign_to_team(request_data.task_ids, request_data.team_id)
    except (BadRequestException, NotFoundException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/tasks/count",
    response_model=int,
    status_code=status.HTTP_200_OK,
    summary="Count tasks for a project",
    description="Count the number of tasks for a project."
)
def count_tasks_for_project(
    project_id: str = Path(..., description="The ID of the project"),
    service: TaskService = Depends(get_task_service)
):
    """Count tasks for a project.
    
    Args:
        project_id: The ID of the project.
        service: The task service.
        
    Returns:
        The number of tasks for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.count_tasks_for_project(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/teams/{team_id}/tasks/count",
    response_model=int,
    status_code=status.HTTP_200_OK,
    summary="Count tasks for a team",
    description="Count the number of tasks assigned to a team."
)
def count_tasks_for_team(
    team_id: int = Path(..., description="The ID of the team"),
    service: TaskService = Depends(get_task_service)
):
    """Count tasks for a team.
    
    Args:
        team_id: The ID of the team.
        service: The task service.
        
    Returns:
        The number of tasks assigned to the team.
        
    Raises:
        NotFoundException: If the team is not found.
    """
    try:
        return service.count_tasks_for_team(team_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/tasks/status-counts",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get task status counts for a project",
    description="Get the count of tasks by status for a project."
)
def get_task_status_counts(
    project_id: str = Path(..., description="The ID of the project"),
    service: TaskService = Depends(get_task_service)
):
    """Get task status counts for a project.
    
    Args:
        project_id: The ID of the project.
        service: The task service.
        
    Returns:
        A dictionary mapping status to count.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.get_task_status_counts(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)