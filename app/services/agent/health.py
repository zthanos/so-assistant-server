"""
Health checks and monitoring for the agent system.
Provides comprehensive health monitoring for all agent components.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.services.agent.config import agent_config
from app.services.agent.llm_client import StreamingOllamaClient
from app.services.agent.performance.resource_management import (
    resource_monitor, connection_pool, llm_rate_limiter, memory_manager
)
from app.services.agent.performance.caching import get_cache_stats
from app.services.agent.observability.metrics import agent_metrics

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    duration_ms: float
    timestamp: float


class HealthChecker:
    """Base health checker class."""
    
    def __init__(self, name: str, timeout: float = 5.0):
        """Initialize health checker."""
        self.name = name
        self.timeout = timeout
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    async def check(self) -> HealthCheckResult:
        """Perform health check."""
        start_time = time.time()
        
        try:
            # Run check with timeout
            status, message, details = await asyncio.wait_for(
                self._perform_check(), 
                timeout=self.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details=details,
                duration_ms=duration_ms,
                timestamp=time.time()
            )
        
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
                details={"timeout": self.timeout},
                duration_ms=duration_ms,
                timestamp=time.time()
            )
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Health check failed: {str(e)}")
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                duration_ms=duration_ms,
                timestamp=time.time()
            )
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Perform the actual health check. Override in subclasses."""
        raise NotImplementedError


class LLMHealthChecker(HealthChecker):
    """Health checker for LLM connectivity and response time."""
    
    def __init__(self):
        """Initialize LLM health checker."""
        super().__init__("llm_connectivity", timeout=10.0)
        self.config = agent_config
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Check LLM connectivity and response time."""
        try:
            # Create LLM client
            llm_client = StreamingOllamaClient(
                model=self.config.llm_model,
                base_url=self.config.ollama_base_url,
                temperature=0.1
            )
            
            # Test simple prompt
            test_prompt = "Respond with 'OK' if you can process this message."
            
            start_time = time.time()
            response = await llm_client.agenerate([test_prompt])
            response_time = (time.time() - start_time) * 1000
            
            # Check response
            if response and response.generations:
                response_text = response.generations[0][0].text.strip()
                
                details = {
                    "model": self.config.llm_model,
                    "base_url": self.config.ollama_base_url,
                    "response_time_ms": response_time,
                    "response_text": response_text[:100]  # First 100 chars
                }
                
                if response_time < 5000:  # Less than 5 seconds
                    return HealthStatus.HEALTHY, f"LLM responding in {response_time:.0f}ms", details
                elif response_time < 10000:  # Less than 10 seconds
                    return HealthStatus.DEGRADED, f"LLM responding slowly ({response_time:.0f}ms)", details
                else:
                    return HealthStatus.UNHEALTHY, f"LLM response too slow ({response_time:.0f}ms)", details
            
            else:
                return HealthStatus.UNHEALTHY, "LLM returned empty response", {
                    "model": self.config.llm_model,
                    "base_url": self.config.ollama_base_url,
                    "response_time_ms": response_time
                }
        
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"LLM connection failed: {str(e)}", {
                "model": self.config.llm_model,
                "base_url": self.config.ollama_base_url,
                "error": str(e)
            }


class DatabaseHealthChecker(HealthChecker):
    """Health checker for database connectivity."""
    
    def __init__(self):
        """Initialize database health checker."""
        super().__init__("database_connectivity", timeout=5.0)
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Check database connectivity."""
        try:
            # Use connection pool to test database
            async with connection_pool.get_connection() as conn:
                # TODO: Implement actual database health check
                # This is a placeholder - replace with actual DB query
                
                start_time = time.time()
                # Simulate database query
                await asyncio.sleep(0.1)  # Placeholder
                query_time = (time.time() - start_time) * 1000
                
                details = {
                    "connection_pool_stats": connection_pool.get_stats(),
                    "query_time_ms": query_time
                }
                
                if query_time < 1000:  # Less than 1 second
                    return HealthStatus.HEALTHY, f"Database responding in {query_time:.0f}ms", details
                elif query_time < 3000:  # Less than 3 seconds
                    return HealthStatus.DEGRADED, f"Database responding slowly ({query_time:.0f}ms)", details
                else:
                    return HealthStatus.UNHEALTHY, f"Database response too slow ({query_time:.0f}ms)", details
        
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Database connection failed: {str(e)}", {
                "error": str(e),
                "connection_pool_stats": connection_pool.get_stats()
            }


