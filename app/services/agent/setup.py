"""Agent framework setup and initialization."""
import logging
from typing import Optional

from app.services.agent.config import agent_config
from app.services.agent.llm_client import streaming_ollama_client
from app.services.agent.orchestrator import get_agent_instance
from app.services.agent.sse_manager import agent_sse_manager
from app.services.agent.tools.base import tool_registry

logger = logging.getLogger(__name__)


class AgentFramework:
    """Main agent framework setup and management."""
    
    def __init__(self):
        """Initialize the agent framework."""
        self.config = agent_config
        self.llm_client = streaming_ollama_client
        self.sse_manager = agent_sse_manager
        self.tool_registry = tool_registry
        self._agent_instance: Optional = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the agent framework."""
        if self._initialized:
            logger.info("Agent framework already initialized")
            return
        
        try:
            logger.info("Initializing SO Assistant Agent Framework...")
            
            # Test LLM connectivity
            await self._test_llm_connectivity()
            
            # Initialize tool registry (tools will be registered by their modules)
            logger.info(f"Tool registry initialized with {len(self.tool_registry.get_all_tools())} tools")
            
            # Create agent instance
            self._agent_instance = get_agent_instance(self.sse_manager)
            
            self._initialized = True
            logger.info("Agent framework initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent framework: {str(e)}")
            raise
    
    async def _test_llm_connectivity(self) -> None:
        """Test connectivity to the local LLM."""
        try:
            logger.info("Testing LLM connectivity...")
            test_prompt = "Hello, this is a connectivity test."
            response = await self.llm_client.generate(test_prompt, "connectivity_test")
            
            if response:
                logger.info("LLM connectivity test successful")
            else:
                raise Exception("LLM returned empty response")
                
        except Exception as e:
            logger.error(f"LLM connectivity test failed: {str(e)}")
            raise Exception(f"Cannot connect to LLM at {self.llm_client.base_url}: {str(e)}")
    
    def get_agent(self):
        """Get the agent instance."""
        if not self._initialized:
            raise RuntimeError("Agent framework not initialized. Call initialize() first.")
        return self._agent_instance
    
    def get_sse_manager(self):
        """Get the SSE manager."""
        return self.sse_manager
    
    def get_config(self):
        """Get the agent configuration."""
        return self.config
    
    def is_initialized(self) -> bool:
        """Check if the framework is initialized."""
        return self._initialized
    
    async def shutdown(self) -> None:
        """Shutdown the agent framework."""
        if not self._initialized:
            return
        
        logger.info("Shutting down agent framework...")
        
        # Close all SSE connections
        await self.sse_manager.close_all_connections()
        
        # Clean up request trackers
        self.sse_manager.cleanup_completed_requests(0)  # Clean all
        
        self._initialized = False
        logger.info("Agent framework shutdown completed")
    
    def reload_configuration(self) -> None:
        """Reload agent configuration."""
        global agent_config
        # Reload configuration from environment
        agent_config = agent_config.__class__()
        self.config = agent_config
        
        # Update LLM client configuration
        self.llm_client.temperature = agent_config.temperature
        self.llm_client.max_tokens = agent_config.max_tokens
        self.llm_client.timeout = agent_config.timeout_seconds
        
        logger.info("Agent configuration reloaded")
    
    def get_framework_status(self) -> dict:
        """Get framework status information."""
        return {
            "initialized": self._initialized,
            "llm_model": self.config.model_name,
            "tools_registered": len(self.tool_registry.get_all_tools()),
            "tools_enabled": len(self.tool_registry.get_enabled_tools()),
            "active_connections": self.sse_manager.get_client_count(),
            "active_requests": len(self.sse_manager.request_trackers),
            "feature_flags": {
                "integration_check": self.config.enable_integration_check,
                "requirements_coverage": self.config.enable_requirements_coverage,
                "improve_paragraph": self.config.enable_improve_paragraph,
                "qna": self.config.enable_qna,
            }
        }


# Global agent framework instance
agent_framework = AgentFramework()


async def initialize_agent_framework() -> AgentFramework:
    """Initialize and return the global agent framework."""
    await agent_framework.initialize()
    return agent_framework


def get_agent_framework() -> AgentFramework:
    """Get the global agent framework instance."""
    return agent_framework