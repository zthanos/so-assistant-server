"""Comprehensive error handling for agent operations."""
import asyncio
import logging
import time
import traceback
from typing import Any, Dict, Optional, Callable
from functools import wraps

from app.core.exceptions import LLMException, NotFoundException, ValidationException
from app.services.agent.config import agent_config

logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Base exception for agent-related errors."""
    
    def __init__(self, message: str, error_code: str = "AGENT_ERROR", 
                 original_exception: Optional[Exception] = None):
        """Initialize agent error."""
        self.message = message
        self.error_code = error_code
        self.original_exception = original_exception
        super().__init__(self.message)


class IntentDetectionError(AgentError):
    """Error in intent detection."""
    
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message, "INTENT_DETECTION_ERROR", original_exception)


class ContextAssemblyError(AgentError):
    """Error in context assembly."""
    
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message, "CONTEXT_ASSEMBLY_ERROR", original_exception)


class AnalysisError(AgentError):
    """Error in analysis execution."""
    
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message, "ANALYSIS_ERROR", original_exception)


class TimeoutError(AgentError):
    """Timeout error."""
    
    def __init__(self, message: str, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, "TIMEOUT_ERROR")


class ErrorHandler:
    """Centralized error handler for agent operations."""
    
    @staticmethod
    def handle_agent_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent errors and return structured error response."""
        
        error_response = {
            "error": True,
            "error_type": type(error).__name__,
            "message": str(error),
            "context": context,
            "timestamp": time.time()
        }
        
        # Add specific error details based on error type
        if isinstance(error, AgentError):
            error_response["error_code"] = error.error_code
            if error.original_exception:
                error_response["original_error"] = str(error.original_exception)
        
        elif isinstance(error, LLMException):
            error_response["error_code"] = "LLM_ERROR"
            error_response["llm_related"] = True
        
        elif isinstance(error, NotFoundException):
            error_response["error_code"] = "NOT_FOUND"
            error_response["resource_type"] = getattr(error, 'resource_type', 'unknown')
        
        elif isinstance(error, ValidationException):
            error_response["error_code"] = "VALIDATION_ERROR"
            error_response["validation_details"] = getattr(error, 'details', None)
        
        elif isinstance(error, asyncio.TimeoutError):
            error_response["error_code"] = "TIMEOUT_ERROR"
            error_response["timeout_related"] = True
        
        else:
            error_response["error_code"] = "UNKNOWN_ERROR"
        
        # Log the error
        logger.error(f"Agent error: {error_response}")
        
        return error_response
    
    @staticmethod
    def create_user_friendly_message(error: Exception, context: Dict[str, Any]) -> str:
        """Create user-friendly error message."""
        
        if isinstance(error, IntentDetectionError):
            return "I'm having trouble understanding your request. Could you please rephrase it?"
        
        elif isinstance(error, ContextAssemblyError):
            return "I couldn't find enough information in your project to answer this question."
        
        elif isinstance(error, AnalysisError):
            return "I encountered an issue while analyzing your request. Please try again."
        
        elif isinstance(error, TimeoutError):
            return f"The analysis is taking longer than expected (>{error.timeout_seconds}s). Please try again."
        
        elif isinstance(error, LLMException):
            return "I'm experiencing technical difficulties with the language model. Please try again in a moment."
        
        elif isinstance(error, NotFoundException):
            resource_type = getattr(error, 'resource_type', 'resource')
            return f"The requested {resource_type} was not found in your project."
        
        else:
            return "I encountered an unexpected error. Please try again or contact support if the issue persists."


def with_error_handling(
    error_type: type = AgentError,
    fallback_result: Any = None,
    log_errors: bool = True
):
    """Decorator for adding error handling to agent methods."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                
                # Re-raise as specified error type if not already
                if not isinstance(e, error_type):
                    raise error_type(f"Error in {func.__name__}: {str(e)}", original_exception=e)
                else:
                    raise e
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                
                # Re-raise as specified error type if not already
                if not isinstance(e, error_type):
                    raise error_type(f"Error in {func.__name__}: {str(e)}", original_exception=e)
                else:
                    raise e
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def with_timeout(
    coro,
    timeout_seconds: int,
    error_message: str = "Operation timed out"
) -> Any:
    """Execute coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"{error_message} after {timeout_seconds} seconds", timeout_seconds)


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """Initialize circuit breaker."""
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise AgentError("Circuit breaker is open - service temporarily unavailable")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset failure count
            if self.state == "half-open":
                self.state = "closed"
            self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise e


class RetryManager:
    """Advanced retry manager with exponential backoff."""
    
    @staticmethod
    async def retry_with_backoff(
        func: Callable,
        max_retries: int = None,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """Retry function with exponential backoff."""
        
        max_retries = max_retries or agent_config.max_retries
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
                    
            except exceptions as e:
                last_exception = e
                
                if attempt == max_retries:
                    break
                
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}, retrying in {delay}s")
                await asyncio.sleep(delay)
                
                # Exponential backoff
                delay = min(delay * backoff_multiplier, max_delay)
        
        # All retries failed
        raise AgentError(
            f"Operation failed after {max_retries + 1} attempts",
            original_exception=last_exception
        )


class GracefulDegradation:
    """Graceful degradation strategies for agent operations."""
    
    @staticmethod
    def get_fallback_intent() -> Dict[str, Any]:
        """Get fallback intent when detection fails."""
        return {
            "intent": "qna",
            "targets": {"so_ids": [], "requirement_ids": [], "diagram_ids": []},
            "confidence": 0.1,
            "reason": "Fallback to Q&A due to intent detection failure"
        }
    
    @staticmethod
    def get_minimal_context(project_id: str) -> Dict[str, Any]:
        """Get minimal context when full assembly fails."""
        return {
            "so_sections": [],
            "requirements": [],
            "diagrams": [],
            "chat_summary": "",
            "metadata": {
                "project_id": project_id,
                "degraded": True,
                "reason": "Context assembly failed - using minimal context"
            }
        }
    
    @staticmethod
    def get_insufficient_response() -> Dict[str, Any]:
        """Get response for insufficient context."""
        return {
            "suggestions": [],
            "scores": {
                "integration_consistency": 0.0,
                "requirements_coverage": 0.0,
                "security_readiness": 0.0,
                "operability": 0.0
            },
            "status": "insufficient"
        }


# Global instances
error_handler = ErrorHandler()
circuit_breaker = CircuitBreaker()
retry_manager = RetryManager()
graceful_degradation = GracefulDegradation()