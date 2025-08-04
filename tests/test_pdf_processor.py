"""Unit tests for PDF processing components."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from fastapi import UploadFile
import io

from app.services.pdf_processor import PDFProcessor
from app.exceptions.pdf_exceptions import (
    InvalidPDFError,
    PDFTooLargeError,
    TextExtractionError,
    PDFProcessingError
)


class TestPDFProcessor:
    """Test cases for PDFProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pdf_processor = PDFProcessor()

    def test_init_sets_correct_defaults(self):
        """Test that PDFProcessor initializes with correct default values."""
        assert self.pdf_processor.max_file_size == 10 * 1024 * 1024  # 10MB
        assert self.pdf_processor.allowed_extensions == {'.pdf'}
        assert self.pdf_processor.temp_dir is not None

    def test_validate_pdf_file_valid_pdf(self):
        """Test validation passes for valid PDF file."""
        # Create mock UploadFile
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.size = 1024 * 1024  # 1MB
        mock_file.content_type = "application/pdf"

        # Should not raise any exception
        self.pdf_processor.validate_pdf_file(mock_file)

    def test_validate_pdf_file_invalid_extension(self):
        """Test validation fails for non-PDF file."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.size = 1024
        mock_file.content_type = "text/plain"

        with pytest.raises(InvalidPDFError) as exc_info:
            self.pdf_processor.validate_pdf_file(mock_file)
        
        assert "Invalid file type" in str(exc_info.value)
        assert "test.txt" in str(exc_info.value)

    def test_validate_pdf_file_no_extension(self):
        """Test validation fails for file without extension."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test"
        mock_file.size = 1024
        mock_file.content_type = "application/pdf"

        with pytest.raises(InvalidPDFError) as exc_info:
            self.pdf_processor.validate_pdf_file(mock_file)
        
        assert "Invalid file type" in str(exc_info.value)

    def test_validate_pdf_file_too_large(self):
        """Test validation fails for oversized file."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.size = 15 * 1024 * 1024  # 15MB (over 10MB limit)
        mock_file.content_type = "application/pdf"

        with pytest.raises(PDFTooLargeError) as exc_info:
            self.pdf_processor.validate_pdf_file(mock_file)
        
        assert "File too large" in str(exc_info.value)
        assert "15.0 MB" in str(exc_info.value)
        assert "10.0 MB" in str(exc_info.value)

    def test_validate_pdf_file_no_filename(self):
        """Test validation fails for file without filename."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None
        mock_file.size = 1024
        mock_file.content_type = "application/pdf"

        with pytest.raises(InvalidPDFError) as exc_info:
            self.pdf_processor.validate_pdf_file(mock_file)
        
        assert "No filename provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_save_temp_file_success(self):
        """Test successful temporary file saving."""
        # Create mock file content
        file_content = b"PDF file content"
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.read = Mock(return_value=file_content)

        # Save temp file
        temp_path = await self.pdf_processor.save_temp_file(mock_file)

        # Verify file was created and contains correct content
        assert os.path.exists(temp_path)
        assert temp_path.endswith("test.pdf")
        
        with open(temp_path, 'rb') as f:
            saved_content = f.read()
        
        assert saved_content == file_content

        # Clean up
        os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_save_temp_file_read_error(self):
        """Test error handling when file read fails."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.read = Mock(side_effect=Exception("Read failed"))

        with pytest.raises(PDFProcessingError) as exc_info:
            await self.pdf_processor.save_temp_file(mock_file)
        
        assert "Failed to save temporary file" in str(exc_info.value)

    def test_cleanup_temp_file_success(self):
        """Test successful temporary file cleanup."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")

        # Verify file exists
        assert os.path.exists(temp_path)

        # Clean up file
        self.pdf_processor.cleanup_temp_file(temp_path)

        # Verify file is deleted
        assert not os.path.exists(temp_path)

    def test_cleanup_temp_file_nonexistent(self):
        """Test cleanup handles non-existent files gracefully."""
        nonexistent_path = "/path/that/does/not/exist.pdf"
        
        # Should not raise exception
        self.pdf_processor.cleanup_temp_file(nonexistent_path)

    @pytest.mark.asyncio
    @patch('fitz.open')
    async def test_extract_text_from_pdf_success(self, mock_fitz_open):
        """Test successful text extraction from PDF."""
        # Mock PyMuPDF document
        mock_page = Mock()
        mock_page.get_text.return_value = "Page 1 content\n"
        
        mock_doc = Mock()
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1
        
        mock_fitz_open.return_value = mock_doc

        # Test text extraction
        pdf_content = b"fake pdf content"
        extracted_text = await self.pdf_processor.extract_text_from_pdf(pdf_content)

        # Verify results
        assert extracted_text == "Page 1 content\n"
        mock_fitz_open.assert_called_once()
        mock_page.get_text.assert_called_once()

    @pytest.mark.asyncio
    @patch('fitz.open')
    async def test_extract_text_from_pdf_multiple_pages(self, mock_fitz_open):
        """Test text extraction from multi-page PDF."""
        # Mock multiple pages
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1 content\n"
        
        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2 content\n"
        
        mock_doc = Mock()
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_doc.__iter__.return_value = [mock_page1, mock_page2]
        mock_doc.__len__.return_value = 2
        
        mock_fitz_open.return_value = mock_doc

        # Test text extraction
        pdf_content = b"fake pdf content"
        extracted_text = await self.pdf_processor.extract_text_from_pdf(pdf_content)

        # Verify results
        expected_text = "Page 1 content\nPage 2 content\n"
        assert extracted_text == expected_text

    @pytest.mark.asyncio
    @patch('fitz.open')
    async def test_extract_text_from_pdf_empty_pages(self, mock_fitz_open):
        """Test text extraction from PDF with empty pages."""
        # Mock empty pages
        mock_page1 = Mock()
        mock_page1.get_text.return_value = ""
        
        mock_page2 = Mock()
        mock_page2.get_text.return_value = "   \n  \n"  # Whitespace only
        
        mock_page3 = Mock()
        mock_page3.get_text.return_value = "Actual content\n"
        
        mock_doc = Mock()
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_doc.__iter__.return_value = [mock_page1, mock_page2, mock_page3]
        mock_doc.__len__.return_value = 3
        
        mock_fitz_open.return_value = mock_doc

        # Test text extraction
        pdf_content = b"fake pdf content"
        extracted_text = await self.pdf_processor.extract_text_from_pdf(pdf_content)

        # Should only include non-empty content
        assert extracted_text == "Actual content\n"

    @pytest.mark.asyncio
    @patch('fitz.open')
    async def test_extract_text_from_pdf_corrupted_file(self, mock_fitz_open):
        """Test error handling for corrupted PDF file."""
        mock_fitz_open.side_effect = Exception("Invalid PDF")

        pdf_content = b"corrupted pdf content"
        
        with pytest.raises(TextExtractionError) as exc_info:
            await self.pdf_processor.extract_text_from_pdf(pdf_content)
        
        assert "Failed to extract text from PDF" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('fitz.open')
    async def test_extract_text_from_pdf_no_text(self, mock_fitz_open):
        """Test handling of PDF with no extractable text."""
        # Mock pages with no text
        mock_page = Mock()
        mock_page.get_text.return_value = ""
        
        mock_doc = Mock()
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1
        
        mock_fitz_open.return_value = mock_doc

        pdf_content = b"pdf with no text"
        
        with pytest.raises(TextExtractionError) as exc_info:
            await self.pdf_processor.extract_text_from_pdf(pdf_content)
        
        assert "No text content found in PDF" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_pdf_file_complete_workflow(self):
        """Test complete PDF processing workflow."""
        # Create mock file
        file_content = b"fake pdf content"
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.size = 1024
        mock_file.content_type = "application/pdf"
        mock_file.read = Mock(return_value=file_content)

        # Mock text extraction
        with patch.object(self.pdf_processor, 'extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = "Extracted PDF text content"
            
            # Process PDF file
            result = await self.pdf_processor.process_pdf_file(mock_file)

            # Verify results
            assert result == "Extracted PDF text content"
            mock_extract.assert_called_once_with(file_content)

    @pytest.mark.asyncio
    async def test_process_pdf_file_validation_error(self):
        """Test PDF processing with validation error."""
        # Create invalid mock file
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"  # Invalid extension
        mock_file.size = 1024
        mock_file.content_type = "text/plain"

        with pytest.raises(InvalidPDFError):
            await self.pdf_processor.process_pdf_file(mock_file)

    @pytest.mark.asyncio
    async def test_process_pdf_file_extraction_error(self):
        """Test PDF processing with text extraction error."""
        # Create valid mock file
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.size = 1024
        mock_file.content_type = "application/pdf"
        mock_file.read = Mock(return_value=b"fake pdf content")

        # Mock extraction failure
        with patch.object(self.pdf_processor, 'extract_text_from_pdf') as mock_extract:
            mock_extract.side_effect = TextExtractionError("Extraction failed")
            
            with pytest.raises(TextExtractionError):
                await self.pdf_processor.process_pdf_file(mock_file)

    def test_get_file_extension(self):
        """Test file extension extraction."""
        assert self.pdf_processor._get_file_extension("test.pdf") == ".pdf"
        assert self.pdf_processor._get_file_extension("document.PDF") == ".pdf"
        assert self.pdf_processor._get_file_extension("file.txt") == ".txt"
        assert self.pdf_processor._get_file_extension("noextension") == ""
        assert self.pdf_processor._get_file_extension("") == ""
        assert self.pdf_processor._get_file_extension(None) == ""

    def test_format_file_size(self):
        """Test file size formatting."""
        assert self.pdf_processor._format_file_size(1024) == "1.0 KB"
        assert self.pdf_processor._format_file_size(1024 * 1024) == "1.0 MB"
        assert self.pdf_processor._format_file_size(1536) == "1.5 KB"
        assert self.pdf_processor._format_file_size(0) == "0.0 B"
        assert self.pdf_processor._format_file_size(512) == "512.0 B"


class TestPDFProcessorIntegration:
    """Integration tests for PDF processor with real file operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pdf_processor = PDFProcessor()

    @pytest.mark.asyncio
    async def test_temp_file_lifecycle(self):
        """Test complete temporary file lifecycle."""
        # Create mock file
        file_content = b"test pdf content"
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "integration_test.pdf"
        mock_file.read = Mock(return_value=file_content)

        # Save temp file
        temp_path = await self.pdf_processor.save_temp_file(mock_file)
        
        try:
            # Verify file exists and has correct content
            assert os.path.exists(temp_path)
            with open(temp_path, 'rb') as f:
                saved_content = f.read()
            assert saved_content == file_content
            
        finally:
            # Clean up
            self.pdf_processor.cleanup_temp_file(temp_path)
            assert not os.path.exists(temp_path)

    def test_concurrent_temp_files(self):
        """Test handling of multiple temporary files."""
        temp_paths = []
        
        try:
            # Create multiple temp files
            for i in range(3):
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_test_{i}.pdf") as temp_file:
                    temp_file.write(f"content {i}".encode())
                    temp_paths.append(temp_file.name)
            
            # Verify all files exist
            for path in temp_paths:
                assert os.path.exists(path)
            
            # Clean up all files
            for path in temp_paths:
                self.pdf_processor.cleanup_temp_file(path)
            
            # Verify all files are deleted
            for path in temp_paths:
                assert not os.path.exists(path)
                
        finally:
            # Ensure cleanup even if test fails
            for path in temp_paths:
                if os.path.exists(path):
                    os.unlink(path)


# Test fixtures and utilities
@pytest.fixture
def sample_pdf_content():
    """Fixture providing sample PDF content."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"

@pytest.fixture
def mock_upload_file():
    """Fixture providing mock UploadFile."""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    mock_file.size = 1024
    mock_file.content_type = "application/pdf"
    return mock_file

@pytest.fixture
def pdf_processor():
    """Fixture providing PDFProcessor instance."""
    return PDFProcessor()