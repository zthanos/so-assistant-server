"""Monitoring and logging enhancements for requirements versioning system."""

import time
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, deque
import os
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from app.core.performance import performance_monitor


class LogLevel(Enum):
    """Log levels for monitoring."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""
    timestamp: datetime
    alert_type: str
    severity: LogLevel
    message: str
    metrics: Dict[str, Any]
    threshold_exceeded: Optional[str] = None


class PerformanceThresholds:
    """Performance thresholds for alerting."""
    
    # Response time thresholds (seconds)
    RESPONSE_TIME_WARNING = 2.0
    RESPONSE_TIME_CRITICAL = 5.0
    
    # PDF processing thresholds
    PDF_PROCESSING_WARNING = 15.0  # seconds
    PDF_PROCESSING_CRITICAL = 30.0  # seconds
    
    # Cache hit rate thresholds
    CACHE_HIT_RATE_WARNING = 0.7  # 70%
    CACHE_HIT_RATE_CRITICAL = 0.5  # 50%
    
    # Memory usage thresholds (percentage)
    MEMORY_USAGE_WARNING = 80.0
    MEMORY_USAGE_CRITICAL = 90.0
    
    # Error rate thresholds (per minute)
    ERROR_RATE_WARNING = 10
    ERROR_RATE_CRITICAL = 25


class SystemMonitor:
    """Monitor system resources and performance."""
    
    def __init__(self):
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process(os.getpid())
        else:
            self.process = None
        self.start_time = datetime.utcnow()
        self.alerts: deque = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            if not PSUTIL_AVAILABLE or not self.process:
                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                    'psutil_available': False,
                    'message': 'System metrics require psutil package'
                }
            
            # CPU and memory usage
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # Disk usage for database
            disk_usage = psutil.disk_usage('.')
            
            # Network connections (if available)
            try:
                connections = len(self.process.connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'psutil_available': True,
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'rss_bytes': memory_info.rss,
                    'vms_bytes': memory_info.vms,
                    'percent': memory_percent,
                    'available_bytes': psutil.virtual_memory().available
                },
                'disk': {
                    'total_bytes': disk_usage.total,
                    'used_bytes': disk_usage.used,
                    'free_bytes': disk_usage.free,
                    'percent': (disk_usage.used / disk_usage.total) * 100
                },
                'network': {
                    'connections': connections
                }
            }
        except Exception as e:
            logging.error(f"Error getting system metrics: {e}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    def check_thresholds(self, metrics: Dict[str, Any]) -> List[PerformanceAlert]:
        """Check metrics against thresholds and generate alerts."""
        alerts = []
        
        # Check memory usage (only if psutil is available)
        if PSUTIL_AVAILABLE and 'memory' in metrics and 'percent' in metrics['memory']:
            memory_percent = metrics['memory']['percent']
            if memory_percent > PerformanceThresholds.MEMORY_USAGE_CRITICAL:
                alerts.append(PerformanceAlert(
                    timestamp=datetime.utcnow(),
                    alert_type="memory_usage",
                    severity=LogLevel.CRITICAL,
                    message=f"Critical memory usage: {memory_percent:.1f}%",
                    metrics={'memory_percent': memory_percent},
                    threshold_exceeded=f"{PerformanceThresholds.MEMORY_USAGE_CRITICAL}%"
                ))
            elif memory_percent > PerformanceThresholds.MEMORY_USAGE_WARNING:
                alerts.append(PerformanceAlert(
                    timestamp=datetime.utcnow(),
                    alert_type="memory_usage",
                    severity=LogLevel.WARNING,
                    message=f"High memory usage: {memory_percent:.1f}%",
                    metrics={'memory_percent': memory_percent},
                    threshold_exceeded=f"{PerformanceThresholds.MEMORY_USAGE_WARNING}%"
                ))
        
        return alerts
    
    def add_alert(self, alert: PerformanceAlert):
        """Add alert to the alert queue."""
        with self.lock:
            self.alerts.append(alert)
            
            # Log the alert
            log_level = getattr(logging, alert.severity.value)
            logging.log(log_level, f"Performance Alert: {alert.message}")
    
    def get_recent_alerts(self, minutes: int = 60) -> List[PerformanceAlert]:
        """Get alerts from the last N minutes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        with self.lock:
            return [alert for alert in self.alerts if alert.timestamp > cutoff_time]


