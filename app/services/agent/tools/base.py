"""Base tool framework for LangChain agent tools."""
import asyncio
import logging
import time
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

from app.services.agent.config import agent_config
from app.core.exceptions import LLMException

logger = logging.getLogger(__name__)


class ToolExecutionResult(BaseModel):
    """Result of tool execution with metadata."""
    
    success: bool = Field(..., description="Whether the tool execution was successful")
    result: Any = Field(..., description="The actual result data")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: float = Field(..., description="Execution time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseAgentTool(BaseTool, ABC):
    """Base class for all SO Assistant agent tools."""
    
    # Tool metadata
    tool_category: str = Field(..., description="Category of the tool")
    requires_project_id: bool = Field(default=True, description="Whether tool requires project_id")
    
    def __init__(self, **kwargs):
        """Initialize the base agent tool."""
        super().__init__(**kwargs)
        self.config = agent_config
    
    def _run(
        self,
        *args,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """Synchronous tool execution wrapper."""
        try:
            # Run async method in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._arun(*args, run_manager=None, **kwargs))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error in {self.name} sync execution: {str(e)}")
            return self._handle_error(e)
    
    async def _arun(
        self,
        *args,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """Asynchronous tool execution wrapper with error handling and logging."""
        start_time = time.time()
        tool_name = self.name
        
        try:
            logger.info(f"Starting tool execution: {tool_name}")
            
            # Validate inputs if project_id is required
            if self.requires_project_id and "project_id" not in kwargs:
                raise ValueError(f"Tool {tool_name} requires project_id parameter")
            
            # Execute the actual tool logic
            result = await self._execute(*args, **kwargs)
            
            execution_time = time.time() - start_time
            logger.info(f"Tool {tool_name} completed successfully in {execution_time:.2f}s")
            
            # Return structured result
            return ToolExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={
                    "tool_name": tool_name,
                    "tool_category": self.tool_category,
                }
            ).dict()
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Tool {tool_name} failed after {execution_time:.2f}s: {error_msg}")
            logger.debug(f"Tool {tool_name} traceback: {traceback.format_exc()}")
            
            return ToolExecutionResult(
                success=False,
                result=None,
                error=error_msg,
                execution_time=execution_time,
                metadata={
                    "tool_name": tool_name,
                    "tool_category": self.tool_category,
                    "error_type": type(e).__name__,
                }
            ).dict()
    
    @abstractmethod
    async def _execute(self, *args, **kwargs) -> Any:
        """Execute the actual tool logic. Must be implemented by subclasses."""
        pass
    
    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle tool execution errors."""
        return {
            "success": False,
            "result": None,
            "error": str(error),
            "error_type": type(error).__name__
        }
    
    def _validate_project_access(self, project_id: str) -> bool:
        """Validate that the tool can access the specified project."""
        # TODO: Implement actual project access validation
        # For now, just check that project_id is provided
        return bool(project_id and project_id.strip())
    
    async def _retry_with_backoff(self, func, max_retries: int = None, *args, **kwargs):
        """Execute function with retry and exponential backoff."""
        max_retries = max_retries or self.config.max_retries
        backoff = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries:
                    raise e
                
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}")
                await asyncio.sleep(backoff)
                backoff *= self.config.retry_backoff_multiplier


class ToolRegistry:
    """Registry for managing agent tools."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseAgentTool] = {}
        self._categories: Dict[str, list] = {}
    
    def register_tool(self, tool: BaseAgentTool) -> None:
        """Register a tool in the registry."""
        tool_name = tool.name
        if tool_name in self._tools:
            logger.warning(f"Tool {tool_name} is already registered, overwriting")
        
        self._tools[tool_name] = tool
        
        # Add to category
        category = tool.tool_category
        if category not in self._categories:
            self._categories[category] = []
        if tool not in self._categories[category]:
            self._categories[category].append(tool)
        
        logger.info(f"Registered tool: {tool_name} (category: {category})")
    
    def get_tool(self, name: str) -> Optional[BaseAgentTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_tools_by_category(self, category: str) -> list:
        """Get all tools in a specific category."""
        return self._categories.get(category, [])
    
    def get_all_tools(self) -> list:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_enabled_tools(self) -> list:
        """Get all enabled tools based on feature flags."""
        enabled_tools = []
        
        for tool in self._tools.values():
            # Check feature flags based on tool category
            if tool.tool_category == "routing" and self.config.enable_qna:
                enabled_tools.append(tool)
            elif tool.tool_category == "context" and True:  # Context tools always enabled
                enabled_tools.append(tool)
            elif tool.tool_category == "analysis":
                # Check specific analysis tool flags
                if (tool.name == "integration_check_analysis" and self.config.enable_integration_check) or \
                   (tool.name == "requirements_coverage_analysis" and self.config.enable_requirements_coverage) or \
                   (tool.name == "paragraph_improvement_analysis" and self.config.enable_improve_paragraph) or \
                   (tool.name == "qna_response" and self.config.enable_qna):
                    enabled_tools.append(tool)
            else:
                enabled_tools.append(tool)
        
        return enabled_tools
    
    @property
    def config(self):
        """Get agent configuration."""
        return agent_config


# Global tool registry instance
tool_registry = ToolRegistry()


class ToolExecutionContext:
    """Context for tool execution with shared state."""
    
    def __init__(self, project_id: str, request_id: str, client_id: str):
        """Initialize tool execution context."""
        self.project_id = project_id
        self.request_id = request_id
        self.client_id = client_id
        self.shared_data: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def set_data(self, key: str, value: Any) -> None:
        """Set shared data for the execution context."""
        self.shared_data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get shared data from the execution context."""
        return self.shared_data.get(key, default)
    
    def add_execution_record(self, tool_name: str, result: Any, execution_time: float) -> None:
        """Add an execution record to the history."""
        self.execution_history.append({
            "tool_name": tool_name,
            "result": result,
            "execution_time": execution_time,
            "timestamp": time.time()
        })


def create_tool_input_schema(fields: Dict[str, Any]) -> Type[BaseModel]:
    """Create a Pydantic schema for tool input validation."""
    return type("ToolInputSchema", (BaseModel,), fields)


def validate_tool_output(output: Any, expected_type: Type) -> bool:
    """Validate tool output against expected type."""
    try:
        if expected_type == dict and isinstance(output, dict):
            return True
        elif expected_type == str and isinstance(output, str):
            return True
        elif expected_type == list and isinstance(output, list):
            return True
        elif hasattr(expected_type, "__origin__"):  # Generic types
            return True
        else:
            return isinstance(output, expected_type)
    except Exception:
        return False


async def execute_tools_in_parallel(tools: List[BaseAgentTool], inputs: List[Dict[str, Any]]) -> List[Any]:
    """Execute multiple tools in parallel."""
    if len(tools) != len(inputs):
        raise ValueError("Number of tools must match number of input sets")
    
    tasks = []
    for tool, tool_input in zip(tools, inputs):
        task = tool._arun(**tool_input)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and handle exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Tool {tools[i].name} failed: {str(result)}")
            processed_results.append({
                "success": False,
                "error": str(result),
                "tool_name": tools[i].name
            })
        else:
            processed_results.append(result)
    
    return processed_results


class ToolMetrics:
    """Collect and track tool execution metrics."""
    
    def __init__(self):
        """Initialize tool metrics collector."""
        self.execution_counts: Dict[str, int] = {}
        self.execution_times: Dict[str, List[float]] = {}
        self.error_counts: Dict[str, int] = {}
        self.success_counts: Dict[str, int] = {}
    
    def record_execution(self, tool_name: str, execution_time: float, success: bool) -> None:
        """Record a tool execution."""
        # Update counts
        self.execution_counts[tool_name] = self.execution_counts.get(tool_name, 0) + 1
        
        if success:
            self.success_counts[tool_name] = self.success_counts.get(tool_name, 0) + 1
        else:
            self.error_counts[tool_name] = self.error_counts.get(tool_name, 0) + 1
        
        # Track execution times
        if tool_name not in self.execution_times:
            self.execution_times[tool_name] = []
        self.execution_times[tool_name].append(execution_time)
        
        # Keep only last 100 execution times to prevent memory growth
        if len(self.execution_times[tool_name]) > 100:
            self.execution_times[tool_name] = self.execution_times[tool_name][-100:]
    
    def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get statistics for a specific tool."""
        if tool_name not in self.execution_counts:
            return {"error": "No data for tool"}
        
        times = self.execution_times.get(tool_name, [])
        return {
            "executions": self.execution_counts[tool_name],
            "successes": self.success_counts.get(tool_name, 0),
            "errors": self.error_counts.get(tool_name, 0),
            "success_rate": self.success_counts.get(tool_name, 0) / self.execution_counts[tool_name],
            "avg_execution_time": sum(times) / len(times) if times else 0,
            "min_execution_time": min(times) if times else 0,
            "max_execution_time": max(times) if times else 0,
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tools."""
        return {
            tool_name: self.get_tool_stats(tool_name)
            for tool_name in self.execution_counts.keys()
        }


# Global tool metrics instance
tool_metrics = ToolMetrics()