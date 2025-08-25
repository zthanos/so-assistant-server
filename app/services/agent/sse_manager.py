"""Enhanced SSE manager for agent streaming."""
import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional

from app.core.events import SSEManager
from app.services.agent.config import agent_config

logger = logging.getLogger(__name__)


class RequestTracker:
    """Track request execution state and metrics."""
    
    def __init__(self, request_id: str, project_id: str, intent: Optional[str] = None):
        """Initialize request tracker."""
        self.request_id = request_id
        self.project_id = project_id
        self.intent = intent
        self.start_time = time.time()
        self.last_activity = time.time()
        self.events_sent = 0
        self.tokens_streamed = 0
        self.tools_executed = []
        self.status = "active"
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
    
    def add_event(self, event_type: str) -> None:
        """Record an event being sent."""
        self.events_sent += 1
        self.update_activity()
    
    def add_token(self, token_count: int = 1) -> None:
        """Record tokens being streamed."""
        self.tokens_streamed += token_count
        self.update_activity()
    
    def add_tool_execution(self, tool_name: str) -> None:
        """Record tool execution."""
        self.tools_executed.append({
            "tool": tool_name,
            "timestamp": time.time()
        })
        self.update_activity()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        return {
            "request_id": self.request_id,
            "project_id": self.project_id,
            "intent": self.intent,
            "execution_time_ms": int((time.time() - self.start_time) * 1000),
            "events_sent": self.events_sent,
            "tokens_streamed": self.tokens_streamed,
            "tools_executed": len(self.tools_executed),
            "tool_details": self.tools_executed,
            "status": self.status
        }