class ApplicationMonitor:
    """Monitor application-specific metrics."""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.operation_counts = defaultdict(int)
        self.lock = threading.Lock()
        self.window_start = datetime.utcnow()
        self.window_duration = timedelta(minutes=1)
    
    def record_error(self, error_type: str, operation: str = None):
        """Record an error occurrence."""
        with self.lock:
            self.error_counts[error_type] += 1
            if operation:
                self.error_counts[f"{operation}_{error_type}"] += 1
            
            # Reset window if needed
            self._reset_window_if_needed()
    
    def record_operation(self, operation: str):
        """Record an operation occurrence."""
        with self.lock:
            self.operation_counts[operation] += 1
            self._reset_window_if_needed()
    
    def _reset_window_if_needed(self):
        """Reset counting window if duration exceeded."""
        if datetime.utcnow() - self.window_start > self.window_duration:
            self.error_counts.clear()
            self.operation_counts.clear()
            self.window_start = datetime.utcnow()
    
    def get_error_rate(self, error_type: str = None) -> float:
        """Get error rate per minute."""
        with self.lock:
            if error_type:
                return self.error_counts.get(error_type, 0)
            else:
                return sum(self.error_counts.values())
    
    def get_operation_rate(self, operation: str = None) -> float:
        """Get operation rate per minute."""
        with self.lock:
            if operation:
                return self.operation_counts.get(operation, 0)
            else:
                return sum(self.operation_counts.values())
    
    def check_error_thresholds(self) -> List[PerformanceAlert]:
        """Check error rates against thresholds."""
        alerts = []
        total_errors = self.get_error_rate()
        
        if total_errors > PerformanceThresholds.ERROR_RATE_CRITICAL:
            alerts.append(PerformanceAlert(
                timestamp=datetime.utcnow(),
                alert_type="error_rate",
                severity=LogLevel.CRITICAL,
                message=f"Critical error rate: {total_errors} errors/minute",
                metrics={'error_rate': total_errors},
                threshold_exceeded=str(PerformanceThresholds.ERROR_RATE_CRITICAL)
            ))
        elif total_errors > PerformanceThresholds.ERROR_RATE_WARNING:
            alerts.append(PerformanceAlert(
                timestamp=datetime.utcnow(),
                alert_type="error_rate",
                severity=LogLevel.WARNING,
                message=f"High error rate: {total_errors} errors/minute",
                metrics={'error_rate': total_errors},
                threshold_exceeded=str(PerformanceThresholds.ERROR_RATE_WARNING)
            ))
        
        return alerts


