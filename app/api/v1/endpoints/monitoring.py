"""API endpoints for monitoring and performance metrics."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from datetime import datetime, timedelta

try:
    from app.core.monitoring import (
        monitoring_dashboard,
        system_monitor,
        app_monitor,
        performance_logger,
        get_monitoring_report
    )
except ImportError:
    # Fallback for missing monitoring components
    monitoring_dashboard = None
    system_monitor = None
    app_monitor = None
    performance_logger = None
    
    def get_monitoring_report():
        return {"status": "monitoring_unavailable"}

try:
    from app.core.performance import (
        performance_monitor,
        cache_manager,
        get_performance_report
    )
except ImportError:
    # Fallback for missing performance components
    performance_monitor = None
    cache_manager = None
    
    def get_performance_report():
        return {"status": "performance_monitoring_unavailable"}
from app.services.optimized_requirement_document_service import concurrent_pdf_processor

router = APIRouter()


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Get system health status",
    description="Get overall system health and basic metrics."
)
def get_health_status():
    """Get system health status."""
    try:
        dashboard_data = monitoring_dashboard.get_dashboard_data()
        
        health_score = dashboard_data.get('health_score', 0)
        
        # Determine status based on health score
        if health_score >= 90:
            status_text = "healthy"
        elif health_score >= 70:
            status_text = "warning"
        elif health_score >= 50:
            status_text = "degraded"
        else:
            status_text = "critical"
        
        return {
            "status": status_text,
            "health_score": health_score,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": dashboard_data.get('system_metrics', {}).get('uptime_seconds', 0),
            "version": "1.0.0"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "health_score": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get(
    "/metrics",
    response_model=Dict[str, Any],
    summary="Get performance metrics",
    description="Get detailed performance metrics for all operations."
)
def get_performance_metrics():
    """Get comprehensive performance metrics."""
    try:
        return get_performance_report()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get(
    "/dashboard",
    response_model=Dict[str, Any],
    summary="Get monitoring dashboard data",
    description="Get comprehensive monitoring dashboard data including system metrics, performance, and alerts."
)
def get_dashboard_data():
    """Get monitoring dashboard data."""
    try:
        return get_monitoring_report()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.get(
    "/alerts",
    response_model=Dict[str, Any],
    summary="Get recent alerts",
    description="Get recent performance alerts and warnings."
)
def get_recent_alerts(
    minutes: int = Query(60, ge=1, le=1440, description="Number of minutes to look back for alerts")
):
    """Get recent performance alerts."""
    try:
        alerts = system_monitor.get_recent_alerts(minutes=minutes)
        
        return {
            "alerts": [
                {
                    "timestamp": alert.timestamp.isoformat(),
                    "alert_type": alert.alert_type,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "metrics": alert.metrics,
                    "threshold_exceeded": alert.threshold_exceeded
                }
                for alert in alerts
            ],
            "total_alerts": len(alerts),
            "time_range_minutes": minutes,
            "query_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.get(
    "/system",
    response_model=Dict[str, Any],
    summary="Get system metrics",
    description="Get current system resource usage metrics."
)
def get_system_metrics():
    """Get system resource metrics."""
    try:
        return system_monitor.get_system_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )


@router.get(
    "/cache",
    response_model=Dict[str, Any],
    summary="Get cache statistics",
    description="Get cache performance statistics and hit rates."
)
def get_cache_statistics():
    """Get cache statistics."""
    try:
        stats = cache_manager.get_stats()
        
        # Add additional cache information
        cache_info = {
            "statistics": stats,
            "performance_counters": {
                "cache_hit": performance_monitor.counters.get('cache_hit', 0),
                "cache_miss": performance_monitor.counters.get('cache_miss', 0),
                "cache_set": performance_monitor.counters.get('cache_set', 0),
                "cache_delete": performance_monitor.counters.get('cache_delete', 0),
                "cache_expired": performance_monitor.counters.get('cache_expired', 0),
                "cache_cleanup": performance_monitor.counters.get('cache_cleanup', 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return cache_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )


@router.post(
    "/cache/clear",
    response_model=Dict[str, Any],
    summary="Clear cache",
    description="Clear all cached data (use with caution)."
)
def clear_cache():
    """Clear all cached data."""
    try:
        entries_before = len(cache_manager.cache)
        cache_manager.clear()
        
        return {
            "success": True,
            "message": f"Cache cleared successfully",
            "entries_cleared": entries_before,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get(
    "/operations",
    response_model=Dict[str, Any],
    summary="Get operation statistics",
    description="Get statistics for specific operations like PDF processing, requirements creation, etc."
)
def get_operation_statistics(
    operation: Optional[str] = Query(None, description="Specific operation to get stats for")
):
    """Get operation-specific statistics."""
    try:
        all_stats = performance_monitor.get_all_stats()
        
        if operation:
            if operation in all_stats:
                return {
                    "operation": operation,
                    "statistics": all_stats[operation],
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Operation '{operation}' not found"
                )
        else:
            return {
                "all_operations": all_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get operation statistics: {str(e)}"
        )


@router.get(
    "/pdf-processing",
    response_model=Dict[str, Any],
    summary="Get PDF processing status",
    description="Get current PDF processing queue status and statistics."
)
def get_pdf_processing_status():
    """Get PDF processing status and statistics."""
    try:
        processor_status = concurrent_pdf_processor.get_status()
        
        # Get PDF-related performance metrics
        pdf_stats = {}
        all_stats = performance_monitor.get_all_stats()
        
        for key, stats in all_stats.items():
            if 'pdf' in key.lower() or 'upload' in key.lower():
                pdf_stats[key] = stats
        
        # Get PDF-related counters
        pdf_counters = {}
        for key, value in performance_monitor.counters.items():
            if 'pdf' in key.lower() or 'upload' in key.lower():
                pdf_counters[key] = value
        
        return {
            "processor_status": processor_status,
            "performance_statistics": pdf_stats,
            "counters": pdf_counters,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get PDF processing status: {str(e)}"
        )


@router.get(
    "/errors",
    response_model=Dict[str, Any],
    summary="Get error statistics",
    description="Get error rates and statistics for the current time window."
)
def get_error_statistics():
    """Get error statistics."""
    try:
        total_error_rate = app_monitor.get_error_rate()
        total_operation_rate = app_monitor.get_operation_rate()
        
        # Calculate error percentage
        error_percentage = 0.0
        if total_operation_rate > 0:
            error_percentage = (total_error_rate / total_operation_rate) * 100
        
        return {
            "error_rate_per_minute": total_error_rate,
            "operation_rate_per_minute": total_operation_rate,
            "error_percentage": error_percentage,
            "window_start": app_monitor.window_start.isoformat(),
            "window_duration_minutes": app_monitor.window_duration.total_seconds() / 60,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get error statistics: {str(e)}"
        )


@router.post(
    "/cleanup",
    response_model=Dict[str, Any],
    summary="Trigger cleanup operations",
    description="Trigger cleanup of expired cache entries and temporary data."
)
def trigger_cleanup():
    """Trigger cleanup operations."""
    try:
        from app.core.performance import MemoryOptimizer
        
        cleanup_results = MemoryOptimizer.cleanup_temp_data()
        
        return {
            "success": True,
            "message": "Cleanup completed successfully",
            "results": cleanup_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger cleanup: {str(e)}"
        )


@router.get(
    "/thresholds",
    response_model=Dict[str, Any],
    summary="Get performance thresholds",
    description="Get current performance monitoring thresholds and limits."
)
def get_performance_thresholds():
    """Get performance thresholds."""
    from app.core.monitoring import PerformanceThresholds
    
    return {
        "response_time": {
            "warning_seconds": PerformanceThresholds.RESPONSE_TIME_WARNING,
            "critical_seconds": PerformanceThresholds.RESPONSE_TIME_CRITICAL
        },
        "pdf_processing": {
            "warning_seconds": PerformanceThresholds.PDF_PROCESSING_WARNING,
            "critical_seconds": PerformanceThresholds.PDF_PROCESSING_CRITICAL
        },
        "cache_hit_rate": {
            "warning_threshold": PerformanceThresholds.CACHE_HIT_RATE_WARNING,
            "critical_threshold": PerformanceThresholds.CACHE_HIT_RATE_CRITICAL
        },
        "memory_usage": {
            "warning_percent": PerformanceThresholds.MEMORY_USAGE_WARNING,
            "critical_percent": PerformanceThresholds.MEMORY_USAGE_CRITICAL
        },
        "error_rate": {
            "warning_per_minute": PerformanceThresholds.ERROR_RATE_WARNING,
            "critical_per_minute": PerformanceThresholds.ERROR_RATE_CRITICAL
        },
        "timestamp": datetime.utcnow().isoformat()
    }