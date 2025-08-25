"""Caching mechanisms for agent operations."""
import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Union, Callable
from functools import wraps
import pickle

from app.services.agent.config import agent_config

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with TTL support."""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        """Initialize cache entry."""
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl or agent_config.cache_ttl_seconds
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.ttl <= 0:
            return False  # No expiration
        return time.time() - self.created_at > self.ttl
    
    def access(self) -> Any:
        """Access the cached value and update statistics."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache entry statistics."""
        return {
            "created_at": self.created_at,
            "ttl": self.ttl,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "age_seconds": time.time() - self.created_at,
            "is_expired": self.is_expired()
        }


class InMemoryCache:
    """In-memory cache with TTL and LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """Initialize cache."""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
                return None
            
            # Update access order
            self._access_order[key] = time.time()
            
            return entry.access()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        async with self._lock:
            # Clean up expired entries
            await self._cleanup_expired()
            
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_lru()
            
            # Store entry
            entry_ttl = ttl if ttl is not None else self.default_ttl
            self._cache[key] = CacheEntry(value, entry_ttl)
            self._access_order[key] = time.time()
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    async def _cleanup_expired(self) -> int:
        """Clean up expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                del self._access_order[key]
        
        return len(expired_keys)
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._access_order:
            return
        
        # Find LRU key
        lru_key = min(self._access_order.keys(), key=lambda k: self._access_order[k])
        
        # Remove from cache
        if lru_key in self._cache:
            del self._cache[lru_key]
        del self._access_order[lru_key]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            expired_count = await self._cleanup_expired()
            
            total_entries = len(self._cache)
            total_access_count = sum(entry.access_count for entry in self._cache.values())
            
            return {
                "total_entries": total_entries,
                "max_size": self.max_size,
                "utilization": total_entries / self.max_size if self.max_size > 0 else 0,
                "total_access_count": total_access_count,
                "expired_cleaned": expired_count,
                "average_age": sum(
                    time.time() - entry.created_at for entry in self._cache.values()
                ) / total_entries if total_entries > 0 else 0
            }


class DiagramCache(InMemoryCache):
    """Specialized cache for parsed diagrams."""
    
    def __init__(self):
        """Initialize diagram cache."""
        super().__init__(max_size=500, default_ttl=7200)  # 2 hours
    
    def _get_diagram_key(self, diagram_id: str, content_hash: str) -> str:
        """Get cache key for diagram."""
        return f"diagram:{diagram_id}:{content_hash}"
    
    def _hash_content(self, content: str) -> str:
        """Hash diagram content."""
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_parsed_diagram(self, diagram_id: str, content: str) -> Optional[Dict[str, Any]]:
        """Get parsed diagram from cache."""
        content_hash = self._hash_content(content)
        key = self._get_diagram_key(diagram_id, content_hash)
        return await self.get(key)
    
    async def set_parsed_diagram(self, diagram_id: str, content: str, parsed_data: Dict[str, Any]) -> None:
        """Set parsed diagram in cache."""
        content_hash = self._hash_content(content)
        key = self._get_diagram_key(diagram_id, content_hash)
        await self.set(key, parsed_data)


class IntentCache(InMemoryCache):
    """Specialized cache for intent detection results."""
    
    def __init__(self):
        """Initialize intent cache."""
        super().__init__(max_size=1000, default_ttl=1800)  # 30 minutes
    
    def _get_intent_key(self, message: str, language: str) -> str:
        """Get cache key for intent."""
        message_hash = hashlib.md5(message.lower().encode()).hexdigest()
        return f"intent:{language}:{message_hash}"
    
    async def get_intent_result(self, message: str, language: str) -> Optional[Dict[str, Any]]:
        """Get intent detection result from cache."""
        key = self._get_intent_key(message, language)
        return await self.get(key)
    
    async def set_intent_result(self, message: str, language: str, result: Dict[str, Any]) -> None:
        """Set intent detection result in cache."""
        key = self._get_intent_key(message, language)
        await self.set(key, result)


class ContextCache(InMemoryCache):
    """Specialized cache for assembled context."""
    
    def __init__(self):
        """Initialize context cache."""
        super().__init__(max_size=200, default_ttl=3600)  # 1 hour
    
    def _get_context_key(self, project_id: str, targets: Dict[str, Any], intent: str) -> str:
        """Get cache key for context."""
        targets_str = json.dumps(targets, sort_keys=True)
        targets_hash = hashlib.md5(targets_str.encode()).hexdigest()
        return f"context:{project_id}:{intent}:{targets_hash}"
    
    async def get_context(self, project_id: str, targets: Dict[str, Any], intent: str) -> Optional[Dict[str, Any]]:
        """Get assembled context from cache."""
        key = self._get_context_key(project_id, targets, intent)
        return await self.get(key)
    
    async def set_context(self, project_id: str, targets: Dict[str, Any], intent: str, context: Dict[str, Any]) -> None:
        """Set assembled context in cache."""
        key = self._get_context_key(project_id, targets, intent)
        await self.set(key, context)


def cached(
    cache_instance: InMemoryCache,
    key_func: Optional[Callable] = None,
    ttl: Optional[int] = None
):
    """Decorator for caching function results."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{func.__name__}:{hashlib.md5(args_str.encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = await cache_instance.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result
            
            # Execute function
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_instance.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to handle async cache operations
            loop = asyncio.get_event_loop()
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{func.__name__}:{hashlib.md5(args_str.encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = loop.run_until_complete(cache_instance.get(cache_key))
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result
            
            # Execute function
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            loop.run_until_complete(cache_instance.set(cache_key, result, ttl))
            
            return result
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global cache instances
diagram_cache = DiagramCache()
intent_cache = IntentCache()
context_cache = ContextCache()
general_cache = InMemoryCache()


async def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches."""
    return {
        "diagram_cache": await diagram_cache.get_stats(),
        "intent_cache": await intent_cache.get_stats(),
        "context_cache": await context_cache.get_stats(),
        "general_cache": await general_cache.get_stats()
    }


async def clear_all_caches() -> None:
    """Clear all caches."""
    await diagram_cache.clear()
    await intent_cache.clear()
    await context_cache.clear()
    await general_cache.clear()
    logger.info("All caches cleared")