"""Agent configuration for LangChain Agent."""
from typing import List, Optional
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for the LangChain Agent."""
    
    # LLM Configuration
    model_name: str = Field(default="gemma3", description="Local LLM model name")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="LLM temperature")
    max_tokens: int = Field(default=4096, gt=0, description="Maximum tokens for LLM response")
    timeout_seconds: int = Field(default=30, gt=0, description="LLM request timeout")
    
    # Context Limits
    max_so_chunks: int = Field(default=8, gt=0, description="Maximum SO sections to retrieve")
    max_diagrams: int = Field(default=2, gt=0, description="Maximum diagrams to retrieve")
    max_requirements: int = Field(default=10, gt=0, description="Maximum requirements to retrieve")
    max_context_tokens: int = Field(default=30000, gt=0, description="Maximum context size in tokens")
    
    # Agent Configuration
    max_iterations: int = Field(default=5, gt=0, description="Maximum agent iterations")
    handle_parsing_errors: bool = Field(default=True, description="Handle LLM parsing errors")
    verbose: bool = Field(default=False, description="Enable verbose agent logging")
    
    # Feature Flags
    enable_integration_check: bool = Field(default=True, description="Enable integration check intent")
    enable_requirements_coverage: bool = Field(default=True, description="Enable requirements coverage intent")
    enable_improve_paragraph: bool = Field(default=True, description="Enable improve paragraph intent")
    enable_qna: bool = Field(default=True, description="Enable Q&A intent")
    
    # Language Support
    supported_languages: List[str] = Field(default=["el", "en"], description="Supported languages")
    default_language: str = Field(default="auto", description="Default language detection")
    
    # Performance Settings
    enable_caching: bool = Field(default=True, description="Enable result caching")
    cache_ttl_seconds: int = Field(default=3600, gt=0, description="Cache TTL in seconds")
    parallel_processing: bool = Field(default=True, description="Enable parallel context retrieval")
    
    # Retry Configuration
    max_retries: int = Field(default=1, ge=0, description="Maximum retry attempts")
    retry_backoff_multiplier: float = Field(default=1.5, gt=1.0, description="Retry backoff multiplier")
    
    class Config:
        """Pydantic config."""
        env_prefix = "AGENT_"
        case_sensitive = False


# Global agent configuration instance
agent_config = AgentConfig()