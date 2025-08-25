"""SSE event models and schemas."""
import time
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

from app.api.schemas.assistant import (
    AssistantIntent, SuggestionType, SuggestionSeverity, AnalysisStatus,
    StructuredAnalysisResponse
)


class SSEEventType(str, Enum):
    """SSE event types for agent streaming."""
    START = "start"
    TOKEN = "token"
    JSON = "json"
    FINAL = "final"
    ERROR = "error"
    PROGRESS = "progress"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    LLM_START = "llm_start"
    LLM_END = "llm_end"
    HEARTBEAT = "heartbeat"


class BaseSSEEvent(BaseModel):
    """Base SSE event model."""
    
    event_type: SSEEventType = Field(..., description="Event type")
    request_id: Optional[str] = Field(None, description="Request ID")
    timestamp: float = Field(default_factory=time.time, description="Event timestamp")
    
    class Config:
        """Pydantic config."""
        use_enum_values = True


class SSEStartEventData(BaseModel):
    """SSE start event data."""
    
    intent: AssistantIntent = Field(..., description="Detected intent")
    targets: Dict[str, List[str]] = Field(..., description="Target IDs")
    project_id: str = Field(..., description="Project ID")
    confidence: Optional[float] = Field(None, description="Intent confidence")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "intent": "requirements_coverage",
                "targets": {
                    "so_ids": ["SEC-2.1"],
                    "requirement_ids": ["REQ-12"],
                    "diagram_ids": []
                },
                "project_id": "proj-123",
                "confidence": 0.85
            }
        }


class SSETokenEventData(BaseModel):
    """SSE token event data."""
    
    delta: str = Field(..., description="Token content")
    total_tokens: Optional[int] = Field(None, description="Total tokens so far")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "delta": "The analysis shows",
                "total_tokens": 15
            }
        }


class SSEJsonEventData(BaseModel):
    """SSE JSON event data."""
    
    partial: Dict[str, Any] = Field(..., description="Partial JSON data")
    chunk_index: Optional[int] = Field(None, description="Chunk index")
    is_final_chunk: Optional[bool] = Field(None, description="Is final chunk")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "partial": {"suggestions": []},
                "chunk_index": 0,
                "is_final_chunk": False
            }
        }


class SSEProgressEventData(BaseModel):
    """SSE progress event data."""
    
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress (0.0-1.0)")
    status: str = Field(..., description="Current status")
    stage: Optional[str] = Field(None, description="Current stage")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "progress": 0.5,
                "status": "Analyzing requirements coverage",
                "stage": "analysis"
            }
        }


class SSEToolEventData(BaseModel):
    """SSE tool execution event data."""
    
    tool_name: str = Field(..., description="Tool name")
    status: str = Field(..., description="Tool status (started/completed/failed)")
    tool_input: Optional[Dict[str, Any]] = Field(None, description="Tool input")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "tool_name": "intent_router",
                "status": "completed",
                "execution_time": 1.2
            }
        }


class SSEExecutionMetrics(BaseModel):
    """Execution metrics for SSE events."""
    
    execution_time_ms: int = Field(..., description="Total execution time in milliseconds")
    request_id: str = Field(..., description="Request ID")
    project_id: str = Field(..., description="Project ID")
    intent: Optional[AssistantIntent] = Field(None, description="Detected intent")
    tools_executed: Optional[int] = Field(None, description="Number of tools executed")
    tokens_processed: Optional[int] = Field(None, description="Number of tokens processed")
    context_size: Optional[int] = Field(None, description="Context size in tokens")
    cache_hits: Optional[int] = Field(None, description="Number of cache hits")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "execution_time_ms": 5234,
                "request_id": "req-123",
                "project_id": "proj-456",
                "intent": "requirements_coverage",
                "tools_executed": 3,
                "tokens_processed": 1500,
                "context_size": 2000,
                "cache_hits": 2
            }
        }


