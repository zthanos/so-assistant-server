"""Requirement items specific exceptions."""

from app.core.exceptions import AppException, BadRequestException, NotFoundException


class RequirementItemException(AppException):
    """Base exception for requirement item operations."""
    pass


class RequirementItemNotFound(NotFoundException):
    """Exception raised when a requirement item is not found."""
    
    def __init__(self, item_id: int):
        super().__init__(
            f"Requirement item with id {item_id} not found",
            resource_type="RequirementItem",
            resource_id=item_id
        )


class RequirementItemValidationError(BadRequestException):
    """Exception raised when requirement item data validation fails."""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field


class RequirementItemStatusTransitionError(BadRequestException):
    """Exception raised when an invalid status transition is attempted."""
    
    def __init__(self, current_status: str, new_status: str):
        message = f"Invalid status transition from {current_status} to {new_status}"
        super().__init__(message)
        self.current_status = current_status
        self.new_status = new_status


class RequirementItemBulkOperationError(BadRequestException):
    """Exception raised when bulk operations fail."""
    
    def __init__(self, message: str, failed_items: list = None):
        super().__init__(message)
        self.failed_items = failed_items or []


class RequirementSuggestionError(AppException):
    """Exception raised when requirement suggestion generation fails."""
    
    def __init__(self, message: str, project_id: str = None):
        super().__init__(message)
        self.project_id = project_id


class RequirementSuggestionParsingError(RequirementSuggestionError):
    """Exception raised when LLM response parsing fails."""
    
    def __init__(self, message: str, raw_response: str = None):
        super().__init__(message)
        self.raw_response = raw_response


class RequirementSuggestionStreamingError(RequirementSuggestionError):
    """Exception raised when SSE streaming fails during suggestion generation."""
    
    def __init__(self, message: str, client_id: str = None):
        super().__init__(message)
        self.client_id = client_id