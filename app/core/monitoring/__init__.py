"""Monitoring and metrics utilities."""

from app.core.monitoring.requirement_items import (
    requirement_items_metrics,
    monitor_performance,
    log_status_transition,
    log_bulk_operation,
    log_search_operation,
    get_health_status,
    reset_metrics
)

# Import from the main monitoring module (avoiding circular imports)
try:
    import sys
    if 'app.core.monitoring' in sys.modules:
        # If the main monitoring module is already loaded, get references from it
        main_monitoring = sys.modules['app.core.monitoring']
        monitoring_dashboard = getattr(main_monitoring, 'monitoring_dashboard', None)
        system_monitor = getattr(main_monitoring, 'system_monitor', None)
        app_monitor = getattr(main_monitoring, 'app_monitor', None)
        performance_logger = getattr(main_monitoring, 'performance_logger', None)
        setup_monitoring = getattr(main_monitoring, 'setup_monitoring', lambda: None)
        get_monitoring_report = getattr(main_monitoring, 'get_monitoring_report', lambda: {"status": "unavailable"})
    else:
        # Fallback if main monitoring module is not loaded
        monitoring_dashboard = None
        system_monitor = None
        app_monitor = None
        performance_logger = None
        
        def setup_monitoring():
            """Fallback setup monitoring function."""
            pass
        
        def get_monitoring_report():
            """Fallback monitoring report function."""
            return {"status": "monitoring_unavailable"}
except Exception:
    # Fallback for any import issues
    monitoring_dashboard = None
    system_monitor = None
    app_monitor = None
    performance_logger = None
    
    def setup_monitoring():
        """Fallback setup monitoring function."""
        pass
    
    def get_monitoring_report():
        """Fallback monitoring report function."""
        return {"status": "monitoring_unavailable"}

__all__ = [
    "requirement_items_metrics",
    "monitor_performance",
    "log_status_transition", 
    "log_bulk_operation",
    "log_search_operation",
    "get_health_status",
    "reset_metrics",
    "monitoring_dashboard",
    "system_monitor",
    "app_monitor",
    "performance_logger",
    "setup_monitoring",
    "get_monitoring_report"
]