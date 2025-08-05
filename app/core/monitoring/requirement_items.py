"""Monitoring and metrics for requirement items."""

import logging
import time
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RequirementItemsMetrics:
    """Metrics collector for requirement items operations."""
    
    def __init__(self):
        self.operation_counts = {}
        self.operation_times = {}
        self.error_counts = {}
        self.status_transitions = {}
        self.project_activity = {}
    
    def record_operation(self, operation: str, execution_time: float, success: bool = True):
        """Record an operation with its execution time and success status."""
        # Count operations
        if operation not in self.operation_counts:
            self.operation_counts[operation] = {"success": 0, "error": 0}
        
        if success:
            self.operation_counts[operation]["success"] += 1
        else:
            self.operation_counts[operation]["error"] += 1
        
        # Record execution times
        if operation not in self.operation_times:
            self.operation_times[operation] = []
        self.operation_times[operation].append(execution_time)
        
        # Keep only last 1000 measurements to prevent memory growth
        if len(self.operation_times[operation]) > 1000:
            self.operation_times[operation] = self.operation_times[operation][-1000:]
    
    def record_status_transition(self, from_status: str, to_status: str, project_id: str):
        """Record a status transition."""
        transition_key = f"{from_status}->{to_status}"
        
        if transition_key not in self.status_transitions:
            self.status_transitions[transition_key] = 0
        self.status_transitions[transition_key] += 1
        
        # Record project activity
        if project_id not in self.project_activity:
            self.project_activity[project_id] = {"transitions": 0, "last_activity": None}
        
        self.project_activity[project_id]["transitions"] += 1
        self.project_activity[project_id]["last_activity"] = datetime.utcnow()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        summary = {
            "operation_counts": self.operation_counts,
            "status_transitions": self.status_transitions,
            "project_activity_count": len(self.project_activity),
            "performance_stats": {}
        }
        
        # Calculate performance statistics
        for operation, times in self.operation_times.items():
            if times:
                summary["performance_stats"][operation] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "slow_queries": len([t for t in times if t > 1.0])
                }
        
        return summary
    
    def get_active_projects(self, hours: int = 24) -> Dict[str, Any]:
        """Get projects with activity in the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        active_projects = {}
        
        for project_id, activity in self.project_activity.items():
            if activity["last_activity"] and activity["last_activity"] > cutoff_time:
                active_projects[project_id] = activity
        
        return active_projects


# Global metrics instance
requirement_items_metrics = RequirementItemsMetrics()


def monitor_performance(operation_name: str):
    """Decorator to monitor performance of requirement items operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"Operation {operation_name} failed: {str(e)}")
                raise
            finally:
                execution_time = time.time() - start_time
                requirement_items_metrics.record_operation(operation_name, execution_time, success)
                
                # Log performance info
                if execution_time > 1.0:
                    logger.warning(f"SLOW_OPERATION: {operation_name} took {execution_time:.3f}s")
                else:
                    logger.debug(f"PERFORMANCE: {operation_name} completed in {execution_time:.3f}s")
        
        return wrapper
    return decorator


def log_status_transition(item_id: int, from_status: str, to_status: str, project_id: str):
    """Log a status transition for monitoring."""
    requirement_items_metrics.record_status_transition(from_status, to_status, project_id)
    
    logger.info(f"STATUS_TRANSITION: Item {item_id} in project {project_id} "
               f"changed from {from_status} to {to_status}")


def log_bulk_operation(operation: str, item_count: int, project_ids: list, execution_time: float):
    """Log bulk operations for monitoring."""
    logger.info(f"BULK_OPERATION: {operation} completed for {item_count} items "
               f"across {len(set(project_ids))} projects in {execution_time:.3f}s")
    
    if execution_time > 5.0:  # Warn on slow bulk operations
        logger.warning(f"SLOW_BULK_OPERATION: {operation} took {execution_time:.3f}s "
                      f"for {item_count} items")


def log_search_operation(project_id: str, search_term: str, result_count: int, execution_time: float):
    """Log search operations for monitoring."""
    logger.info(f"SEARCH_OPERATION: Project {project_id}, Term: '{search_term}', "
               f"Results: {result_count}, Time: {execution_time:.3f}s")
    
    if execution_time > 2.0:  # Warn on slow searches
        logger.warning(f"SLOW_SEARCH: Search in project {project_id} took {execution_time:.3f}s")


def get_health_status() -> Dict[str, Any]:
    """Get health status of requirement items system."""
    metrics = requirement_items_metrics.get_metrics_summary()
    
    # Calculate health indicators
    total_operations = sum(
        counts["success"] + counts["error"] 
        for counts in metrics["operation_counts"].values()
    )
    
    total_errors = sum(
        counts["error"] 
        for counts in metrics["operation_counts"].values()
    )
    
    error_rate = (total_errors / total_operations * 100) if total_operations > 0 else 0
    
    # Check for slow operations
    slow_operations = sum(
        stats.get("slow_queries", 0) 
        for stats in metrics["performance_stats"].values()
    )
    
    health_status = {
        "status": "healthy",
        "total_operations": total_operations,
        "error_rate_percent": round(error_rate, 2),
        "slow_operations": slow_operations,
        "active_projects_24h": len(requirement_items_metrics.get_active_projects(24)),
        "metrics": metrics
    }
    
    # Determine overall health
    if error_rate > 10:
        health_status["status"] = "unhealthy"
    elif error_rate > 5 or slow_operations > 10:
        health_status["status"] = "degraded"
    
    return health_status


def reset_metrics():
    """Reset all metrics (useful for testing or periodic cleanup)."""
    global requirement_items_metrics
    requirement_items_metrics = RequirementItemsMetrics()
    logger.info("Requirement items metrics reset")