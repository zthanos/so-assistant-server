"""Assistant API schemas for LLM routing and SSE responses."""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

from app.api.schemas.common import BaseResponse


class AssistantIntent(str, Enum):
    """Assistant intent types."""
    INTEGRATION_CHECK = "integration_check"
    REQUIREMENTS_COVERAGE = "requirements_coverage"
    IMPROVE_PARAGRAPH = "improve_paragraph"
    QNA = "qna"


class SuggestionType(str, Enum):
    """Suggestion types."""
    INTEGRATION = "integration"
    COVERAGE = "coverage"
    REWRITE = "rewrite"
    SECURITY = "security"
    PERFORMANCE = "performance"
    OBSERVABILITY = "observability"
    FAULT_HANDLING = "fault_handling"


class SuggestionSeverity(str, Enum):
    """Suggestion severity levels."""
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class AnalysisStatus(str, Enum):
    """Analysis status."""
    OK = "ok"
    INSUFFICIENT = "insufficient"


# Request Schemas
class AssistantQueryRequest(BaseModel):
    """Request schema for assistant query."""
    
    user_message: str = Field(..., description="User query text", min_length=1, max_length=5000)
    routing_override: Optional[AssistantIntent] = Field(None, description="Force specific intent")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "user_message": "Καλύπτουμε το REQ-12;",
                "routing_override": None
            }
        }


# Response Schemas
class RouterOutput(BaseModel):
    """Router output schema."""
    
    intent: AssistantIntent = Field(..., description="Detected intent")
    targets: Dict[str, List[str]] = Field(..., description="Target IDs")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reason: str = Field(..., description="Rationale for intent")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "intent": "requirements_coverage",
                "targets": {
                    "so_ids": ["SEC-2.1"],
                    "requirement_ids": ["REQ-12"],
                    "diagram_ids": ["SEQ-01"]
                },
                "confidence": 0.85,
                "reason": "User asking about requirement coverage"
            }
        }


class SuggestionEvidence(BaseModel):
    """Evidence supporting a suggestion."""
    
    requirements: List[str] = Field(default_factory=list, description="REQ-* IDs")
    diagrams: List[Dict[str, Any]] = Field(default_factory=list, description="Diagram references")
    so_quotes: List[str] = Field(default_factory=list, description="SO excerpts")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "requirements": ["REQ-12", "REQ-15"],
                "diagrams": [
                    {
                        "diagram_id": "SEQ-01",
                        "steps": [1, 2, 3]
                    }
                ],
                "so_quotes": ["The system shall implement authentication"]
            }
        }


class SuggestionLocation(BaseModel):
    """Location reference for a suggestion."""
    
    so_section_id: str = Field(..., description="SO section ID (SEC-*)")
    paragraph_index: int = Field(..., ge=0, description="Paragraph index within section")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "so_section_id": "SEC-2.1",
                "paragraph_index": 0
            }
        }


class Suggestion(BaseModel):
    """Analysis suggestion."""
    
    id: str = Field(..., description="Unique suggestion ID")
    type: SuggestionType = Field(..., description="Suggestion type")
    severity: SuggestionSeverity = Field(..., description="Severity level")
    location: SuggestionLocation = Field(..., description="Location reference")
    summary: str = Field(..., description="One-line summary")
    rationale: str = Field(..., description="Why this suggestion")
    evidence: SuggestionEvidence = Field(..., description="Supporting evidence")
    recommendation: str = Field(..., description="What to do")
    proposed_text: Optional[str] = Field(None, description="Full rewrite if applicable")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "id": "SUG-001",
                "type": "integration",
                "severity": "major",
                "location": {
                    "so_section_id": "SEC-2.1",
                    "paragraph_index": 0
                },
                "summary": "Component X missing in sequence diagram",
                "rationale": "SO describes component X but it's not shown in SEQ-01",
                "evidence": {
                    "requirements": ["REQ-12"],
                    "diagrams": [{"diagram_id": "SEQ-01", "steps": [1, 2]}],
                    "so_quotes": ["The system shall include component X"]
                },
                "recommendation": "Add component X to sequence diagram",
                "proposed_text": None,
                "confidence": 0.9
            }
        }


class AnalysisScores(BaseModel):
    """Analysis scores."""
    
    integration_consistency: float = Field(..., ge=0.0, le=1.0, description="Integration consistency score")
    requirements_coverage: float = Field(..., ge=0.0, le=1.0, description="Requirements coverage score")
    security_readiness: float = Field(..., ge=0.0, le=1.0, description="Security readiness score")
    operability: float = Field(..., ge=0.0, le=1.0, description="Operability score")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "integration_consistency": 0.75,
                "requirements_coverage": 0.80,
                "security_readiness": 0.85,
                "operability": 0.70
            }
        }


