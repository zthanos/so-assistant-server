"""LangChain-based PDF processor for enhanced text extraction and processing."""

import asyncio
import tempfile
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from fastapi import UploadFile

# LangChain imports
try:
    from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    Document = None

from app.exceptions.pdf_exceptions import (
    InvalidPDFError,
    PDFTooLargeError,
    TextExtractionError,
    PDFProcessingError
)
from app.core.performance import timing_decorator, performance_monitor


logger = logging.getLogger(__name__)


class LangChainPDFProcessor:
    """Enhanced PDF processor using LangChain for better text extraction and processing."""
    
    def __init__(self, max_file_size: int = 10 * 1024 * 1024):
        """Initialize the LangChain PDF processor.
        
        Args:
            max_file_size: Maximum file size in bytes (default: 10MB)
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not available. Install with: pip install langchain langchain-community unstructured"
            )
        
        self.max_file_size = max_file_size
        self.allowed_extensions = {'.pdf'}
        self.temp_dir = tempfile.gettempdir()
        
        # Configure text splitter for better chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def validate_pdf_file(self, file: UploadFile) -> None:
        """Validate PDF file format and size.
        
        Args:
            file: The uploaded file to validate
            
        Raises:
            InvalidPDFError: If file is not a valid PDF
            PDFTooLargeError: If file exceeds size limit
        """
        if not file.filename:
            raise InvalidPDFError("No filename provided")
        
        # Check file extension
        file_ext = self._get_file_extension(file.filename)
        if file_ext not in self.allowed_extensions:
            raise InvalidPDFError(
                f"Invalid file type: {file_ext}. Only PDF files are allowed.",
                filename=file.filename
            )
        
        # Check file size
        if hasattr(file, 'size') and file.size:
            if file.size > self.max_file_size:
                raise PDFTooLargeError(
                    f"File too large: {self._format_file_size(file.size)} exceeds limit of {self._format_file_size(self.max_file_size)}",
                    file_size=file.size,
                    max_size=self.max_file_size
                )
        
        # Check content type
        if hasattr(file, 'content_type') and file.content_type:
            if not file.content_type.startswith('application/pdf'):
                logger.warning(f"Unexpected content type: {file.content_type} for file {file.filename}")
    
    async def save_temp_file(self, file: UploadFile) -> str:
        """Save uploaded file to temporary location.
        
        Args:
            file: The uploaded file to save
            
        Returns:
            Path to the temporary file
            
        Raises:
            PDFProcessingError: If file saving fails
        """
        try:
            # Create temporary file with PDF extension
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f"_{file.filename}",
                dir=self.temp_dir
            )
            
            # Read and write file content
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to save temporary file: {e}")
            raise PDFProcessingError(f"Failed to save temporary file: {str(e)}")
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """Clean up temporary file.
        
        Args:
            file_path: Path to the temporary file to delete
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {file_path}: {e}")
    
    @timing_decorator("langchain_pdf_extraction")
    async def extract_text_with_langchain(self, file_path: str, loader_type: str = "pypdf") -> List[Document]:
        """Extract text from PDF using LangChain loaders.
        
        Args:
            file_path: Path to the PDF file
            loader_type: Type of loader to use ("pypdf" or "unstructured")
            
        Returns:
            List of LangChain Document objects
            
        Raises:
            TextExtractionError: If text extraction fails
        """
        try:
            # Choose loader based on type
            if loader_type == "unstructured":
                loader = UnstructuredPDFLoader(file_path)
            else:
                loader = PyPDFLoader(file_path)
            
            # Load documents
            documents = await asyncio.get_event_loop().run_in_executor(
                None, loader.load
            )
            
            if not documents:
                raise TextExtractionError("No content extracted from PDF")
            
            # Log extraction results
            total_chars = sum(len(doc.page_content) for doc in documents)
            performance_monitor.record_counter('pdf_pages_processed', len(documents))
            performance_monitor.record_counter('pdf_chars_extracted', total_chars)
            
            logger.info(f"Extracted {len(documents)} pages, {total_chars} characters from PDF")
            
            return documents
            
        except Exception as e:
            logger.error(f"LangChain text extraction failed: {e}")
            raise TextExtractionError(f"Failed to extract text from PDF: {str(e)}")
    
    @timing_decorator("langchain_text_processing")
    def process_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """Process extracted documents for better structure and metadata.
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            Dictionary with processed text and metadata
        """
        try:
            # Combine all page content
            full_text = "\n\n".join(doc.page_content for doc in documents)
            
            # Extract metadata
            metadata = {
                'total_pages': len(documents),
                'total_characters': len(full_text),
                'page_metadata': []
            }
            
            # Process each page's metadata
            for i, doc in enumerate(documents):
                page_meta = doc.metadata.copy()
                page_meta['page_number'] = i + 1
                page_meta['character_count'] = len(doc.page_content)
                metadata['page_metadata'].append(page_meta)
            
            # Split text into chunks for better processing
            text_chunks = self.text_splitter.split_text(full_text)
            
            # Clean and optimize text
            cleaned_text = self._clean_extracted_text(full_text)
            
            return {
                'full_text': cleaned_text,
                'text_chunks': text_chunks,
                'metadata': metadata,
                'page_count': len(documents),
                'chunk_count': len(text_chunks)
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise PDFProcessingError(f"Failed to process documents: {str(e)}")
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and optimize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned and optimized text
        """
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                cleaned_lines.append(line)
        
        # Join with single newlines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove control characters
        cleaned_text = ''.join(char for char in cleaned_text if ord(char) >= 32 or char in '\n\t')
        
        # Limit text length for processing
        max_length = 100000  # 100KB limit
        if len(cleaned_text) > max_length:
            cleaned_text = cleaned_text[:max_length] + "\n\n[Text truncated for processing]"
            performance_monitor.record_counter('pdf_text_truncated')
        
        return cleaned_text
    
    @timing_decorator("langchain_pdf_processing")
    async def process_pdf_file(self, file: UploadFile, loader_type: str = "pypdf") -> Dict[str, Any]:
        """Process PDF file using LangChain with enhanced features.
        
        Args:
            file: The uploaded PDF file
            loader_type: Type of loader to use ("pypdf" or "unstructured")
            
        Returns:
            Dictionary with extracted text and metadata
            
        Raises:
            InvalidPDFError: If file validation fails
            PDFTooLargeError: If file is too large
            TextExtractionError: If text extraction fails
        """
        # Validate file
        self.validate_pdf_file(file)
        
        temp_file_path = None
        try:
            # Save file temporarily
            temp_file_path = await self.save_temp_file(file)
            
            # Extract text using LangChain
            documents = await self.extract_text_with_langchain(temp_file_path, loader_type)
            
            # Process documents
            result = self.process_documents(documents)
            
            # Add file information
            result['original_filename'] = file.filename
            result['file_size'] = getattr(file, 'size', 0)
            result['loader_type'] = loader_type
            
            performance_monitor.record_counter('pdf_processing_success')
            
            return result
            
        except (InvalidPDFError, PDFTooLargeError, TextExtractionError):
            performance_monitor.record_counter('pdf_processing_failed')
            raise
        except Exception as e:
            performance_monitor.record_counter('pdf_processing_error')
            logger.error(f"PDF processing failed: {e}")
            raise PDFProcessingError(f"PDF processing failed: {str(e)}")
        finally:
            # Clean up temporary file
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path)
    
    async def extract_text_simple(self, file: UploadFile) -> str:
        """Simple text extraction for backward compatibility.
        
        Args:
            file: The uploaded PDF file
            
        Returns:
            Extracted text as string
        """
        result = await self.process_pdf_file(file)
        return result['full_text']
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension in lowercase.
        
        Args:
            filename: Name of the file
            
        Returns:
            File extension in lowercase
        """
        if not filename:
            return ""
        return Path(filename).suffix.lower()
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'max_file_size': self.max_file_size,
            'max_file_size_mb': self.max_file_size / (1024 * 1024),
            'allowed_extensions': list(self.allowed_extensions),
            'text_splitter_config': {
                'chunk_size': self.text_splitter._chunk_size,
                'chunk_overlap': self.text_splitter._chunk_overlap
            },
            'langchain_available': LANGCHAIN_AVAILABLE
        }


