"""Performance optimization utilities."""

import time
import logging
from functools import wraps
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from app.core.performance.requirement_items import (
    RequirementItemsPerformanceOptimizer,
    get_performance_optimizer
)

logger = logging.getLogger(__name__)


def timing_decorator(operation_name: str = None):
    """Decorator to measure execution time of functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                func_name = operation_name or f"{func.__module__}.{func.__name__}"
                logger.debug(f"TIMING: {func_name} executed in {execution_time:.3f}s")
                
                if execution_time > 1.0:
                    logger.warning(f"SLOW_FUNCTION: {func_name} took {execution_time:.3f}s")
        
        return wrapper
    return decorator


class PerformanceMonitor:
    """Simple performance monitoring utility."""
    
    def __init__(self):
        self.metrics = {}
    
    def record_timing(self, operation: str, execution_time: float):
        """Record timing for an operation."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(execution_time)
        
        # Keep only last 100 measurements
        if len(self.metrics[operation]) > 100:
            self.metrics[operation] = self.metrics[operation][-100:]
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        if operation not in self.metrics or not self.metrics[operation]:
            return {}
        
        times = self.metrics[operation]
        return {
            "count": len(times),
            "avg": sum(times) / len(times),
            "min": min(times),
            "max": max(times)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations."""
        return {op: self.get_stats(op) for op in self.metrics.keys()}


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


class CacheManager:
    """Simple cache manager for performance optimization."""
    
    def __init__(self):
        self.cache = {}
    
    def get(self, key: str):
        """Get value from cache."""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL."""
        self.cache[key] = {
            "value": value,
            "expires": time.time() + ttl
        }
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
    
    def cleanup_expired(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.cache.items()
            if data.get("expires", 0) < current_time
        ]
        for key in expired_keys:
            del self.cache[key]


# Global cache manager instance
cache_manager = CacheManager()


@asynccontextmanager
async def performance_context(operation_name: str, metadata: Optional[Dict] = None):
    """Context manager for timing operations."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        performance_monitor.record_timing(operation_name, duration)
        logger.debug(f"PERFORMANCE_CONTEXT: {operation_name} took {duration:.3f}s")


class PDFProcessingOptimizer:
    """Simple PDF processing optimizer."""
    
    @staticmethod
    async def process_with_timeout(coro, timeout: int = 30):
        """Process with timeout."""
        import asyncio
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception(f"Operation timed out after {timeout} seconds")


class LLMProcessingOptimizer:
    """Simple LLM processing optimizer."""
    
    @staticmethod
    async def optimize_prompt(prompt: str) -> str:
        """Optimize LLM prompt."""
        return prompt
    
    @staticmethod
    async def process_with_retry(coro, max_retries: int = 3):
        """Process with retry logic."""
        import asyncio
        for attempt in range(max_retries):
            try:
                return await coro
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff


def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report."""
    return {
        "performance_monitor": performance_monitor.get_all_stats(),
        "cache_stats": {
            "entries": len(cache_manager.cache),
            "memory_usage": "unknown"
        },
        "timestamp": time.time()
    }


__all__ = [
    "RequirementItemsPerformanceOptimizer",
    "get_performance_optimizer",
    "timing_decorator",
    "performance_monitor",
    "PerformanceMonitor",
    "cache_manager",
    "CacheManager",
    "get_performance_report",
    "performance_context",
    "PDFProcessingOptimizer",
    "LLMProcessingOptimizer"
]