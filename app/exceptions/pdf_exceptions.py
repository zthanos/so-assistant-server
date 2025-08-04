"""PDF processing exceptions and error handling."""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class InvalidPDFError(PDFProcessingError):
    """Raised when PDF file is invalid or corrupted."""
    
    def __init__(self, message: str, filename: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.filename = filename
        error_details = details or {}
        if filename:
            error_details["filename"] = filename
        super().__init__(message, error_details)


class PDFTooLargeError(PDFProcessingError):
    """Raised when PDF file exceeds size limit."""
    
    def __init__(self, message: str, file_size: Optional[int] = None, max_size: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.file_size = file_size
        self.max_size = max_size
        error_details = details or {}
        if file_size:
            error_details["file_size"] = file_size
        if max_size:
            error_details["max_size"] = max_size
            error_details["max_size_mb"] = max_size // (1024 * 1024)
        super().__init__(message, error_details)


class TextExtractionError(PDFProcessingError):
    """Raised when text extraction from PDF fails."""
    
    def __init__(self, message: str, page_count: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.page_count = page_count
        error_details = details or {}
        if page_count is not None:
            error_details["page_count"] = page_count
        super().__init__(message, error_details)


class PDFValidationError(PDFProcessingError):
    """Raised when PDF validation fails."""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None, details: Optional[Dict[str, Any]] = None):
        self.validation_errors = validation_errors or []
        error_details = details or {}
        if validation_errors:
            error_details["validation_errors"] = validation_errors
        super().__init__(message, error_details)


def pdf_exception_to_http_exception(exc: PDFProcessingError) -> HTTPException:
    """Convert PDF processing exceptions to HTTP exceptions.
    
    Args:
        exc: The PDF processing exception to convert
        
    Returns:
        HTTPException with appropriate status code and details
    """
    error_response = {
        "error": exc.__class__.__name__.lower().replace("error", "_error"),
        "message": exc.message,
        "details": exc.details
    }
    
    if isinstance(exc, InvalidPDFError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response
        )
    elif isinstance(exc, PDFTooLargeError):
        return HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_response
        )
    elif isinstance(exc, TextExtractionError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response
        )
    elif isinstance(exc, PDFValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response
        )
    else:
        # Generic PDF processing error
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response
        )


def create_pdf_error_response(
    error_type: str,
    message: str,
    filename: Optional[str] = None,
    file_size: Optional[int] = None,
    additional_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized PDF error response.
    
    Args:
        error_type: Type of error (e.g., 'invalid_pdf', 'file_too_large')
        message: Human-readable error message
        filename: Name of the file that caused the error
        file_size: Size of the file in bytes
        additional_details: Additional error details
        
    Returns:
        Standardized error response dictionary
    """
    details = additional_details or {}
    
    if filename:
        details["filename"] = filename
    if file_size:
        details["file_size"] = file_size
        details["file_size_mb"] = round(file_size / (1024 * 1024), 2)
    
    return {
        "error": error_type,
        "message": message,
        "details": details,
        "timestamp": None  # Will be set by the API layer
    }


# Predefined error responses for common scenarios
COMMON_PDF_ERRORS = {
    "invalid_file_type": {
        "error": "invalid_file_type",
        "message": "Only PDF files are allowed for upload"
    },
    "file_too_large": {
        "error": "file_too_large", 
        "message": "File size exceeds the maximum allowed limit"
    },
    "corrupted_pdf": {
        "error": "corrupted_pdf",
        "message": "The PDF file appears to be corrupted or invalid"
    },
    "no_text_content": {
        "error": "no_text_content",
        "message": "No readable text content found in the PDF file"
    },
    "extraction_failed": {
        "error": "extraction_failed",
        "message": "Failed to extract text from the PDF file"
    },
    "processing_timeout": {
        "error": "processing_timeout",
        "message": "PDF processing timed out - file may be too complex"
    }
}


class LLMConversionError(PDFProcessingError):
    """Raised when LLM conversion fails."""
    
    def __init__(self, message: str, retry_count: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.retry_count = retry_count
        error_details = details or {}
        if retry_count is not None:
            error_details["retry_count"] = retry_count
        super().__init__(message, error_details)


class MarkdownValidationError(PDFProcessingError):
    """Raised when markdown validation fails."""
    
    def __init__(self, message: str, markdown_content: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.markdown_content = markdown_content
        error_details = details or {}
        if markdown_content:
            error_details["content_length"] = len(markdown_content)
        super().__init__(message, error_details)