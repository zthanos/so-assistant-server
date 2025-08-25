"""Main LangChain Agent orchestrator for SO Assistant."""
import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks import BaseCallbackHandler

from app.services.agent.config import agent_config
from app.services.agent.llm_client import streaming_ollama_client
from app.services.agent.tools.base import tool_registry
from app.services.agent.error_handling import (
    error_handler, circuit_breaker, retry_manager, graceful_degradation,
    with_error_handling, with_timeout, IntentDetectionError, ContextAssemblyError, AnalysisError
)
from app.core.events import SSEManager
from app.core.exceptions import LLMException

logger = logging.getLogger(__name__)


class AgentSSECallback(BaseCallbackHandler):
    """Callback handler for streaming agent execution via SSE."""
    
    def __init__(self, client_id: str, sse_manager: SSEManager):
        """Initialize the SSE callback handler."""
        self.client_id = client_id
        self.sse_manager = sse_manager
        self.request_id = str(uuid.uuid4())
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts running."""
        await self.sse_manager.send_event(
            self.client_id,
            "llm_start",
            {
                "request_id": self.request_id,
                "timestamp": time.time(),
                "message": "LLM processing started"
            }
        )
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when LLM generates a new token."""
        await self.sse_manager.send_event(
            self.client_id,
            "token",
            {
                "request_id": self.request_id,
                "timestamp": time.time(),
                "delta": token
            }
        )
    
    async def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM finishes running."""
        await self.sse_manager.send_event(
            self.client_id,
            "llm_end",
            {
                "request_id": self.request_id,
                "timestamp": time.time(),
                "message": "LLM processing completed"
            }
        )
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when a tool starts running."""
        tool_name = serialized.get("name", "unknown")
        await self.sse_manager.send_event(
            self.client_id,
            "tool_start",
            {
                "request_id": self.request_id,
                "timestamp": time.time(),
                "tool_name": tool_name,
                "message": f"Starting tool: {tool_name}"
            }
        )
    
    async def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when a tool finishes running."""
        await self.sse_manager.send_event(
            self.client_id,
            "tool_end",
            {
                "request_id": self.request_id,
                "timestamp": time.time(),
                "message": "Tool execution completed"
            }
        )
    
    async def on_agent_action(self, action, **kwargs) -> None:
        """Called when agent takes an action."""
        await self.sse_manager.send_event(
            self.client_id,
            "agent_action",
            {
                "request_id": self.request_id,
                "timestamp": time.time(),
                "action": action.tool,
                "input": str(action.tool_input)
            }
        )


class SOAssistantAgent:
    """Main SO Assistant Agent orchestrator."""
    
    def __init__(self, sse_manager: SSEManager):
        """Initialize the SO Assistant Agent."""
        self.config = agent_config
        self.llm = streaming_ollama_client
        self.sse_manager = sse_manager
        self.tools = tool_registry.get_enabled_tools()
        
        # Create the agent prompt template
        self.prompt_template = self._create_agent_prompt()
        
        # Create the agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt_template
        )
        
        # Create the agent executor
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=self.config.verbose,
            handle_parsing_errors=self.config.handle_parsing_errors,
            max_iterations=self.config.max_iterations,
            return_intermediate_steps=True
        )
        
        logger.info(f"SO Assistant Agent initialized with {len(self.tools)} tools")
    
    def _create_agent_prompt(self) -> PromptTemplate:
        """Create the agent prompt template."""
        template = """You are the SO Assistant Agent, an expert in analyzing Solution Outline documents, requirements, and diagrams.

Your role is to help architects by:
1. Detecting the intent of their queries (integration_check, requirements_coverage, improve_paragraph, qna)
2. Gathering relevant context from project documents
3. Providing structured analysis and suggestions

Available tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Important guidelines:
- Always start by using the intent_router tool to detect the user's intent
- Gather relevant context using the appropriate retrieval tools
- Use the specialized analysis tools based on the detected intent
- For structured intents (integration_check, requirements_coverage, improve_paragraph), return JSON responses
- For qna intent, return plain text responses
- If context is insufficient, clearly state this in your response

