"""Custom exceptions for systems and teams operations.

This module provides specific exception classes for systems and teams management
operations, extending the base AppException class for consistent error handling.
"""
from typing import Optional, List, Dict, Any, Union
from app.core.exceptions import AppException, NotFoundException, ConflictException, ValidationException


class SystemNotFoundException(NotFoundException):
    """Exception raised when a system is not found.
    
    Attributes:
        message: A human-readable error message.
        system_id: The ID of the system that was not found.
        project_id: The project ID where the system was expected.
    """
    def __init__(
        self, 
        message: str = "System not found", 
        system_id: Optional[Union[str, int]] = None,
        project_id: Optional[str] = None
    ):
        detail = {"resource_type": "System"}
        if system_id:
            detail["system_id"] = system_id
        if project_id:
            detail["project_id"] = project_id
        super().__init__(message, resource_type="System", resource_id=system_id)


class TeamNotFoundException(NotFoundException):
    """Exception raised when a team is not found.
    
    Attributes:
        message: A human-readable error message.
        team_id: The ID of the team that was not found.
        project_id: The project ID where the team was expected.
    """
    def __init__(
        self, 
        message: str = "Team not found", 
        team_id: Optional[Union[str, int]] = None,
        project_id: Optional[str] = None
    ):
        detail = {"resource_type": "Team"}
        if team_id:
            detail["team_id"] = team_id
        if project_id:
            detail["project_id"] = project_id
        super().__init__(message, resource_type="Team", resource_id=team_id)


