"""Resource management for agent operations."""
import asyncio
import logging
import psutil
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

from app.services.agent.config import agent_config

logger = logging.getLogger(__name__)


@dataclass
class ResourceUsage:
    """Resource usage statistics."""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    active_connections: int
    active_requests: int
    timestamp: float


class ResourceMonitor:
    """Monitor system resource usage."""
    
    def __init__(self, check_interval: float = 5.0):
        """Initialize resource monitor."""
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.usage_history: list[ResourceUsage] = []
        self.max_history = 100
        
        # Resource limits
        self.cpu_limit = 80.0  # 80% CPU
        self.memory_limit = 85.0  # 85% Memory
        
    async def start_monitoring(self) -> None:
        """Start resource monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Resource monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Resource monitoring stopped")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        try:
            while self.monitoring:
                usage = self.get_current_usage()
                self.usage_history.append(usage)
                
                # Keep history size limited
                if len(self.usage_history) > self.max_history:
                    self.usage_history.pop(0)
                
                # Check for resource pressure
                await self._check_resource_pressure(usage)
                
                await asyncio.sleep(self.check_interval)
        
        except asyncio.CancelledError:
            logger.debug("Resource monitoring cancelled")
        except Exception as e:
            logger.error(f"Error in resource monitoring: {str(e)}")
    
    def get_current_usage(self) -> ResourceUsage:
        """Get current resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_mb = memory.used / (1024 * 1024)
            
            # Connection counts (placeholder - would need actual tracking)
            active_connections = 0  # TODO: Get from SSE manager
            active_requests = 0     # TODO: Get from request tracker
            
            return ResourceUsage(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                active_connections=active_connections,
                active_requests=active_requests,
                timestamp=time.time()
            )
        
        except Exception as e:
            logger.error(f"Error getting resource usage: {str(e)}")
            return ResourceUsage(0, 0, 0, 0, 0, time.time())
    
    async def _check_resource_pressure(self, usage: ResourceUsage) -> None:
        """Check for resource pressure and take action."""
        
        # CPU pressure
        if usage.cpu_percent > self.cpu_limit:
            logger.warning(f"High CPU usage: {usage.cpu_percent:.1f}%")
            # TODO: Implement CPU pressure handling
        
        # Memory pressure
        if usage.memory_percent > self.memory_limit:
            logger.warning(f"High memory usage: {usage.memory_percent:.1f}%")
            # TODO: Implement memory pressure handling
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        if not self.usage_history:
            return {}
        
        recent_usage = self.usage_history[-10:]  # Last 10 readings
        
        return {
            "current": self.usage_history[-1].__dict__ if self.usage_history else None,
            "average_cpu": sum(u.cpu_percent for u in recent_usage) / len(recent_usage),
            "average_memory": sum(u.memory_percent for u in recent_usage) / len(recent_usage),
            "peak_cpu": max(u.cpu_percent for u in recent_usage),
            "peak_memory": max(u.memory_percent for u in recent_usage),
            "history_count": len(self.usage_history),
            "monitoring": self.monitoring
        }