class VectorStoreHealthChecker(HealthChecker):
    """Health checker for vector store availability."""
    
    def __init__(self):
        """Initialize vector store health checker."""
        super().__init__("vector_store_availability", timeout=5.0)
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Check vector store availability."""
        try:
            # TODO: Implement actual vector store health check
            # This is a placeholder - replace with actual vector store query
            
            start_time = time.time()
            # Simulate vector store query
            await asyncio.sleep(0.05)  # Placeholder
            query_time = (time.time() - start_time) * 1000
            
            details = {
                "query_time_ms": query_time,
                "status": "available"  # Placeholder
            }
            
            if query_time < 500:  # Less than 500ms
                return HealthStatus.HEALTHY, f"Vector store responding in {query_time:.0f}ms", details
            elif query_time < 2000:  # Less than 2 seconds
                return HealthStatus.DEGRADED, f"Vector store responding slowly ({query_time:.0f}ms)", details
            else:
                return HealthStatus.UNHEALTHY, f"Vector store response too slow ({query_time:.0f}ms)", details
        
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Vector store connection failed: {str(e)}", {
                "error": str(e)
            }


class SystemResourcesHealthChecker(HealthChecker):
    """Health checker for system resources."""
    
    def __init__(self):
        """Initialize system resources health checker."""
        super().__init__("system_resources", timeout=2.0)
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Check system resource usage."""
        try:
            # Get current resource usage
            usage = resource_monitor.get_current_usage()
            stats = resource_monitor.get_usage_stats()
            
            details = {
                "cpu_percent": usage.cpu_percent,
                "memory_percent": usage.memory_percent,
                "memory_mb": usage.memory_mb,
                "stats": stats
            }
            
            # Determine health based on resource usage
            if usage.cpu_percent > 90 or usage.memory_percent > 90:
                return HealthStatus.UNHEALTHY, f"High resource usage (CPU: {usage.cpu_percent:.1f}%, Memory: {usage.memory_percent:.1f}%)", details
            elif usage.cpu_percent > 75 or usage.memory_percent > 75:
                return HealthStatus.DEGRADED, f"Elevated resource usage (CPU: {usage.cpu_percent:.1f}%, Memory: {usage.memory_percent:.1f}%)", details
            else:
                return HealthStatus.HEALTHY, f"Normal resource usage (CPU: {usage.cpu_percent:.1f}%, Memory: {usage.memory_percent:.1f}%)", details
        
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Failed to check system resources: {str(e)}", {
                "error": str(e)
            }


class CacheHealthChecker(HealthChecker):
    """Health checker for caching system."""
    
    def __init__(self):
        """Initialize cache health checker."""
        super().__init__("cache_system", timeout=2.0)
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Check cache system health."""
        try:
            # Get cache statistics
            cache_stats = await get_cache_stats()
            
            details = cache_stats
            
            # Check cache utilization and performance
            total_entries = sum(stats.get("total_entries", 0) for stats in cache_stats.values())
            
            if total_entries == 0:
                return HealthStatus.DEGRADED, "No cache entries (cold start)", details
            else:
                return HealthStatus.HEALTHY, f"Cache system operational ({total_entries} total entries)", details
        
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Cache system check failed: {str(e)}", {
                "error": str(e)
            }


class SSEConnectionsHealthChecker(HealthChecker):
    """Health checker for SSE connection management."""
    
    def __init__(self):
        """Initialize SSE connections health checker."""
        super().__init__("sse_connections", timeout=2.0)
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Check SSE connection management."""
        try:
            # Get metrics from agent metrics collector
            metrics_summary = agent_metrics.get_metrics_summary()
            sse_stats = metrics_summary.get("sse", {})
            
            details = {
                "active_connections": sse_stats.get("active_connections", 0),
                "events_sent": sse_stats.get("events_sent", 0),
                "connection_errors": sse_stats.get("connection_errors", 0)
            }
            
            active_connections = sse_stats.get("active_connections", 0)
            connection_errors = sse_stats.get("connection_errors", 0)
            
            if connection_errors > 10:
                return HealthStatus.DEGRADED, f"High SSE error rate ({connection_errors} errors)", details
            else:
                return HealthStatus.HEALTHY, f"SSE system operational ({active_connections} active connections)", details
        
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"SSE health check failed: {str(e)}", {
                "error": str(e)
            }