class AgentSSEManager(SSEManager):
    """Enhanced SSE manager for agent execution streaming."""
    
    def __init__(self, connection_timeout: int = 3600):
        """Initialize the agent SSE manager."""
        super().__init__(connection_timeout)
        self.request_trackers: Dict[str, RequestTracker] = {}
        self.config = agent_config
    
    async def send_start_event(
        self,
        client_id: str,
        intent: str,
        targets: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> str:
        """Send initial processing event and create request tracker."""
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Create request tracker
        project_id = targets.get("project_id", "unknown")
        tracker = RequestTracker(request_id, project_id, intent)
        self.request_trackers[request_id] = tracker
        
        event_data = {
            "request_id": request_id,
            "timestamp": time.time(),
            "intent": intent,
            "targets": targets
        }
        
        success = await self.send_event(client_id, "start", event_data)
        if success:
            tracker.add_event("start")
        
        return request_id
    
    async def send_token_event(
        self,
        client_id: str,
        delta: str,
        request_id: Optional[str] = None
    ) -> None:
        """Send incremental content token."""
        event_data = {
            "timestamp": time.time(),
            "delta": delta
        }
        
        if request_id:
            event_data["request_id"] = request_id
            if request_id in self.request_trackers:
                self.request_trackers[request_id].add_token(len(delta))
        
        success = await self.send_event(client_id, "token", event_data)
        if success and request_id and request_id in self.request_trackers:
            self.request_trackers[request_id].add_event("token")
    
    async def send_json_event(
        self,
        client_id: str,
        partial_json: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> None:
        """Send partial JSON for structured responses."""
        event_data = {
            "timestamp": time.time(),
            "partial": partial_json
        }
        
        if request_id:
            event_data["request_id"] = request_id
        
        success = await self.send_event(client_id, "json", event_data)
        if success and request_id and request_id in self.request_trackers:
            self.request_trackers[request_id].add_event("json")
    
    async def send_final_event(
        self,
        client_id: str,
        result: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> None:
        """Send final result with metrics."""
        metrics = {}
        if request_id and request_id in self.request_trackers:
            tracker = self.request_trackers[request_id]
            tracker.status = "completed"
            metrics = tracker.get_metrics()
        
        event_data = {
            "timestamp": time.time(),
            "result": result,
            "metrics": metrics
        }
        
        if request_id:
            event_data["request_id"] = request_id
        
        success = await self.send_event(client_id, "final", event_data)
        if success and request_id and request_id in self.request_trackers:
            self.request_trackers[request_id].add_event("final")
    
    async def send_error_event(
        self,
        client_id: str,
        error: str,
        trace_id: str,
        request_id: Optional[str] = None
    ) -> None:
        """Send error event with trace information."""
        event_data = {
            "timestamp": time.time(),
            "message": error,
            "trace_id": trace_id
        }
        
        if request_id:
            event_data["request_id"] = request_id
            if request_id in self.request_trackers:
                tracker = self.request_trackers[request_id]
                tracker.status = "error"
        
        success = await self.send_event(client_id, "error", event_data)
        if success and request_id and request_id in self.request_trackers:
            self.request_trackers[request_id].add_event("error")
    
    async def send_tool_start_event(
        self,
        client_id: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> None:
        """Send tool execution start event."""
        event_data = {
            "timestamp": time.time(),
            "tool_name": tool_name,
            "tool_input": tool_input,
            "status": "started"
        }
        
        if request_id:
            event_data["request_id"] = request_id
            if request_id in self.request_trackers:
                self.request_trackers[request_id].add_tool_execution(tool_name)
        
        await self.send_event(client_id, "tool_execution", event_data)
    
    async def send_tool_end_event(
        self,
        client_id: str,
        tool_name: str,
        tool_output: Any,
        request_id: Optional[str] = None
    ) -> None:
        """Send tool execution completion event."""
        event_data = {
            "timestamp": time.time(),
            "tool_name": tool_name,
            "status": "completed",
            "output_preview": str(tool_output)[:200] + "..." if len(str(tool_output)) > 200 else str(tool_output)
        }
        
        if request_id:
            event_data["request_id"] = request_id
        
        await self.send_event(client_id, "tool_execution", event_data)
    
    async def send_progress_event(
        self,
        client_id: str,
        progress: float,
        status: str,
        request_id: Optional[str] = None
    ) -> None:
        """Send progress update event."""
        event_data = {
            "timestamp": time.time(),
            "progress": max(0.0, min(1.0, progress)),  # Clamp between 0 and 1
            "status": status
        }
        
        if request_id:
            event_data["request_id"] = request_id
        
        await self.send_event(client_id, "progress", event_data)
    
    def get_request_metrics(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific request."""
        if request_id in self.request_trackers:
            return self.request_trackers[request_id].get_metrics()
        return None
    
    def cleanup_completed_requests(self, max_age_seconds: int = 3600) -> int:
        """Clean up old completed request trackers."""
        current_time = time.time()
        to_remove = []
        
        for request_id, tracker in self.request_trackers.items():
            if (tracker.status in ["completed", "error"] and 
                current_time - tracker.last_activity > max_age_seconds):
                to_remove.append(request_id)
        
        for request_id in to_remove:
            del self.request_trackers[request_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} completed request trackers")
        
        return len(to_remove)
    
    async def stream_agent_execution(
        self,
        client_id: str,
        agent_executor,
        inputs: Dict[str, Any]
    ) -> None:
        """Stream agent execution with progress updates."""
        request_id = inputs.get("request_id", str(uuid.uuid4()))
        
        try:
            # Send initial progress
            await self.send_progress_event(client_id, 0.0, "Initializing agent", request_id)
            
            # Execute agent with streaming
            result = await agent_executor.ainvoke(inputs)
            
            # Send completion
            await self.send_progress_event(client_id, 1.0, "Agent execution completed", request_id)
            await self.send_final_event(client_id, result, request_id)
            
        except Exception as e:
            logger.error(f"Error in agent execution streaming: {str(e)}")
            await self.send_error_event(client_id, str(e), request_id, request_id)


# Global agent SSE manager instance
agent_sse_manager = AgentSSEManager()