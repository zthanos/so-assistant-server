"""Performance optimization utilities for requirements versioning system."""

import time
import asyncio
import functools
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
    
    def record_timing(self, operation: str, duration: float, metadata: Optional[Dict] = None):
        """Record timing for an operation."""
        with self.lock:
            self.metrics[f"{operation}_duration"].append({
                'timestamp': datetime.utcnow(),
                'duration': duration,
                'metadata': metadata or {}
            })
            self.counters[f"{operation}_count"] += 1
    
    def record_counter(self, metric: str, value: int = 1):
        """Record a counter metric."""
        with self.lock:
            self.counters[metric] += value
    
    def get_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for an operation."""
        with self.lock:
            durations = [m['duration'] for m in self.metrics[f"{operation}_duration"]]
            
            if not durations:
                return {'count': 0}
            
            return {
                'count': len(durations),
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'recent_avg': sum(durations[-10:]) / min(10, len(durations)),
                'total_calls': self.counters[f"{operation}_count"]
            }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get all performance statistics."""
        stats = {}
        operations = set()
        
        with self.lock:
            for key in self.metrics.keys():
                if key.endswith('_duration'):
                    operation = key[:-9]  # Remove '_duration'
                    operations.add(operation)
            
            for operation in operations:
                stats[operation] = self.get_stats(operation)
            
            # Add counter-only metrics
            for key, value in self.counters.items():
                if not any(key.startswith(op) for op in operations):
                    stats[key] = value
        
        return stats


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def timing_decorator(operation_name: str):
    """Decorator to automatically time function execution."""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    performance_monitor.record_timing(operation_name, duration)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    performance_monitor.record_timing(operation_name, duration)
            return sync_wrapper
    return decorator