class EnhancedPDFProcessor:
    """Enhanced PDF processor that can use either LangChain or PyMuPDF."""
    
    def __init__(self, prefer_langchain: bool = True):
        """Initialize enhanced PDF processor.
        
        Args:
            prefer_langchain: Whether to prefer LangChain over PyMuPDF
        """
        self.prefer_langchain = prefer_langchain and LANGCHAIN_AVAILABLE
        
        if self.prefer_langchain:
            self.processor = LangChainPDFProcessor()
            logger.info("Using LangChain PDF processor")
        else:
            # Fallback to original processor
            from app.services.pdf_processor import PDFProcessor
            self.processor = PDFProcessor()
            logger.info("Using PyMuPDF PDF processor")
    
    async def process_pdf_file(self, file: UploadFile) -> str:
        """Process PDF file and return extracted text.
        
        Args:
            file: The uploaded PDF file
            
        Returns:
            Extracted text as string
        """
        if self.prefer_langchain:
            # Use LangChain processor
            result = await self.processor.process_pdf_file(file)
            return result['full_text']
        else:
            # Use original processor
            return await self.processor.process_uploaded_pdf(file)
    
    async def process_pdf_file_enhanced(self, file: UploadFile) -> Dict[str, Any]:
        """Process PDF file with enhanced features (only available with LangChain).
        
        Args:
            file: The uploaded PDF file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if self.prefer_langchain:
            return await self.processor.process_pdf_file(file)
        else:
            # Fallback to simple processing
            text = await self.processor.process_uploaded_pdf(file)
            return {
                'full_text': text,
                'text_chunks': [text],
                'metadata': {
                    'total_pages': 1,
                    'total_characters': len(text)
                },
                'original_filename': file.filename,
                'file_size': getattr(file, 'size', 0),
                'loader_type': 'pymupdf'
            }
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about the current processor.
        
        Returns:
            Dictionary with processor information
        """
        return {
            'processor_type': 'langchain' if self.prefer_langchain else 'pymupdf',
            'langchain_available': LANGCHAIN_AVAILABLE,
            'features': {
                'basic_text_extraction': True,
                'enhanced_metadata': self.prefer_langchain,
                'text_chunking': self.prefer_langchain,
                'multiple_loaders': self.prefer_langchain
            }
        }


# Factory function for easy integration
def create_pdf_processor(use_langchain: bool = True) -> EnhancedPDFProcessor:
    """Create a PDF processor instance.
    
    Args:
        use_langchain: Whether to use LangChain if available
        
    Returns:
        Enhanced PDF processor instance
    """
    return EnhancedPDFProcessor(prefer_langchain=use_langchain)