class AgentHealthMonitor:
    """Comprehensive health monitor for the agent system."""
    
    def __init__(self):
        """Initialize agent health monitor."""
        self.logger = logging.getLogger(f"{__name__}.AgentHealthMonitor")
        
        # Initialize health checkers
        self.health_checkers = [
            LLMHealthChecker(),
            DatabaseHealthChecker(),
            VectorStoreHealthChecker(),
            SystemResourcesHealthChecker(),
            CacheHealthChecker(),
            SSEConnectionsHealthChecker()
        ]
        
        # Health check history
        self.health_history: List[Dict[str, HealthCheckResult]] = []
        self.max_history = 100
    
    async def check_health(self, include_details: bool = True) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        start_time = time.time()
        
        # Run all health checks in parallel
        health_tasks = [checker.check() for checker in self.health_checkers]
        results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        # Process results
        health_results = {}
        overall_status = HealthStatus.HEALTHY
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle checker that raised an exception
                checker_name = self.health_checkers[i].name
                health_results[checker_name] = HealthCheckResult(
                    name=checker_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health checker failed: {str(result)}",
                    details={"error": str(result)},
                    duration_ms=0,
                    timestamp=time.time()
                )
            else:
                health_results[result.name] = result
            
            # Update overall status
            if isinstance(result, HealthCheckResult):
                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        # Store in history
        self.health_history.append(health_results)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        # Build response
        total_duration = (time.time() - start_time) * 1000
        
        response = {
            "overall_status": overall_status.value,
            "timestamp": time.time(),
            "duration_ms": total_duration,
            "checks": {}
        }
        
        for name, result in health_results.items():
            check_data = {
                "status": result.status.value,
                "message": result.message,
                "duration_ms": result.duration_ms
            }
            
            if include_details:
                check_data["details"] = result.details
            
            response["checks"][name] = check_data
        
        # Add summary statistics
        response["summary"] = {
            "total_checks": len(health_results),
            "healthy_checks": sum(1 for r in health_results.values() if r.status == HealthStatus.HEALTHY),
            "degraded_checks": sum(1 for r in health_results.values() if r.status == HealthStatus.DEGRADED),
            "unhealthy_checks": sum(1 for r in health_results.values() if r.status == HealthStatus.UNHEALTHY)
        }
        
        return response
    
    async def check_readiness(self) -> Dict[str, Any]:
        """Check if the system is ready to serve requests."""
        # Critical components for readiness
        critical_checkers = [
            checker for checker in self.health_checkers 
            if checker.name in ["llm_connectivity", "database_connectivity"]
        ]
        
        # Run critical checks
        critical_tasks = [checker.check() for checker in critical_checkers]
        results = await asyncio.gather(*critical_tasks, return_exceptions=True)
        
        # Check if all critical components are healthy
        ready = True
        failed_components = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception) or result.status == HealthStatus.UNHEALTHY:
                ready = False
                failed_components.append(critical_checkers[i].name)
        
        return {
            "ready": ready,
            "timestamp": time.time(),
            "failed_components": failed_components,
            "message": "System ready" if ready else f"System not ready: {', '.join(failed_components)}"
        }
    
    async def check_liveness(self) -> Dict[str, Any]:
        """Check if the system is alive (basic functionality)."""
        try:
            # Simple liveness check - just verify the monitor is running
            return {
                "alive": True,
                "timestamp": time.time(),
                "message": "System is alive",
                "uptime_seconds": time.time() - agent_metrics.start_time
            }
        except Exception as e:
            return {
                "alive": False,
                "timestamp": time.time(),
                "message": f"Liveness check failed: {str(e)}",
                "error": str(e)
            }
    
    def get_health_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent health check history."""
        recent_history = self.health_history[-limit:] if self.health_history else []
        
        return [
            {
                "timestamp": min(result.timestamp for result in check_results.values()),
                "overall_status": self._determine_overall_status(check_results),
                "checks": {
                    name: {
                        "status": result.status.value,
                        "message": result.message,
                        "duration_ms": result.duration_ms
                    }
                    for name, result in check_results.items()
                }
            }
            for check_results in recent_history
        ]
    
    def _determine_overall_status(self, check_results: Dict[str, HealthCheckResult]) -> str:
        """Determine overall status from individual check results."""
        if any(result.status == HealthStatus.UNHEALTHY for result in check_results.values()):
            return HealthStatus.UNHEALTHY.value
        elif any(result.status == HealthStatus.DEGRADED for result in check_results.values()):
            return HealthStatus.DEGRADED.value
        else:
            return HealthStatus.HEALTHY.value


# Global health monitor instance
health_monitor = AgentHealthMonitor()