@asynccontextmanager
async def performance_context(operation_name: str, metadata: Optional[Dict] = None):
    """Context manager for timing operations."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        performance_monitor.record_timing(operation_name, duration, metadata)


class DatabaseQueryOptimizer:
    """Optimize database queries for requirements documents."""
    
    @staticmethod
    def optimize_version_queries():
        """Provide optimized query patterns for version operations."""
        return {
            'latest_version': """
                SELECT * FROM requirement_documents 
                WHERE project_id = ? 
                ORDER BY version DESC 
                LIMIT 1
            """,
            'version_count': """
                SELECT COUNT(*) FROM requirement_documents 
                WHERE project_id = ?
            """,
            'paginated_versions': """
                SELECT * FROM requirement_documents 
                WHERE project_id = ? 
                ORDER BY version DESC 
                LIMIT ? OFFSET ?
            """,
            'filtered_versions': """
                SELECT * FROM requirement_documents 
                WHERE project_id = ? 
                AND status = ? 
                AND source_type = ?
                ORDER BY version DESC 
                LIMIT ? OFFSET ?
            """
        }
    
    @staticmethod
    def get_index_recommendations() -> List[str]:
        """Get recommended database indexes for performance."""
        return [
            "CREATE INDEX IF NOT EXISTS idx_req_docs_project_version_desc ON requirement_documents(project_id, version DESC)",
            "CREATE INDEX IF NOT EXISTS idx_req_docs_status_created ON requirement_documents(status, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_req_docs_source_created ON requirement_documents(source_type, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_req_docs_project_status_version ON requirement_documents(project_id, status, version DESC)"
        ]


class CacheManager:
    """Simple in-memory cache for frequently accessed data."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        self.cache: Dict[str, Dict] = {}
        self.default_ttl = default_ttl
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if datetime.utcnow() < entry['expires']:
                    performance_monitor.record_counter('cache_hit')
                    return entry['value']
                else:
                    del self.cache[key]
                    performance_monitor.record_counter('cache_expired')
            
            performance_monitor.record_counter('cache_miss')
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        expires = datetime.utcnow() + timedelta(seconds=ttl)
        
        with self.lock:
            self.cache[key] = {
                'value': value,
                'expires': expires,
                'created': datetime.utcnow()
            }
            performance_monitor.record_counter('cache_set')
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                performance_monitor.record_counter('cache_delete')
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            performance_monitor.record_counter('cache_clear', count)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        now = datetime.utcnow()
        expired_keys = []
        
        with self.lock:
            for key, entry in self.cache.items():
                if now >= entry['expires']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
        
        if expired_keys:
            performance_monitor.record_counter('cache_cleanup', len(expired_keys))
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_entries = len(self.cache)
            total_size = sum(len(str(entry['value'])) for entry in self.cache.values())
            
            return {
                'total_entries': total_entries,
                'estimated_size_bytes': total_size,
                'hit_rate': self._calculate_hit_rate()
            }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        hits = performance_monitor.counters.get('cache_hit', 0)
        misses = performance_monitor.counters.get('cache_miss', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return hits / total


# Global cache instance
cache_manager = CacheManager()


class PDFProcessingOptimizer:
    """Optimize PDF processing operations."""
    
    @staticmethod
    def get_processing_limits() -> Dict[str, Any]:
        """Get optimized processing limits."""
        return {
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'max_pages': 100,  # Limit pages processed
            'timeout_seconds': 30,  # Processing timeout
            'max_concurrent_uploads': 3,  # Concurrent processing limit
            'chunk_size': 1024 * 1024,  # 1MB chunks for large files
        }
    
    @staticmethod
    async def process_with_timeout(coro, timeout: float):
        """Process with timeout to prevent hanging."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            performance_monitor.record_counter('pdf_processing_timeout')
            raise
    
    @staticmethod
    def optimize_text_extraction(text: str) -> str:
        """Optimize extracted text for LLM processing."""
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                cleaned_lines.append(line)
        
        # Join with single newlines
        optimized_text = '\n'.join(cleaned_lines)
        
        # Limit text length for LLM processing
        max_length = 50000  # ~50KB limit
        if len(optimized_text) > max_length:
            optimized_text = optimized_text[:max_length] + "\n\n[Text truncated for processing]"
            performance_monitor.record_counter('pdf_text_truncated')
        
        return optimized_text


class LLMProcessingOptimizer:
    """Optimize LLM processing operations."""
    
    @staticmethod
    def optimize_prompt_size(prompt: str, max_tokens: int = 4000) -> str:
        """Optimize prompt size for LLM processing."""
        # Rough token estimation (1 token ≈ 4 characters)
        estimated_tokens = len(prompt) // 4
        
        if estimated_tokens <= max_tokens:
            return prompt
        
        # Truncate while preserving structure
        max_chars = max_tokens * 4
        truncated = prompt[:max_chars]
        
        # Try to truncate at a natural break point
        last_paragraph = truncated.rfind('\n\n')
        if last_paragraph > max_chars * 0.8:  # If we can save 80% of content
            truncated = truncated[:last_paragraph]
        
        truncated += "\n\n[Content truncated for processing]"
        performance_monitor.record_counter('llm_prompt_truncated')
        
        return truncated
    
    @staticmethod
    def get_retry_strategy() -> Dict[str, Any]:
        """Get optimized retry strategy for LLM calls."""
        return {
            'max_retries': 3,
            'base_delay': 1.0,  # seconds
            'max_delay': 10.0,  # seconds
            'exponential_base': 2.0,
            'jitter': True
        }


class MemoryOptimizer:
    """Optimize memory usage for large operations."""
    
    @staticmethod
    def process_in_chunks(data: List[Any], chunk_size: int = 100):
        """Process large datasets in chunks."""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]
    
    @staticmethod
    def cleanup_temp_data():
        """Clean up temporary data and caches."""
        cleaned_items = 0
        
        # Clean up expired cache entries
        cleaned_items += cache_manager.cleanup_expired()
        
        # Force garbage collection if needed
        import gc
        collected = gc.collect()
        
        performance_monitor.record_counter('memory_cleanup', cleaned_items)
        
        return {
            'cache_cleaned': cleaned_items,
            'gc_collected': collected
        }


def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report."""
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'performance_metrics': performance_monitor.get_all_stats(),
        'cache_stats': cache_manager.get_stats(),
        'system_info': {
            'cache_entries': len(cache_manager.cache),
            'active_operations': len(performance_monitor.metrics)
        }
    }


# Cleanup task to run periodically
async def periodic_cleanup():
    """Periodic cleanup task."""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            MemoryOptimizer.cleanup_temp_data()
            logger.info("Periodic cleanup completed")
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")


# Initialize cleanup task
def start_performance_monitoring():
    """Start performance monitoring background tasks."""
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(periodic_cleanup())
        logger.info("Performance monitoring started")
    except RuntimeError:
        # No event loop running, skip background tasks
        logger.info("No event loop available, skipping background tasks")