class SSEFinalEventData(BaseModel):
    """SSE final event data."""
    
    result: Union[StructuredAnalysisResponse, str] = Field(..., description="Final result")
    metrics: SSEExecutionMetrics = Field(..., description="Execution metrics")
    success: bool = Field(default=True, description="Whether execution was successful")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "result": {
                    "suggestions": [],
                    "scores": {
                        "integration_consistency": 0.75,
                        "requirements_coverage": 0.80,
                        "security_readiness": 0.85,
                        "operability": 0.70
                    },
                    "status": "ok"
                },
                "metrics": {
                    "execution_time_ms": 5234,
                    "request_id": "req-123",
                    "project_id": "proj-456"
                },
                "success": True
            }
        }


class SSEErrorEventData(BaseModel):
    """SSE error event data."""
    
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    trace_id: str = Field(..., description="Trace ID for debugging")
    recoverable: bool = Field(default=False, description="Whether error is recoverable")
    retry_after: Optional[int] = Field(None, description="Retry after seconds")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "message": "Analysis failed due to insufficient context",
                "error_code": "INSUFFICIENT_CONTEXT",
                "trace_id": "trace-789",
                "recoverable": True,
                "retry_after": 30
            }
        }


class SSEEvent(BaseSSEEvent):
    """Complete SSE event model."""
    
    data: Union[
        SSEStartEventData,
        SSETokenEventData,
        SSEJsonEventData,
        SSEProgressEventData,
        SSEToolEventData,
        SSEFinalEventData,
        SSEErrorEventData,
        Dict[str, Any]  # For generic events
    ] = Field(..., description="Event data")
    
    def to_sse_format(self) -> Dict[str, str]:
        """Convert to SSE format for streaming."""
        import json
        
        return {
            "event": self.event_type.value,
            "data": json.dumps({
                "request_id": self.request_id,
                "timestamp": self.timestamp,
                **self.data.dict() if hasattr(self.data, 'dict') else self.data
            }, ensure_ascii=False)
        }
    
    @classmethod
    def create_start_event(
        cls,
        request_id: str,
        intent: AssistantIntent,
        targets: Dict[str, List[str]],
        project_id: str,
        confidence: Optional[float] = None
    ) -> "SSEEvent":
        """Create start event."""
        return cls(
            event_type=SSEEventType.START,
            request_id=request_id,
            data=SSEStartEventData(
                intent=intent,
                targets=targets,
                project_id=project_id,
                confidence=confidence
            )
        )
    
    @classmethod
    def create_token_event(
        cls,
        request_id: str,
        delta: str,
        total_tokens: Optional[int] = None
    ) -> "SSEEvent":
        """Create token event."""
        return cls(
            event_type=SSEEventType.TOKEN,
            request_id=request_id,
            data=SSETokenEventData(
                delta=delta,
                total_tokens=total_tokens
            )
        )
    
    @classmethod
    def create_progress_event(
        cls,
        request_id: str,
        progress: float,
        status: str,
        stage: Optional[str] = None
    ) -> "SSEEvent":
        """Create progress event."""
        return cls(
            event_type=SSEEventType.PROGRESS,
            request_id=request_id,
            data=SSEProgressEventData(
                progress=progress,
                status=status,
                stage=stage
            )
        )
    
    @classmethod
    def create_final_event(
        cls,
        request_id: str,
        result: Union[StructuredAnalysisResponse, str],
        metrics: SSEExecutionMetrics
    ) -> "SSEEvent":
        """Create final event."""
        return cls(
            event_type=SSEEventType.FINAL,
            request_id=request_id,
            data=SSEFinalEventData(
                result=result,
                metrics=metrics
            )
        )
    
    @classmethod
    def create_error_event(
        cls,
        request_id: str,
        message: str,
        error_code: str,
        trace_id: str,
        recoverable: bool = False
    ) -> "SSEEvent":
        """Create error event."""
        return cls(
            event_type=SSEEventType.ERROR,
            request_id=request_id,
            data=SSEErrorEventData(
                message=message,
                error_code=error_code,
                trace_id=trace_id,
                recoverable=recoverable
            )
        )