Question: {input}
Thought:{agent_scratchpad}"""
        
        return PromptTemplate(
            template=template,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={
                "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
                "tool_names": ", ".join([tool.name for tool in self.tools])
            }
        )
    
    async def process_query(
        self,
        project_id: str,
        user_message: str,
        client_id: str,
        routing_override: Optional[str] = None
    ) -> None:
        """Process user query through the agent workflow."""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Step 1: Intent Detection
            await self.sse_manager.send_event(
                client_id,
                "progress",
                {
                    "request_id": request_id,
                    "timestamp": time.time(),
                    "progress": 0.1,
                    "status": "Detecting intent"
                }
            )
            
            # Get intent router tool
            intent_router = None
            for tool in self.tools:
                if tool.name == "intent_router":
                    intent_router = tool
                    break
            
            if not intent_router:
                raise Exception("Intent router tool not found")
            
            # Detect intent with timeout and error handling
            try:
                router_result = await with_timeout(
                    intent_router._execute(
                        user_message=user_message,
                        language="auto"
                    ),
                    timeout_seconds=agent_config.timeout_seconds,
                    error_message="Intent detection timed out"
                )
            except Exception as e:
                logger.warning(f"Intent detection failed: {str(e)}, using fallback")
                router_result = graceful_degradation.get_fallback_intent()
            
            # Use override if provided
            if routing_override:
                router_result["intent"] = routing_override
                router_result["reason"] = f"Intent overridden to {routing_override}"
            
            # Send start event with detected intent
            await self.sse_manager.send_event(
                client_id,
                "start",
                {
                    "request_id": request_id,
                    "timestamp": time.time(),
                    "intent": router_result["intent"],
                    "targets": router_result["targets"]
                }
            )
            
            # Step 2: Context Assembly
            await self.sse_manager.send_event(
                client_id,
                "progress",
                {
                    "request_id": request_id,
                    "timestamp": time.time(),
                    "progress": 0.3,
                    "status": "Assembling context"
                }
            )
            
            # Get context orchestrator
            context_orchestrator = None
            for tool in self.tools:
                if tool.name == "assemble_context":
                    context_orchestrator = tool
                    break
            
            if not context_orchestrator:
                raise Exception("Context orchestrator tool not found")
            
            # Assemble context with error handling
            try:
                context = await with_timeout(
                    context_orchestrator._execute(
                        project_id=project_id,
                        targets=router_result["targets"],
                        intent=router_result["intent"]
                    ),
                    timeout_seconds=agent_config.timeout_seconds * 2,
                    error_message="Context assembly timed out"
                )
            except Exception as e:
                logger.warning(f"Context assembly failed: {str(e)}, using minimal context")
                context = graceful_degradation.get_minimal_context(project_id)
            
            # Step 3: Analysis
            await self.sse_manager.send_event(
                client_id,
                "progress",
                {
                    "request_id": request_id,
                    "timestamp": time.time(),
                    "progress": 0.6,
                    "status": f"Performing {router_result['intent']} analysis"
                }
            )
            
            # Execute appropriate analysis tool
            result = await self._execute_analysis_tool(
                router_result["intent"],
                project_id,
                router_result["targets"],
                user_message,
                client_id,
                request_id
            )
            
            # Step 4: Finalization
            await self.sse_manager.send_event(
                client_id,
                "progress",
                {
                    "request_id": request_id,
                    "timestamp": time.time(),
                    "progress": 0.9,
                    "status": "Finalizing response"
                }
            )
            
            # Calculate metrics
            execution_time = time.time() - start_time
            metrics = {
                "execution_time_ms": int(execution_time * 1000),
                "request_id": request_id,
                "project_id": project_id,
                "intent": router_result["intent"],
                "tools_executed": 3,  # Router, Context, Analysis
                "confidence": router_result.get("confidence", 0.5)
            }
            
            # Send final event
            await self.sse_manager.send_event(
                client_id,
                "final",
                {
                    "request_id": request_id,
                    "timestamp": time.time(),
                    "result": result,
                    "metrics": metrics
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            
            # Handle error with comprehensive error handling
            error_response = error_handler.handle_agent_error(e, {
                "project_id": project_id,
                "user_message": user_message,
                "client_id": client_id,
                "request_id": request_id
            })
            
            # Create user-friendly message
            user_message = error_handler.create_user_friendly_message(e, {
                "project_id": project_id
            })
            
            await self.sse_manager.send_event(
                client_id,
                "error",
                {
                    "request_id": request_id,
                    "timestamp": time.time(),
                    "message": user_message,
                    "trace_id": request_id,
                    "error_code": error_response.get("error_code", "UNKNOWN_ERROR")
                }
            )
    
    async def _execute_analysis_tool(
        self,
        intent: str,
        project_id: str,
        targets: Dict[str, Any],
        user_message: str,
        client_id: str,
        request_id: str
    ) -> Any:
        """Execute the appropriate analysis tool based on intent."""
        
        # Map intents to tool names
        tool_mapping = {
            "integration_check": "integration_check_analysis",
            "requirements_coverage": "requirements_coverage_analysis",
            "improve_paragraph": "paragraph_improvement_analysis",
            "qna": "qna_response"
        }
        
        tool_name = tool_mapping.get(intent)
        if not tool_name:
            raise Exception(f"No tool found for intent: {intent}")
        
        # Find the tool
        analysis_tool = None
        for tool in self.tools:
            if tool.name == tool_name:
                analysis_tool = tool
                break
        
        if not analysis_tool:
            raise Exception(f"Analysis tool {tool_name} not found")
        
        # Send tool execution start event
        await self.sse_manager.send_event(
            client_id,
            "tool_execution",
            {
                "request_id": request_id,
                "timestamp": time.time(),
                "tool_name": tool_name,
                "status": "started"
            }
        )
        
        # Execute the tool
        if intent == "qna":
            # Q&A tool has different parameters
            result = await analysis_tool._execute(
                project_id=project_id,
                question=user_message,
                targets=targets,
                language="auto"
            )
        else:
            # Structured analysis tools
            result = await analysis_tool._execute(
                project_id=project_id,
                targets=targets,
                language="auto"
            )
        
        # Send tool execution completion event
        await self.sse_manager.send_event(
            client_id,
            "tool_execution",
            {
                "request_id": request_id,
                "timestamp": time.time(),
                "tool_name": tool_name,
                "status": "completed"
            }
        )
        
        return result
    
    async def _execute_agent_with_streaming(
        self,
        inputs: Dict[str, Any],
        callback_handler: AgentSSECallback,
        client_id: str,
        request_id: str
    ) -> Dict[str, Any]:
        """Execute the agent with streaming support."""
        try:
            # Execute the agent asynchronously
            result = await self.executor.ainvoke(
                inputs,
                config={"callbacks": [callback_handler]}
            )
            
            # Process the result
            output = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Try to parse as JSON for structured responses
            try:
                parsed_output = json.loads(output)
                if isinstance(parsed_output, dict):
                    return parsed_output
            except (json.JSONDecodeError, TypeError):
                # Return as plain text for qna responses
                pass
            
            return {
                "response": output,
                "type": "text",
                "intermediate_steps": len(intermediate_steps)
            }
            
        except Exception as e:
            logger.error(f"Error in agent execution: {str(e)}")
            raise LLMException(f"Agent execution failed: {str(e)}")
    
    async def stream_agent_execution(
        self,
        inputs: Dict[str, Any],
        client_id: str
    ) -> None:
        """Stream agent execution progress via SSE."""
        request_id = str(uuid.uuid4())
        
        try:
            # Create callback handler
            callback_handler = AgentSSECallback(client_id, self.sse_manager)
            
            # Execute with streaming
            await self._execute_agent_with_streaming(
                inputs,
                callback_handler,
                client_id,
                request_id
            )
            
        except Exception as e:
            logger.error(f"Error in streaming agent execution: {str(e)}")
            await self.sse_manager.send_event(
                client_id,
                "error",
                {
                    "request_id": request_id,
                    "timestamp": time.time(),
                    "message": str(e),
                    "trace_id": request_id
                }
            )
    
    def get_tool_info(self) -> List[Dict[str, Any]]:
        """Get information about available tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": getattr(tool, "tool_category", "unknown")
            }
            for tool in self.tools
        ]
    
    def reload_tools(self) -> None:
        """Reload tools from the registry."""
        self.tools = tool_registry.get_enabled_tools()
        logger.info(f"Reloaded {len(self.tools)} tools")


# Global agent instance (will be initialized when needed)
_agent_instance: Optional[SOAssistantAgent] = None


def get_agent_instance(sse_manager: SSEManager) -> SOAssistantAgent:
    """Get or create the global agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = SOAssistantAgent(sse_manager)
    return _agent_instance