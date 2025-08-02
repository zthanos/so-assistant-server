"""Diagram API schemas."""

from pydantic import BaseModel


class DiagramBase(BaseModel):
    """Base diagram schema."""
    title: str
    mermaid_code: str
    type: str


class DiagramCreate(DiagramBase):
    """Diagram creation schema."""
    pass


class DiagramUpdate(DiagramBase):
    """Diagram update schema."""
    title: str
    mermaid_code: str
    type: str


class DiagramResponse(DiagramBase):
    """Diagram response schema."""
    id: int
    project_id: str
    
    class Config:
        from_attributes = True