class ConnectionPool:
    """Connection pool for database connections."""
    
    def __init__(self, max_connections: int = 10, min_connections: int = 2):
        """Initialize connection pool."""
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.connections: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.total_created = 0
        self.pool_lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the connection pool."""
        async with self.pool_lock:
            # Create minimum connections
            for _ in range(self.min_connections):
                conn = await self._create_connection()
                if conn:
                    await self.connections.put(conn)
                    self.active_connections += 1
        
        logger.info(f"Connection pool initialized with {self.active_connections} connections")
    
    async def _create_connection(self):
        """Create a new connection."""
        try:
            # TODO: Implement actual connection creation
            # This is a placeholder
            self.total_created += 1
            return f"connection_{self.total_created}"
        except Exception as e:
            logger.error(f"Failed to create connection: {str(e)}")
            return None
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        connection = None
        try:
            # Try to get existing connection
            try:
                connection = await asyncio.wait_for(self.connections.get(), timeout=5.0)
            except asyncio.TimeoutError:
                # Create new connection if pool is empty and under limit
                async with self.pool_lock:
                    if self.active_connections < self.max_connections:
                        connection = await self._create_connection()
                        if connection:
                            self.active_connections += 1
                    else:
                        raise Exception("Connection pool exhausted")
            
            if not connection:
                raise Exception("No connection available")
            
            yield connection
        
        finally:
            # Return connection to pool
            if connection:
                try:
                    await self.connections.put(connection)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {str(e)}")
                    async with self.pool_lock:
                        self.active_connections -= 1
    
    async def close_all(self) -> None:
        """Close all connections."""
        async with self.pool_lock:
            while not self.connections.empty():
                try:
                    conn = await self.connections.get()
                    # TODO: Implement actual connection closing
                    self.active_connections -= 1
                except Exception as e:
                    logger.error(f"Error closing connection: {str(e)}")
        
        logger.info("All connections closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "max_connections": self.max_connections,
            "min_connections": self.min_connections,
            "active_connections": self.active_connections,
            "available_connections": self.connections.qsize(),
            "total_created": self.total_created
        }


class RequestRateLimiter:
    """Rate limiter for LLM requests."""
    
    def __init__(self, max_requests: int = 10, time_window: float = 60.0):
        """Initialize rate limiter."""
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: list[float] = []
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire permission to make a request."""
        async with self.lock:
            now = time.time()
            
            # Remove old requests outside time window
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.time_window]
            
            # Check if we can make a new request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False
    
    async def wait_for_slot(self) -> None:
        """Wait until a slot becomes available."""
        while not await self.acquire():
            await asyncio.sleep(0.1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        now = time.time()
        recent_requests = [req_time for req_time in self.requests 
                          if now - req_time < self.time_window]
        
        return {
            "max_requests": self.max_requests,
            "time_window": self.time_window,
            "current_requests": len(recent_requests),
            "available_slots": self.max_requests - len(recent_requests),
            "next_slot_available": min(self.requests) + self.time_window if self.requests else now
        }


class MemoryManager:
    """Memory management for large context processing."""
    
    def __init__(self, max_memory_mb: int = 1000):
        """Initialize memory manager."""
        self.max_memory_mb = max_memory_mb
        self.allocated_objects: Dict[str, Any] = {}
        self.allocation_sizes: Dict[str, int] = {}
        self.total_allocated = 0
        self.lock = asyncio.Lock()
    
    async def allocate(self, key: str, obj: Any, size_mb: Optional[int] = None) -> bool:
        """Allocate memory for an object."""
        async with self.lock:
            if size_mb is None:
                # Estimate size (rough approximation)
                size_mb = len(str(obj)) / (1024 * 1024)
            
            # Check if allocation would exceed limit
            if self.total_allocated + size_mb > self.max_memory_mb:
                # Try to free some memory
                await self._cleanup_old_allocations()
                
                if self.total_allocated + size_mb > self.max_memory_mb:
                    logger.warning(f"Memory allocation failed: {size_mb}MB would exceed limit")
                    return False
            
            # Allocate
            self.allocated_objects[key] = obj
            self.allocation_sizes[key] = size_mb
            self.total_allocated += size_mb
            
            logger.debug(f"Allocated {size_mb:.2f}MB for {key}")
            return True
    
    async def deallocate(self, key: str) -> bool:
        """Deallocate memory for an object."""
        async with self.lock:
            if key in self.allocated_objects:
                size_mb = self.allocation_sizes[key]
                del self.allocated_objects[key]
                del self.allocation_sizes[key]
                self.total_allocated -= size_mb
                
                logger.debug(f"Deallocated {size_mb:.2f}MB for {key}")
                return True
            
            return False
    
    async def get_object(self, key: str) -> Optional[Any]:
        """Get allocated object."""
        return self.allocated_objects.get(key)
    
    async def _cleanup_old_allocations(self) -> None:
        """Clean up old allocations to free memory."""
        # Simple LRU-style cleanup - remove oldest allocations
        # In a real implementation, you'd track access times
        
        if len(self.allocated_objects) > 10:  # Keep max 10 objects
            oldest_keys = list(self.allocated_objects.keys())[:5]  # Remove 5 oldest
            for key in oldest_keys:
                await self.deallocate(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics."""
        return {
            "max_memory_mb": self.max_memory_mb,
            "total_allocated_mb": self.total_allocated,
            "available_mb": self.max_memory_mb - self.total_allocated,
            "allocated_objects": len(self.allocated_objects),
            "utilization": self.total_allocated / self.max_memory_mb if self.max_memory_mb > 0 else 0
        }


# Global instances
resource_monitor = ResourceMonitor()
connection_pool = ConnectionPool(max_connections=20)
llm_rate_limiter = RequestRateLimiter(max_requests=agent_config.max_so_chunks, time_window=60.0)
memory_manager = MemoryManager(max_memory_mb=2000)


async def initialize_resource_management() -> None:
    """Initialize all resource management components."""
    await connection_pool.initialize()
    await resource_monitor.start_monitoring()
    logger.info("Resource management initialized")


async def shutdown_resource_management() -> None:
    """Shutdown all resource management components."""
    await resource_monitor.stop_monitoring()
    await connection_pool.close_all()
    logger.info("Resource management shutdown")


async def get_resource_stats() -> Dict[str, Any]:
    """Get comprehensive resource statistics."""
    return {
        "system": resource_monitor.get_usage_stats(),
        "connections": connection_pool.get_stats(),
        "rate_limiter": llm_rate_limiter.get_stats(),
        "memory": memory_manager.get_stats()
    }