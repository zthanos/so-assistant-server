"""Document models for agent context processing."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class DocumentType(str, Enum):
    """Document types."""
    SO_SECTION = "so_section"
    REQUIREMENT = "requirement"
    SEQUENCE_DIAGRAM = "sequence_diagram"
    C4_DIAGRAM = "c4_diagram"
    CHAT_SUMMARY = "chat_summary"


class SOSectionType(str, Enum):
    """SO section types based on standard structure."""
    INTRODUCTION = "introduction"
    OVERVIEW = "overview"
    ASSUMPTIONS = "assumptions"
    REFERENCES = "references"
    RISKS = "risks"
    ADRS = "adrs"
    SOLUTION_ARCHITECTURE = "solution_architecture"
    SOLUTION_OVERVIEW = "solution_overview"
    NEW_SERVICES = "new_services"
    DATA_ARCHITECTURE = "data_architecture"
    DATA_OVERVIEW = "data_overview"
    DATA_CONTRACTS = "data_contracts"
    INTEGRATION_ARCHITECTURE = "integration_architecture"
    SECURITY_ARCHITECTURE = "security_architecture"
    FAULT_HANDLING = "fault_handling"
    LOGGING_ARCHITECTURE = "logging_architecture"
    MONITORING_ARCHITECTURE = "monitoring_architecture"
    SUSTAINABILITY = "sustainability"
    IMPLEMENTATION_TEAMS = "implementation_teams"
    GENERIC = "generic"


class RequirementStatus(str, Enum):
    """Requirement status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class RequirementPriority(str, Enum):
    """Requirement priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DiagramType(str, Enum):
    """Diagram types."""
    SEQUENCE = "sequence"
    C4_CONTEXT = "c4_context"
    C4_CONTAINER = "c4_container"
    C4_COMPONENT = "c4_component"
    C4_DYNAMIC = "c4_dynamic"
    C4_DEPLOYMENT = "c4_deployment"


# Base Document Models
class BaseDocument(BaseModel):
    """Base document model."""
    
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    document_type: DocumentType = Field(..., description="Document type")
    project_id: str = Field(..., description="Project ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        """Pydantic config."""
        use_enum_values = True


class SOSection(BaseDocument):
    """Solution Outline section model."""
    
    document_type: DocumentType = Field(default=DocumentType.SO_SECTION, const=True)
    section_type: SOSectionType = Field(..., description="Section type")
    level: int = Field(..., ge=1, le=6, description="Header level (1-6)")
    parent_id: Optional[str] = Field(None, description="Parent section ID")
    start_line: Optional[int] = Field(None, description="Start line in original document")
    line_count: Optional[int] = Field(None, description="Number of lines")
    neighbors: List["SOSection"] = Field(default_factory=list, description="Neighboring sections")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "id": "SEC-2.1",
                "title": "Solution Overview",
                "content": "High-level solution description...",
                "document_type": "so_section",
                "project_id": "proj-123",
                "section_type": "solution_overview",
                "level": 2,
                "parent_id": "SEC-2",
                "start_line": 45,
                "line_count": 15
            }
        }


class Requirement(BaseDocument):
    """Requirement model."""
    
    document_type: DocumentType = Field(default=DocumentType.REQUIREMENT, const=True)
    description: str = Field(..., description="Requirement description")
    priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority")
    status: RequirementStatus = Field(default=RequirementStatus.ACTIVE, description="Status")
    category: Optional[str] = Field(None, description="Requirement category")
    source: Optional[str] = Field(None, description="Requirement source")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Acceptance criteria")
    related_requirements: List[str] = Field(default_factory=list, description="Related requirement IDs")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "id": "REQ-12",
                "title": "User Authentication",
                "content": "The system shall provide secure user authentication",
                "document_type": "requirement",
                "project_id": "proj-123",
                "description": "Users must be able to authenticate securely",
                "priority": "high",
                "status": "active",
                "category": "security",
                "acceptance_criteria": ["Support multi-factor authentication", "Session timeout after 30 minutes"]
            }
        }


# Diagram Models
class DiagramParticipant(BaseModel):
    """Diagram participant model."""
    
    id: str = Field(..., description="Participant ID")
    label: str = Field(..., description="Participant label")
    type: Optional[str] = Field(None, description="Participant type (actor, etc.)")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "id": "user",
                "label": "User",
                "type": "actor"
            }
        }


class DiagramInteraction(BaseModel):
    """Diagram interaction model."""
    
    step: int = Field(..., description="Step number")
    from_participant: str = Field(..., description="Source participant")
    to_participant: str = Field(..., description="Target participant")
    message: str = Field(..., description="Interaction message")
    arrow_type: Optional[str] = Field(None, description="Arrow type")
    interaction_type: Optional[str] = Field(None, description="Interaction type")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "step": 1,
                "from_participant": "user",
                "to_participant": "system",
                "message": "Login request",
                "arrow_type": "->>",
                "interaction_type": "sync_call"
            }
        }


class DiagramStep(BaseModel):
    """Diagram step model."""
    
    step_number: int = Field(..., description="Step number")
    description: str = Field(..., description="Step description")
    participants: List[str] = Field(default_factory=list, description="Involved participants")
    type: Optional[str] = Field(None, description="Step type (note, control_start, etc.)")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "step_number": 1,
                "description": "User -> System: Login request",
                "participants": ["user", "system"],
                "type": "interaction"
            }
        }


class ParsedSequenceDiagram(BaseDocument):
    """Parsed sequence diagram model."""
    
    document_type: DocumentType = Field(default=DocumentType.SEQUENCE_DIAGRAM, const=True)
    diagram_type: DiagramType = Field(default=DiagramType.SEQUENCE, const=True)
    participants: List[DiagramParticipant] = Field(default_factory=list, description="Diagram participants")
    interactions: List[DiagramInteraction] = Field(default_factory=list, description="Participant interactions")
    steps: List[DiagramStep] = Field(default_factory=list, description="Ordered steps")
    total_steps: int = Field(default=0, description="Total number of steps")
    participant_count: int = Field(default=0, description="Number of participants")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "id": "SEQ-01",
                "title": "User Login Flow",
                "content": "sequenceDiagram...",
                "document_type": "sequence_diagram",
                "project_id": "proj-123",
                "diagram_type": "sequence",
                "participants": [
                    {"id": "user", "label": "User", "type": "actor"},
                    {"id": "system", "label": "System"}
                ],
                "interactions": [
                    {
                        "step": 1,
                        "from_participant": "user",
                        "to_participant": "system",
                        "message": "Login request",
                        "arrow_type": "->>",
                        "interaction_type": "sync_call"
                    }
                ],
                "total_steps": 5,
                "participant_count": 2
            }
        }


class C4Element(BaseModel):
    """C4 diagram element model."""
    
    id: str = Field(..., description="Element ID")
    name: str = Field(..., description="Element name")
    technology: Optional[str] = Field(None, description="Technology stack")
    description: Optional[str] = Field(None, description="Element description")
    type: Optional[str] = Field(None, description="Element type")
    external: bool = Field(default=False, description="Is external element")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "id": "web_app",
                "name": "Web Application",
                "technology": "React, Node.js",
                "description": "Main web application",
                "type": "container",
                "external": False
            }
        }


class C4Relationship(BaseModel):
    """C4 diagram relationship model."""
    
    from_element: str = Field(..., description="Source element ID")
    to_element: str = Field(..., description="Target element ID")
    label: str = Field(..., description="Relationship label")
    technology: Optional[str] = Field(None, description="Technology used")
    description: Optional[str] = Field(None, description="Relationship description")
    bidirectional: bool = Field(default=False, description="Is bidirectional")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "from_element": "web_app",
                "to_element": "api",
                "label": "Makes API calls",
                "technology": "HTTPS",
                "description": "Web app communicates with API",
                "bidirectional": False
            }
        }


class ParsedC4Diagram(BaseDocument):
    """Parsed C4 diagram model."""
    
    document_type: DocumentType = Field(default=DocumentType.C4_DIAGRAM, const=True)
    diagram_type: DiagramType = Field(..., description="C4 diagram type")
    systems: List[C4Element] = Field(default_factory=list, description="System elements")
    containers: List[C4Element] = Field(default_factory=list, description="Container elements")
    components: List[C4Element] = Field(default_factory=list, description="Component elements")
    relationships: List[C4Relationship] = Field(default_factory=list, description="Element relationships")
    boundaries: List[Dict[str, Any]] = Field(default_factory=list, description="Boundary definitions")
    element_count: int = Field(default=0, description="Total number of elements")
    relationship_count: int = Field(default=0, description="Number of relationships")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "id": "C4-Context",
                "title": "System Context Diagram",
                "content": "C4Context...",
                "document_type": "c4_diagram",
                "project_id": "proj-123",
                "diagram_type": "c4_context",
                "systems": [
                    {
                        "id": "main_system",
                        "name": "Main System",
                        "technology": "Java, Spring",
                        "description": "Core business system",
                        "type": "system",
                        "external": False
                    }
                ],
                "relationships": [
                    {
                        "from_element": "user",
                        "to_element": "main_system",
                        "label": "Uses",
                        "technology": "HTTPS",
                        "bidirectional": False
                    }
                ],
                "element_count": 3,
                "relationship_count": 2
            }
        }


class ChatSummary(BaseDocument):
    """Chat summary model."""
    
    document_type: DocumentType = Field(default=DocumentType.CHAT_SUMMARY, const=True)
    summary_text: str = Field(..., description="Chat summary text")
    message_count: int = Field(default=0, description="Number of messages summarized")
    time_range: Optional[Dict[str, datetime]] = Field(None, description="Time range of messages")
    key_topics: List[str] = Field(default_factory=list, description="Key topics discussed")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "id": "chat-summary-123",
                "title": "Recent Chat Summary",
                "content": "Discussion about authentication requirements...",
                "document_type": "chat_summary",
                "project_id": "proj-123",
                "summary_text": "Recent discussions focused on authentication and security requirements",
                "message_count": 15,
                "key_topics": ["authentication", "security", "requirements"]
            }
        }


# Context Models
class AssembledContext(BaseModel):
    """Assembled context model."""
    
    project_id: str = Field(..., description="Project ID")
    intent: str = Field(..., description="Analysis intent")
    so_sections: List[SOSection] = Field(default_factory=list, description="SO sections")
    requirements: List[Requirement] = Field(default_factory=list, description="Requirements")
    sequence_diagrams: List[ParsedSequenceDiagram] = Field(default_factory=list, description="Sequence diagrams")
    c4_diagrams: List[ParsedC4Diagram] = Field(default_factory=list, description="C4 diagrams")
    chat_summary: Optional[ChatSummary] = Field(None, description="Chat summary")
    assembly_metadata: Dict[str, Any] = Field(default_factory=dict, description="Assembly metadata")
    
    @property
    def total_documents(self) -> int:
        """Get total number of documents."""
        return (
            len(self.so_sections) +
            len(self.requirements) +
            len(self.sequence_diagrams) +
            len(self.c4_diagrams) +
            (1 if self.chat_summary else 0)
        )
    
    @property
    def estimated_tokens(self) -> int:
        """Estimate total token count."""
        total_chars = 0
        
        for section in self.so_sections:
            total_chars += len(section.content) + len(section.title)
        
        for req in self.requirements:
            total_chars += len(req.content) + len(req.description)
        
        for diagram in self.sequence_diagrams + self.c4_diagrams:
            total_chars += len(diagram.content) + len(str(diagram.dict()))
        
        if self.chat_summary:
            total_chars += len(self.chat_summary.content)
        
        # Rough approximation: 4 characters per token
        return total_chars // 4
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "project_id": "proj-123",
                "intent": "requirements_coverage",
                "so_sections": [],
                "requirements": [],
                "sequence_diagrams": [],
                "c4_diagrams": [],
                "chat_summary": None,
                "assembly_metadata": {
                    "assembly_time_ms": 1500,
                    "context_size_tokens": 2000
                }
            }
        }


# Update forward references
SOSection.model_rebuild()