class PerformanceLogger:
    """Enhanced logging for performance monitoring."""
    
    def __init__(self, log_file: str = "performance.log"):
        self.log_file = log_file
        self.logger = logging.getLogger("performance")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler if not exists
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_operation_performance(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Log operation performance."""
        log_data = {
            'operation': operation,
            'duration_seconds': duration,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if metadata:
            log_data['metadata'] = metadata
        
        # Determine log level based on duration
        if operation.startswith('pdf_') and duration > PerformanceThresholds.PDF_PROCESSING_WARNING:
            level = logging.WARNING if duration < PerformanceThresholds.PDF_PROCESSING_CRITICAL else logging.ERROR
        elif duration > PerformanceThresholds.RESPONSE_TIME_WARNING:
            level = logging.WARNING if duration < PerformanceThresholds.RESPONSE_TIME_CRITICAL else logging.ERROR
        else:
            level = logging.INFO
        
        self.logger.log(level, f"Operation Performance: {json.dumps(log_data)}")
    
    def log_system_metrics(self, metrics: Dict[str, Any]):
        """Log system metrics."""
        self.logger.info(f"System Metrics: {json.dumps(metrics)}")
    
    def log_alert(self, alert: PerformanceAlert):
        """Log performance alert."""
        alert_data = asdict(alert)
        alert_data['timestamp'] = alert.timestamp.isoformat()
        
        level = getattr(logging, alert.severity.value)
        self.logger.log(level, f"Performance Alert: {json.dumps(alert_data)}")


class MonitoringDashboard:
    """Simple monitoring dashboard data provider."""
    
    def __init__(self, system_monitor: SystemMonitor, app_monitor: ApplicationMonitor):
        self.system_monitor = system_monitor
        self.app_monitor = app_monitor
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data."""
        # Get system metrics
        system_metrics = self.system_monitor.get_system_metrics()
        
        # Get performance metrics
        perf_metrics = performance_monitor.get_all_stats()
        
        # Get cache statistics
        from app.core.performance import cache_manager
        cache_stats = cache_manager.get_stats()
        
        # Get recent alerts
        recent_alerts = self.system_monitor.get_recent_alerts(minutes=60)
        
        # Calculate health score
        health_score = self._calculate_health_score(system_metrics, perf_metrics, cache_stats)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'health_score': health_score,
            'system_metrics': system_metrics,
            'performance_metrics': perf_metrics,
            'cache_statistics': cache_stats,
            'recent_alerts': [asdict(alert) for alert in recent_alerts],
            'error_rates': {
                'total_errors_per_minute': self.app_monitor.get_error_rate(),
                'total_operations_per_minute': self.app_monitor.get_operation_rate()
            }
        }
    
    def _calculate_health_score(self, system_metrics: Dict, perf_metrics: Dict, cache_stats: Dict) -> float:
        """Calculate overall system health score (0-100)."""
        score = 100.0
        
        # Deduct for high memory usage
        if 'memory' in system_metrics and 'percent' in system_metrics['memory']:
            memory_percent = system_metrics['memory']['percent']
            if memory_percent > PerformanceThresholds.MEMORY_USAGE_WARNING:
                score -= min(30, (memory_percent - PerformanceThresholds.MEMORY_USAGE_WARNING) * 2)
        
        # Deduct for slow operations
        for operation, stats in perf_metrics.items():
            if isinstance(stats, dict) and 'avg_duration' in stats:
                avg_duration = stats['avg_duration']
                if avg_duration > PerformanceThresholds.RESPONSE_TIME_WARNING:
                    score -= min(20, (avg_duration - PerformanceThresholds.RESPONSE_TIME_WARNING) * 10)
        
        # Deduct for low cache hit rate
        if 'hit_rate' in cache_stats:
            hit_rate = cache_stats['hit_rate']
            if hit_rate < PerformanceThresholds.CACHE_HIT_RATE_WARNING:
                score -= (PerformanceThresholds.CACHE_HIT_RATE_WARNING - hit_rate) * 50
        
        # Deduct for high error rates
        error_rate = self.app_monitor.get_error_rate()
        if error_rate > PerformanceThresholds.ERROR_RATE_WARNING:
            score -= min(25, (error_rate - PerformanceThresholds.ERROR_RATE_WARNING) * 2)
        
        return max(0.0, min(100.0, score))


# Global monitoring instances
system_monitor = SystemMonitor()
app_monitor = ApplicationMonitor()
performance_logger = PerformanceLogger()
monitoring_dashboard = MonitoringDashboard(system_monitor, app_monitor)


def setup_monitoring():
    """Set up monitoring components."""
    # Start background monitoring
    import threading
    
    def monitoring_loop():
        while True:
            try:
                # Get system metrics
                metrics = system_monitor.get_system_metrics()
                
                # Check thresholds
                alerts = system_monitor.check_thresholds(metrics)
                alerts.extend(app_monitor.check_error_thresholds())
                
                # Process alerts
                for alert in alerts:
                    system_monitor.add_alert(alert)
                    performance_logger.log_alert(alert)
                
                # Log system metrics periodically
                performance_logger.log_system_metrics(metrics)
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    # Start monitoring thread
    monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitoring_thread.start()
    
    logging.info("Monitoring system started")


def get_monitoring_report() -> Dict[str, Any]:
    """Get comprehensive monitoring report."""
    return monitoring_dashboard.get_dashboard_data()