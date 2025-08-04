"""PDF processing utilities for requirements document upload."""

import os
import tempfile
import logging
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None

from app.exceptions.pdf_exceptions import (
    PDFProcessingError,
    InvalidPDFError,
    PDFTooLargeError,
    TextExtractionError,
    PDFValidationError
)

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF file processing and text extraction."""
    
    def __init__(self):
        """Initialize PDF processor with configuration."""
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {'.pdf'}
        self.temp_dir = tempfile.gettempdir()
        
    def validate_pdf_file(self, file: UploadFile) -> None:
        """Validate PDF file format and size.
        
        Args:
            file: The uploaded file to validate
            
        Raises:
            InvalidPDFError: If file is not a valid PDF
            PDFTooLargeError: If file exceeds size limit
            PDFValidationError: If multiple validation errors occur
        """
        validation_errors = []
        
        # Check filename
        if not file.filename:
            validation_errors.append("No filename provided")
        else:
            # Check file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in self.allowed_extensions:
                validation_errors.append(
                    f"Invalid file type: {file_ext}. Only PDF files are allowed."
                )
        
        # Check content type
        if file.content_type and not file.content_type.startswith('application/pdf'):
            validation_errors.append(
                f"Invalid content type: {file.content_type}. Expected application/pdf."
            )
        
        # Check file size
        file_size = getattr(file, 'size', None)
        if file_size and file_size > self.max_file_size:
            raise PDFTooLargeError(
                f"File size {file_size} bytes exceeds maximum allowed size "
                f"{self.max_file_size} bytes ({self.max_file_size // (1024*1024)}MB)",
                file_size=file_size,
                max_size=self.max_file_size,
                details={
                    "filename": file.filename,
                    "content_type": file.content_type
                }
            )
        
        # If there are validation errors, raise them
        if validation_errors:
            if len(validation_errors) == 1:
                raise InvalidPDFError(
                    validation_errors[0],
                    filename=file.filename,
                    details={
                        "content_type": file.content_type,
                        "file_size": file_size
                    }
                )
            else:
                raise PDFValidationError(
                    f"Multiple validation errors: {'; '.join(validation_errors)}",
                    validation_errors=validation_errors,
                    details={
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "file_size": file_size
                    }
                )
        
        logger.info(f"PDF file validation passed: {file.filename}")
    
    async def save_temp_file(self, file: UploadFile) -> str:
        """Save uploaded file temporarily for processing.
        
        Args:
            file: The uploaded file to save
            
        Returns:
            Path to the temporary file
            
        Raises:
            PDFProcessingError: If file cannot be saved
        """
        try:
            # Create a temporary file with PDF extension
            temp_fd, temp_path = tempfile.mkstemp(
                suffix='.pdf',
                prefix='req_upload_',
                dir=self.temp_dir
            )
            
            # Write file content to temporary file
            content = await file.read()
            with os.fdopen(temp_fd, 'wb') as temp_file:
                temp_file.write(content)
            
            # Reset file position for potential reuse
            await file.seek(0)
            
            logger.info(f"Saved temporary file: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to save temporary file: {e}")
            raise PDFProcessingError(f"Failed to save uploaded file: {str(e)}")
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """Clean up temporary files after processing.
        
        Args:
            file_path: Path to the temporary file to delete
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {file_path}: {e}")
    
    async def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text content from PDF file.
        
        Args:
            file_content: Raw bytes of the PDF file
            
        Returns:
            Extracted text content from all pages
            
        Raises:
            TextExtractionError: If text extraction fails
            InvalidPDFError: If PDF is corrupted or invalid
        """
        temp_path = None
        try:
            # Save content to temporary file for PyMuPDF processing
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='pdf_extract_')
            with os.fdopen(temp_fd, 'wb') as temp_file:
                temp_file.write(file_content)
            
            # Open PDF document
            try:
                doc = fitz.open(temp_path)
            except Exception as e:
                raise InvalidPDFError(
                    f"Cannot open PDF file: {str(e)}",
                    details={"error_type": "pdf_open_failed", "original_error": str(e)}
                )
            
            # Extract text from all pages
            extracted_text = ""
            page_count = len(doc)
            failed_pages = []
            
            if page_count == 0:
                doc.close()
                raise InvalidPDFError(
                    "PDF file contains no pages",
                    details={"page_count": 0}
                )
            
            logger.info(f"Extracting text from {page_count} pages")
            
            for page_num in range(page_count):
                try:
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    
                    if page_text.strip():
                        extracted_text += f"\n--- Page {page_num + 1} ---\n"
                        extracted_text += page_text
                        extracted_text += "\n"
                    
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    failed_pages.append({
                        "page": page_num + 1,
                        "error": str(e)
                    })
                    continue
            
            doc.close()
            
            if not extracted_text.strip():
                raise TextExtractionError(
                    "No text content found in PDF",
                    page_count=page_count,
                    details={
                        "failed_pages": failed_pages,
                        "total_pages": page_count,
                        "extraction_method": "pymupdf"
                    }
                )
            
            # Log warnings if some pages failed
            if failed_pages:
                logger.warning(f"Failed to extract text from {len(failed_pages)} out of {page_count} pages")
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
            return extracted_text.strip()
            
        except (InvalidPDFError, TextExtractionError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during text extraction: {e}")
            raise TextExtractionError(f"Failed to extract text from PDF: {str(e)}")
        finally:
            # Clean up temporary file
            if temp_path:
                self.cleanup_temp_file(temp_path)
    
    async def process_uploaded_pdf(self, file: UploadFile) -> str:
        """Process uploaded PDF file and extract text.
        
        This is a convenience method that combines validation and text extraction.
        
        Args:
            file: The uploaded PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            InvalidPDFError: If file is invalid
            PDFTooLargeError: If file is too large
            TextExtractionError: If text extraction fails
        """
        # Validate the file
        self.validate_pdf_file(file)
        
        # Read file content
        content = await file.read()
        
        # Reset file position
        await file.seek(0)
        
        # Extract text
        return await self.extract_text_from_pdf(content)
    
    def get_file_info(self, file: UploadFile) -> dict:
        """Get information about the uploaded file.
        
        Args:
            file: The uploaded file
            
        Returns:
            Dictionary with file information
        """
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": getattr(file, 'size', None),
            "max_allowed_size": self.max_file_size,
            "max_allowed_size_mb": self.max_file_size // (1024 * 1024)
        }