"""Performance-optimized requirement document service."""

import asyncio
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.services.requirement_document_service import RequirementDocumentService
from app.services.langchain_pdf_processor import create_pdf_processor
from app.core.performance import (
    timing_decorator, 
    performance_context, 
    cache_manager, 
    PDFProcessingOptimizer,
    LLMProcessingOptimizer,
    performance_monitor
)
from app.models.requirement_document import RequirementDocument
from app.api.schemas.requirements import RequirementDocumentStatus, SourceType
from app.utils.pagination import PaginationParams, PaginatedResponse
from app.core.exceptions import NotFoundException, BadRequestException


class OptimizedRequirementDocumentService(RequirementDocumentService):
    """Performance-optimized version of RequirementDocumentService."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.processing_limits = PDFProcessingOptimizer.get_processing_limits()
        self.retry_strategy = LLMProcessingOptimizer.get_retry_strategy()
        # Override with enhanced LangChain processor
        self.pdf_processor = create_pdf_processor(use_langchain=True)
    
    @timing_decorator("upsert_requirements")
    def upsert_requirements(
        self,
        project_id: str,
        content: str,
        status: RequirementDocumentStatus = RequirementDocumentStatus.draft,
        source_type: SourceType = SourceType.manual,
        original_filename: Optional[str] = None
    ) -> RequirementDocument:
        """Optimized upsert with caching and validation."""
        # Validate project exists (with caching)
        cache_key = f"project_exists:{project_id}"
        project_exists = cache_manager.get(cache_key)
        
        if project_exists is None:
            project = self.project_repository.get_by_id(self.db, project_id)
            if not project:
                raise NotFoundException(f"Project not found: {project_id}")
            cache_manager.set(cache_key, True, ttl=300)  # Cache for 5 minutes
        elif not project_exists:
            raise NotFoundException(f"Project not found: {project_id}")
        
        # Validate content efficiently
        self._validate_content_optimized(content)
        
        # Clear related caches
        self._invalidate_project_caches(project_id)
        
        # Create document
        return super().upsert_requirements(project_id, content, status, source_type, original_filename)
    
    @timing_decorator("get_latest_requirements")
    def get_latest_requirements(self, project_id: str) -> RequirementDocument:
        """Optimized latest requirements retrieval with caching."""
        # Check cache first
        cache_key = f"latest_requirements:{project_id}"
        cached_result = cache_manager.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Validate project exists (with caching)
        cache_key_project = f"project_exists:{project_id}"
        project_exists = cache_manager.get(cache_key_project)
        
        if project_exists is None:
            project = self.project_repository.get_by_id(self.db, project_id)
            if not project:
                raise NotFoundException(f"Project not found: {project_id}")
            cache_manager.set(cache_key_project, True, ttl=300)
        elif not project_exists:
            raise NotFoundException(f"Project not found: {project_id}")
        
        # Get latest requirements
        result = super().get_latest_requirements(project_id)
        
        # Cache result (shorter TTL for frequently changing data)
        if result.id is not None:  # Don't cache empty documents
            cache_manager.set(cache_key, result, ttl=60)  # Cache for 1 minute
        
        return result
    
    @timing_decorator("get_requirements_versions")
    def get_requirements_versions(
        self,
        project_id: str,
        pagination: PaginationParams,
        status_filter: Optional[RequirementDocumentStatus] = None,
        source_type_filter: Optional[SourceType] = None
    ) -> PaginatedResponse:
        """Optimized version listing with caching."""
        # Create cache key based on all parameters
        cache_key = f"requirements_versions:{project_id}:{pagination.page}:{pagination.per_page}:{status_filter}:{source_type_filter}"
        cached_result = cache_manager.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Get results
        result = super().get_requirements_versions(project_id, pagination, status_filter, source_type_filter)
        
        # Cache results (shorter TTL for paginated data)
        cache_manager.set(cache_key, result, ttl=30)  # Cache for 30 seconds
        
        return result
    
    @timing_decorator("process_pdf_upload")
    async def process_pdf_upload(
        self,
        project_id: str,
        file: UploadFile,
        status: RequirementDocumentStatus = RequirementDocumentStatus.draft
    ) -> RequirementDocument:
        """Optimized PDF processing with timeout and resource limits."""
        # Validate project exists
        project = self.project_repository.get_by_id(self.db, project_id)
        if not project:
            raise NotFoundException(f"Project not found: {project_id}")
        
        # Check file size before processing
        if hasattr(file, 'size') and file.size:
            if file.size > self.processing_limits['max_file_size']:
                performance_monitor.record_counter('pdf_upload_rejected_size')
                raise BadRequestException(f"File too large: {file.size} bytes")
        
        performance_monitor.record_counter('pdf_upload_started')
        
        try:
            # Process PDF with timeout
            async with performance_context("pdf_text_extraction", {"filename": file.filename}):
                extracted_text = await PDFProcessingOptimizer.process_with_timeout(
                    self.pdf_processor.process_pdf_file(file),
                    timeout=self.processing_limits['timeout_seconds']
                )
            
            # Optimize text for LLM processing
            optimized_text = PDFProcessingOptimizer.optimize_text_extraction(extracted_text)
            
            # Convert to markdown with retry logic
            async with performance_context("llm_conversion", {"filename": file.filename}):
                converted_markdown = await self._convert_with_retry(optimized_text, file.filename)
            
            # Create requirements document
            async with performance_context("document_creation", {"filename": file.filename}):
                document = self.upsert_requirements(
                    project_id=project_id,
                    content=converted_markdown,
                    status=status,
                    source_type=SourceType.pdf_upload,
                    original_filename=file.filename
                )
            
            performance_monitor.record_counter('pdf_upload_completed')
            return document
            
        except asyncio.TimeoutError:
            performance_monitor.record_counter('pdf_upload_timeout')
            raise BadRequestException(f"PDF processing timed out after {self.processing_limits['timeout_seconds']} seconds")
        except Exception as e:
            performance_monitor.record_counter('pdf_upload_failed')
            raise
    
    async def _convert_with_retry(self, text: str, filename: str) -> str:
        """Convert PDF text to markdown with retry logic."""
        retry_config = self.retry_strategy
        last_exception = None
        
        for attempt in range(retry_config['max_retries']):
            try:
                # Optimize prompt size
                optimized_prompt = LLMProcessingOptimizer.optimize_prompt_size(text)
                
                # Attempt conversion
                result = await self.pdf_converter.convert_pdf_text_to_markdown(
                    optimized_prompt, filename
                )
                
                performance_monitor.record_counter('llm_conversion_success')
                return result
                
            except Exception as e:
                last_exception = e
                performance_monitor.record_counter('llm_conversion_retry')
                
                if attempt < retry_config['max_retries'] - 1:
                    # Calculate delay with exponential backoff
                    delay = min(
                        retry_config['base_delay'] * (retry_config['exponential_base'] ** attempt),
                        retry_config['max_delay']
                    )
                    
                    # Add jitter if enabled
                    if retry_config['jitter']:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    await asyncio.sleep(delay)
        
        # All retries failed
        performance_monitor.record_counter('llm_conversion_failed')
        raise last_exception
    
    def _validate_content_optimized(self, content: str) -> None:
        """Optimized content validation."""
        if not content or not content.strip():
            raise BadRequestException("Content cannot be empty")
        
        # Quick length check
        if len(content) > 100000:  # 100KB limit
            raise BadRequestException(f"Content too large: {len(content)} characters (max: 100000)")
        
        # Basic structure validation (optional)
        if len(content.strip()) < 10:
            raise BadRequestException("Content too short: minimum 10 characters required")
    
    def _invalidate_project_caches(self, project_id: str) -> None:
        """Invalidate all caches related to a project."""
        # Clear latest requirements cache
        cache_manager.delete(f"latest_requirements:{project_id}")
        
        # Clear version listing caches (this is approximate, in production you'd use cache tags)
        # For now, we'll just record that caches were invalidated
        performance_monitor.record_counter('cache_invalidated')
    
    @timing_decorator("get_requirements_summary")
    def get_requirements_summary(self, project_id: str) -> dict:
        """Optimized summary with caching."""
        cache_key = f"requirements_summary:{project_id}"
        cached_result = cache_manager.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Get summary
        result = super().get_requirements_summary(project_id)
        
        # Cache summary (longer TTL since it changes less frequently)
        cache_manager.set(cache_key, result, ttl=300)  # Cache for 5 minutes
        
        return result
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics for this service."""
        from app.core.performance import get_performance_report
        return get_performance_report()


class ConcurrentPDFProcessor:
    """Handle concurrent PDF processing with limits."""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_uploads = 0
    
    async def process_pdf(self, service: OptimizedRequirementDocumentService, project_id: str, file: UploadFile, status: RequirementDocumentStatus):
        """Process PDF with concurrency control."""
        async with self.semaphore:
            self.active_uploads += 1
            performance_monitor.record_counter('concurrent_pdf_processing', self.active_uploads)
            
            try:
                result = await service.process_pdf_upload(project_id, file, status)
                return result
            finally:
                self.active_uploads -= 1
    
    def get_status(self) -> dict:
        """Get current processing status."""
        return {
            'max_concurrent': self.max_concurrent,
            'active_uploads': self.active_uploads,
            'available_slots': self.max_concurrent - self.active_uploads
        }


# Global concurrent processor instance
concurrent_pdf_processor = ConcurrentPDFProcessor()