class DuplicateSystemException(ConflictException):
    """Exception raised when attempting to create a system with a duplicate name.
    
    Attributes:
        message: A human-readable error message.
        system_name: The name of the system that already exists.
        project_id: The project ID where the duplicate was found.
    """
    def __init__(
        self, 
        message: str = "System with this name already exists in the project", 
        system_name: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        detail = {"resource_type": "System"}
        if system_name:
            detail["system_name"] = system_name
        if project_id:
            detail["project_id"] = project_id
        super().__init__(message, resource_type="System", resource_id=system_name)


class DuplicateTeamException(ConflictException):
    """Exception raised when attempting to create a team with a duplicate name.
    
    Attributes:
        message: A human-readable error message.
        team_name: The name of the team that already exists.
        project_id: The project ID where the duplicate was found.
    """
    def __init__(
        self, 
        message: str = "Team with this name already exists in the project", 
        team_name: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        detail = {"resource_type": "Team"}
        if team_name:
            detail["team_name"] = team_name
        if project_id:
            detail["project_id"] = project_id
        super().__init__(message, resource_type="Team", resource_id=team_name)


class InvalidDependencyException(ValidationException):
    """Exception raised when system dependency references are invalid.
    
    Attributes:
        message: A human-readable error message.
        invalid_dependencies: List of dependency names that are invalid.
        system_name: The name of the system with invalid dependencies.
        project_id: The project ID where the validation failed.
    """
    def __init__(
        self, 
        message: str = "Invalid system dependencies", 
        invalid_dependencies: Optional[List[str]] = None,
        system_name: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        detail = {"resource_type": "System"}
        if invalid_dependencies:
            detail["invalid_dependencies"] = invalid_dependencies
        if system_name:
            detail["system_name"] = system_name
        if project_id:
            detail["project_id"] = project_id
        
        errors = []
        if invalid_dependencies:
            for dep in invalid_dependencies:
                errors.append({
                    "field": "dependencies",
                    "message": f"System '{dep}' does not exist in the project",
                    "invalid_value": dep
                })
        
        super().__init__(message, errors=errors)


class CircularDependencyException(ValidationException):
    """Exception raised when circular dependencies are detected in systems.
    
    Attributes:
        message: A human-readable error message.
        dependency_chain: The chain of dependencies that creates the cycle.
        system_name: The name of the system that would create the cycle.
        project_id: The project ID where the validation failed.
    """
    def __init__(
        self, 
        message: str = "Circular dependency detected", 
        dependency_chain: Optional[List[str]] = None,
        system_name: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        detail = {"resource_type": "System"}
        if dependency_chain:
            detail["dependency_chain"] = dependency_chain
        if system_name:
            detail["system_name"] = system_name
        if project_id:
            detail["project_id"] = project_id
        
        errors = []
        if dependency_chain:
            errors.append({
                "field": "dependencies",
                "message": f"Circular dependency detected: {' -> '.join(dependency_chain)}",
                "dependency_chain": dependency_chain
            })
        
        super().__init__(message, errors=errors)


class SystemValidationException(ValidationException):
    """Exception raised when system data validation fails.
    
    Attributes:
        message: A human-readable error message.
        validation_errors: List of specific validation errors.
        system_name: The name of the system that failed validation.
        project_id: The project ID where the validation failed.
    """
    def __init__(
        self, 
        message: str = "System validation failed", 
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        system_name: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        detail = {"resource_type": "System"}
        if system_name:
            detail["system_name"] = system_name
        if project_id:
            detail["project_id"] = project_id
        
        super().__init__(message, errors=validation_errors)


class TeamValidationException(ValidationException):
    """Exception raised when team data validation fails.
    
    Attributes:
        message: A human-readable error message.
        validation_errors: List of specific validation errors.
        team_name: The name of the team that failed validation.
        project_id: The project ID where the validation failed.
    """
    def __init__(
        self, 
        message: str = "Team validation failed", 
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        team_name: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        detail = {"resource_type": "Team"}
        if team_name:
            detail["team_name"] = team_name
        if project_id:
            detail["project_id"] = project_id
        
        super().__init__(message, errors=validation_errors)


class SystemDependencyException(AppException):
    """Exception raised when there are issues with system dependencies.
    
    Attributes:
        message: A human-readable error message.
        system_name: The name of the system with dependency issues.
        dependent_systems: List of systems that depend on this system.
        project_id: The project ID where the issue occurred.
    """
    def __init__(
        self, 
        message: str = "System dependency error", 
        system_name: Optional[str] = None,
        dependent_systems: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        status_code: int = 400
    ):
        detail = {"resource_type": "System"}
        if system_name:
            detail["system_name"] = system_name
        if dependent_systems:
            detail["dependent_systems"] = dependent_systems
        if project_id:
            detail["project_id"] = project_id
        
        super().__init__(message, status_code=status_code, detail=detail)


class TeamMemberValidationException(ValidationException):
    """Exception raised when team member validation fails.
    
    Attributes:
        message: A human-readable error message.
        invalid_members: List of member names that are invalid.
        team_name: The name of the team with invalid members.
        project_id: The project ID where the validation failed.
    """
    def __init__(
        self, 
        message: str = "Team member validation failed", 
        invalid_members: Optional[List[str]] = None,
        team_name: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        detail = {"resource_type": "Team"}
        if invalid_members:
            detail["invalid_members"] = invalid_members
        if team_name:
            detail["team_name"] = team_name
        if project_id:
            detail["project_id"] = project_id
        
        errors = []
        if invalid_members:
            for member in invalid_members:
                errors.append({
                    "field": "members",
                    "message": f"Invalid member name: '{member}'",
                    "invalid_value": member
                })
        
        super().__init__(message, errors=errors)


class SystemOperationException(AppException):
    """Exception raised when system operations fail.
    
    Attributes:
        message: A human-readable error message.
        operation: The operation that failed (create, update, delete, etc.).
        system_name: The name of the system involved in the operation.
        project_id: The project ID where the operation failed.
    """
    def __init__(
        self, 
        message: str = "System operation failed", 
        operation: Optional[str] = None,
        system_name: Optional[str] = None,
        project_id: Optional[str] = None,
        status_code: int = 500
    ):
        detail = {"resource_type": "System"}
        if operation:
            detail["operation"] = operation
        if system_name:
            detail["system_name"] = system_name
        if project_id:
            detail["project_id"] = project_id
        
        super().__init__(message, status_code=status_code, detail=detail)


class TeamOperationException(AppException):
    """Exception raised when team operations fail.
    
    Attributes:
        message: A human-readable error message.
        operation: The operation that failed (create, update, delete, etc.).
        team_name: The name of the team involved in the operation.
        project_id: The project ID where the operation failed.
    """
    def __init__(
        self, 
        message: str = "Team operation failed", 
        operation: Optional[str] = None,
        team_name: Optional[str] = None,
        project_id: Optional[str] = None,
        status_code: int = 500
    ):
        detail = {"resource_type": "Team"}
        if operation:
            detail["operation"] = operation
        if team_name:
            detail["team_name"] = team_name
        if project_id:
            detail["project_id"] = project_id
        
        super().__init__(message, status_code=status_code, detail=detail)