class StructuredAnalysisResponse(BaseModel):
    """Structured analysis response for integration_check, requirements_coverage, improve_paragraph."""
    
    suggestions: List[Suggestion] = Field(default_factory=list, description="Analysis suggestions")
    scores: AnalysisScores = Field(..., description="Analysis scores")
    status: AnalysisStatus = Field(..., description="Analysis status")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "id": "SUG-001",
                        "type": "integration",
                        "severity": "major",
                        "location": {"so_section_id": "SEC-2.1", "paragraph_index": 0},
                        "summary": "Component X missing in sequence diagram",
                        "rationale": "SO describes component X but it's not shown in SEQ-01",
                        "evidence": {
                            "requirements": ["REQ-12"],
                            "diagrams": [{"diagram_id": "SEQ-01", "steps": [1, 2]}],
                            "so_quotes": ["The system shall include component X"]
                        },
                        "recommendation": "Add component X to sequence diagram",
                        "proposed_text": None,
                        "confidence": 0.9
                    }
                ],
                "scores": {
                    "integration_consistency": 0.75,
                    "requirements_coverage": 0.80,
                    "security_readiness": 0.85,
                    "operability": 0.70
                },
                "status": "ok"
            }
        }


# SSE Event Schemas
class SSEEventType(str, Enum):
    """SSE event types."""
    START = "start"
    TOKEN = "token"
    JSON = "json"
    FINAL = "final"
    ERROR = "error"
    PROGRESS = "progress"
    TOOL_EXECUTION = "tool_execution"


class SSEStartEvent(BaseModel):
    """SSE start event data."""
    
    request_id: str = Field(..., description="Request ID")
    timestamp: float = Field(..., description="Event timestamp")
    intent: AssistantIntent = Field(..., description="Detected intent")
    targets: Dict[str, List[str]] = Field(..., description="Target IDs")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "request_id": "req-123",
                "timestamp": 1640995200.0,
                "intent": "requirements_coverage",
                "targets": {
                    "so_ids": ["SEC-2.1"],
                    "requirement_ids": ["REQ-12"],
                    "diagram_ids": []
                }
            }
        }


class SSETokenEvent(BaseModel):
    """SSE token event data."""
    
    request_id: Optional[str] = Field(None, description="Request ID")
    timestamp: float = Field(..., description="Event timestamp")
    delta: str = Field(..., description="Token content")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "request_id": "req-123",
                "timestamp": 1640995200.0,
                "delta": "The analysis shows"
            }
        }


class SSEJsonEvent(BaseModel):
    """SSE JSON event data."""
    
    request_id: Optional[str] = Field(None, description="Request ID")
    timestamp: float = Field(..., description="Event timestamp")
    partial: Dict[str, Any] = Field(..., description="Partial JSON data")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "request_id": "req-123",
                "timestamp": 1640995200.0,
                "partial": {"suggestions": []}
            }
        }


class SSEExecutionMetrics(BaseModel):
    """Execution metrics."""
    
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    request_id: str = Field(..., description="Request ID")
    project_id: str = Field(..., description="Project ID")
    intent: Optional[AssistantIntent] = Field(None, description="Intent")
    tools_executed: Optional[int] = Field(None, description="Number of tools executed")
    tokens_processed: Optional[int] = Field(None, description="Number of tokens processed")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "execution_time_ms": 5234,
                "request_id": "req-123",
                "project_id": "proj-456",
                "intent": "requirements_coverage",
                "tools_executed": 3,
                "tokens_processed": 1500
            }
        }


class SSEFinalEvent(BaseModel):
    """SSE final event data."""
    
    request_id: Optional[str] = Field(None, description="Request ID")
    timestamp: float = Field(..., description="Event timestamp")
    result: Union[StructuredAnalysisResponse, str] = Field(..., description="Final result")
    metrics: SSEExecutionMetrics = Field(..., description="Execution metrics")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "request_id": "req-123",
                "timestamp": 1640995200.0,
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
                }
            }
        }


class SSEErrorEvent(BaseModel):
    """SSE error event data."""
    
    request_id: Optional[str] = Field(None, description="Request ID")
    timestamp: float = Field(..., description="Event timestamp")
    message: str = Field(..., description="Error message")
    trace_id: str = Field(..., description="Trace ID for debugging")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "request_id": "req-123",
                "timestamp": 1640995200.0,
                "message": "Analysis failed due to insufficient context",
                "trace_id": "trace-789"
            }
        }


class SSEProgressEvent(BaseModel):
    """SSE progress event data."""
    
    request_id: Optional[str] = Field(None, description="Request ID")
    timestamp: float = Field(..., description="Event timestamp")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress (0.0-1.0)")
    status: str = Field(..., description="Current status")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "request_id": "req-123",
                "timestamp": 1640995200.0,
                "progress": 0.5,
                "status": "Analyzing requirements coverage"
            }
        }


# Response wrapper for non-SSE endpoints (if needed)
class AssistantResponse(BaseResponse):
    """Assistant response wrapper."""
    
    data: Union[StructuredAnalysisResponse, str] = Field(..., description="Analysis result")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Response metadata")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "suggestions": [],
                    "scores": {
                        "integration_consistency": 0.75,
                        "requirements_coverage": 0.80,
                        "security_readiness": 0.85,
                        "operability": 0.70
                    },
                    "status": "ok"
                },
                "metadata": {
                    "execution_time_ms": 5234,
                    "intent": "requirements_coverage"
                }
            }
        }