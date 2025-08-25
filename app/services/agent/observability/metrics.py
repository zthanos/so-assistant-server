"""Comprehensive metrics collection for agent operations."""
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import statistics

from app.services.agent.observability.logging import metrics


class MetricType(str, Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class AgentMetrics:
    """Agent-specific metrics."""
    
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Intent detection metrics
    intent_detection_calls: int = 0
    intent_detection_successes: int = 0
    intent_detection_failures: int = 0
    intent_detection_cache_hits: int = 0
    
    # Context assembly metrics
    context_assembly_calls: int = 0
    context_assembly_successes: int = 0
    context_assembly_failures: int = 0
    context_assembly_cache_hits: int = 0
    
    # Analysis metrics
    analysis_calls: int = 0
    analysis_successes: int = 0
    analysis_failures: int = 0
    
    # Performance metrics
    request_durations: List[float] = field(default_factory=list)
    intent_detection_durations: List[float] = field(default_factory=list)
    context_assembly_durations: List[float] = field(default_factory=list)
    analysis_durations: List[float] = field(default_factory=list)
    
    # Token metrics
    total_tokens_processed: int = 0
    total_tokens_generated: int = 0
    
    # Tool execution metrics
    tool_executions: Dict[str, int] = field(default_factory=dict)
    tool_failures: Dict[str, int] = field(default_factory=dict)
    tool_durations: Dict[str, List[float]] = field(default_factory=dict)
    
    # SSE metrics
    sse_connections: int = 0
    sse_events_sent: int = 0
    sse_connection_errors: int = 0
    
    def get_success_rate(self) -> float:
        """Get overall success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    def get_intent_detection_success_rate(self) -> float:
        """Get intent detection success rate."""
        if self.intent_detection_calls == 0:
            return 0.0
        return self.intent_detection_successes / self.intent_detection_calls
    
    def get_context_assembly_success_rate(self) -> float:
        """Get context assembly success rate."""
        if self.context_assembly_calls == 0:
            return 0.0
        return self.context_assembly_successes / self.context_assembly_calls
    
    def get_analysis_success_rate(self) -> float:
        """Get analysis success rate."""
        if self.analysis_calls == 0:
            return 0.0
        return self.analysis_successes / self.analysis_calls
    
    def get_average_request_duration(self) -> float:
        """Get average request duration."""
        if not self.request_durations:
            return 0.0
        return statistics.mean(self.request_durations)
    
    def get_p95_request_duration(self) -> float:
        """Get 95th percentile request duration."""
        if not self.request_durations:
            return 0.0
        return statistics.quantiles(self.request_durations, n=20)[18]  # 95th percentile
    
    def get_tool_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get tool execution statistics."""
        stats = {}
        
        for tool_name in self.tool_executions:
            executions = self.tool_executions.get(tool_name, 0)
            failures = self.tool_failures.get(tool_name, 0)
            durations = self.tool_durations.get(tool_name, [])
            
            stats[tool_name] = {
                "executions": executions,
                "failures": failures,
                "success_rate": (executions - failures) / executions if executions > 0 else 0.0,
                "average_duration": statistics.mean(durations) if durations else 0.0,
                "p95_duration": statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else (max(durations) if durations else 0.0)
            }
        
        return stats


class AgentMetricsCollector:
    """Collector for agent-specific metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = AgentMetrics()
        self.start_time = time.time()
    
    # Request metrics
    def record_request_start(self) -> str:
        """Record request start and return timer ID."""
        self.metrics.total_requests += 1
        metrics.increment_counter("agent.requests.total")
        return metrics.start_timer("agent.request.duration")
    
    def record_request_success(self, timer_id: str, tokens_processed: int = 0, tokens_generated: int = 0):
        """Record successful request."""
        self.metrics.successful_requests += 1
        self.metrics.total_tokens_processed += tokens_processed
        self.metrics.total_tokens_generated += tokens_generated
        
        duration = metrics.end_timer("agent.request.duration", timer_id)
        self.metrics.request_durations.append(duration)
        
        metrics.increment_counter("agent.requests.success")
        metrics.increment_counter("agent.tokens.processed", tokens_processed)
        metrics.increment_counter("agent.tokens.generated", tokens_generated)
    
    def record_request_failure(self, timer_id: str, error_type: str = "unknown"):
        """Record failed request."""
        self.metrics.failed_requests += 1
        
        duration = metrics.end_timer("agent.request.duration", timer_id)
        self.metrics.request_durations.append(duration)
        
        metrics.increment_counter("agent.requests.failure")
        metrics.increment_counter("agent.requests.failure_by_type", tags={"error_type": error_type})
    
    # Intent detection metrics
    def record_intent_detection_start(self) -> str:
        """Record intent detection start."""
        self.metrics.intent_detection_calls += 1
        metrics.increment_counter("agent.intent_detection.calls")
        return metrics.start_timer("agent.intent_detection.duration")
    
    def record_intent_detection_success(self, timer_id: str, intent: str, confidence: float, cache_hit: bool = False):
        """Record successful intent detection."""
        self.metrics.intent_detection_successes += 1
        if cache_hit:
            self.metrics.intent_detection_cache_hits += 1
        
        duration = metrics.end_timer("agent.intent_detection.duration", timer_id)
        self.metrics.intent_detection_durations.append(duration)
        
        metrics.increment_counter("agent.intent_detection.success")
        metrics.increment_counter("agent.intent_detection.by_intent", tags={"intent": intent})
        metrics.record_histogram("agent.intent_detection.confidence", confidence)
        
        if cache_hit:
            metrics.increment_counter("agent.intent_detection.cache_hits")
    
    def record_intent_detection_failure(self, timer_id: str, error_type: str = "unknown"):
        """Record failed intent detection."""
        self.metrics.intent_detection_failures += 1
        
        duration = metrics.end_timer("agent.intent_detection.duration", timer_id)
        self.metrics.intent_detection_durations.append(duration)
        
        metrics.increment_counter("agent.intent_detection.failure")
        metrics.increment_counter("agent.intent_detection.failure_by_type", tags={"error_type": error_type})
    
    # Context assembly metrics
    def record_context_assembly_start(self) -> str:
        """Record context assembly start."""
        self.metrics.context_assembly_calls += 1
        metrics.increment_counter("agent.context_assembly.calls")
        return metrics.start_timer("agent.context_assembly.duration")
    
    def record_context_assembly_success(self, timer_id: str, context_size: int, cache_hit: bool = False):
        """Record successful context assembly."""
        self.metrics.context_assembly_successes += 1
        if cache_hit:
            self.metrics.context_assembly_cache_hits += 1
        
        duration = metrics.end_timer("agent.context_assembly.duration", timer_id)
        self.metrics.context_assembly_durations.append(duration)
        
        metrics.increment_counter("agent.context_assembly.success")
        metrics.record_histogram("agent.context_assembly.size", context_size)
        
        if cache_hit:
            metrics.increment_counter("agent.context_assembly.cache_hits")
    
    def record_context_assembly_failure(self, timer_id: str, error_type: str = "unknown"):
        """Record failed context assembly."""
        self.metrics.context_assembly_failures += 1
        
        duration = metrics.end_timer("agent.context_assembly.duration", timer_id)
        self.metrics.context_assembly_durations.append(duration)
        
        metrics.increment_counter("agent.context_assembly.failure")
        metrics.increment_counter("agent.context_assembly.failure_by_type", tags={"error_type": error_type})
    
    # Analysis metrics
    def record_analysis_start(self, intent: str) -> str:
        """Record analysis start."""
        self.metrics.analysis_calls += 1
        metrics.increment_counter("agent.analysis.calls")
        metrics.increment_counter("agent.analysis.calls_by_intent", tags={"intent": intent})
        return metrics.start_timer("agent.analysis.duration", tags={"intent": intent})
    
    def record_analysis_success(self, timer_id: str, intent: str, suggestions_count: int = 0):
        """Record successful analysis."""
        self.metrics.analysis_successes += 1
        
        duration = metrics.end_timer("agent.analysis.duration", timer_id, tags={"intent": intent})
        self.metrics.analysis_durations.append(duration)
        
        metrics.increment_counter("agent.analysis.success")
        metrics.increment_counter("agent.analysis.success_by_intent", tags={"intent": intent})
        metrics.record_histogram("agent.analysis.suggestions_count", suggestions_count, tags={"intent": intent})
    
    def record_analysis_failure(self, timer_id: str, intent: str, error_type: str = "unknown"):
        """Record failed analysis."""
        self.metrics.analysis_failures += 1
        
        duration = metrics.end_timer("agent.analysis.duration", timer_id, tags={"intent": intent})
        self.metrics.analysis_durations.append(duration)
        
        metrics.increment_counter("agent.analysis.failure")
        metrics.increment_counter("agent.analysis.failure_by_intent", tags={"intent": intent})
        metrics.increment_counter("agent.analysis.failure_by_type", tags={"error_type": error_type})
    
    # Tool execution metrics
    def record_tool_execution_start(self, tool_name: str) -> str:
        """Record tool execution start."""
        if tool_name not in self.metrics.tool_executions:
            self.metrics.tool_executions[tool_name] = 0
            self.metrics.tool_failures[tool_name] = 0
            self.metrics.tool_durations[tool_name] = []
        
        self.metrics.tool_executions[tool_name] += 1
        
        metrics.increment_counter("agent.tool.executions")
        metrics.increment_counter("agent.tool.executions_by_name", tags={"tool": tool_name})
        
        return metrics.start_timer("agent.tool.duration", tags={"tool": tool_name})
    
    def record_tool_execution_success(self, timer_id: str, tool_name: str):
        """Record successful tool execution."""
        duration = metrics.end_timer("agent.tool.duration", timer_id, tags={"tool": tool_name})
        self.metrics.tool_durations[tool_name].append(duration)
        
        metrics.increment_counter("agent.tool.success")
        metrics.increment_counter("agent.tool.success_by_name", tags={"tool": tool_name})
    
    def record_tool_execution_failure(self, timer_id: str, tool_name: str, error_type: str = "unknown"):
        """Record failed tool execution."""
        self.metrics.tool_failures[tool_name] += 1
        
        duration = metrics.end_timer("agent.tool.duration", timer_id, tags={"tool": tool_name})
        self.metrics.tool_durations[tool_name].append(duration)
        
        metrics.increment_counter("agent.tool.failure")
        metrics.increment_counter("agent.tool.failure_by_name", tags={"tool": tool_name})
        metrics.increment_counter("agent.tool.failure_by_type", tags={"error_type": error_type})
    
    # SSE metrics
    def record_sse_connection(self):
        """Record SSE connection."""
        self.metrics.sse_connections += 1
        metrics.increment_counter("agent.sse.connections")
        metrics.set_gauge("agent.sse.active_connections", self.metrics.sse_connections)
    
    def record_sse_disconnection(self):
        """Record SSE disconnection."""
        self.metrics.sse_connections = max(0, self.metrics.sse_connections - 1)
        metrics.set_gauge("agent.sse.active_connections", self.metrics.sse_connections)
    
    def record_sse_event_sent(self, event_type: str):
        """Record SSE event sent."""
        self.metrics.sse_events_sent += 1
        metrics.increment_counter("agent.sse.events_sent")
        metrics.increment_counter("agent.sse.events_sent_by_type", tags={"event_type": event_type})
    
    def record_sse_error(self, error_type: str = "unknown"):
        """Record SSE error."""
        self.metrics.sse_connection_errors += 1
        metrics.increment_counter("agent.sse.errors")
        metrics.increment_counter("agent.sse.errors_by_type", tags={"error_type": error_type})
    
    # Summary methods
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "requests": {
                "total": self.metrics.total_requests,
                "successful": self.metrics.successful_requests,
                "failed": self.metrics.failed_requests,
                "success_rate": self.metrics.get_success_rate(),
                "average_duration": self.metrics.get_average_request_duration(),
                "p95_duration": self.metrics.get_p95_request_duration(),
                "requests_per_second": self.metrics.total_requests / uptime if uptime > 0 else 0
            },
            "intent_detection": {
                "calls": self.metrics.intent_detection_calls,
                "successes": self.metrics.intent_detection_successes,
                "failures": self.metrics.intent_detection_failures,
                "success_rate": self.metrics.get_intent_detection_success_rate(),
                "cache_hits": self.metrics.intent_detection_cache_hits,
                "cache_hit_rate": self.metrics.intent_detection_cache_hits / self.metrics.intent_detection_calls if self.metrics.intent_detection_calls > 0 else 0
            },
            "context_assembly": {
                "calls": self.metrics.context_assembly_calls,
                "successes": self.metrics.context_assembly_successes,
                "failures": self.metrics.context_assembly_failures,
                "success_rate": self.metrics.get_context_assembly_success_rate(),
                "cache_hits": self.metrics.context_assembly_cache_hits,
                "cache_hit_rate": self.metrics.context_assembly_cache_hits / self.metrics.context_assembly_calls if self.metrics.context_assembly_calls > 0 else 0
            },
            "analysis": {
                "calls": self.metrics.analysis_calls,
                "successes": self.metrics.analysis_successes,
                "failures": self.metrics.analysis_failures,
                "success_rate": self.metrics.get_analysis_success_rate()
            },
            "tokens": {
                "processed": self.metrics.total_tokens_processed,
                "generated": self.metrics.total_tokens_generated,
                "tokens_per_request": self.metrics.total_tokens_processed / self.metrics.total_requests if self.metrics.total_requests > 0 else 0
            },
            "tools": self.metrics.get_tool_stats(),
            "sse": {
                "active_connections": self.metrics.sse_connections,
                "events_sent": self.metrics.sse_events_sent,
                "connection_errors": self.metrics.sse_connection_errors
            }
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = AgentMetrics()
        self.start_time = time.time()


# Global metrics collector instance
agent_metrics = AgentMetricsCollector()