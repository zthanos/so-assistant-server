"""Enhanced logging and tracing for agent operations."""
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional
from functools import wraps
from contextvars import ContextVar
import re

# Context variables for request tracking
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
project_id_context: ContextVar[Optional[str]] = ContextVar('project_id', default=None)
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class PIIRedactor:
    """PII redaction utility."""
    
    # PII patterns
    PII_PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
        'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
        'api_key': re.compile(r'\b[A-Za-z0-9]{32,}\b'),  # Generic API key pattern
    }
    
    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redact PII from text."""
        if not isinstance(text, str):
            return str(text)
        
        redacted = text
        
        for pii_type, pattern in cls.PII_PATTERNS.items():
            redacted = pattern.sub(f'[REDACTED_{pii_type.upper()}]', redacted)
        
        return redacted
    
    @classmethod
    def redact_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact PII from dictionary."""
        if not isinstance(data, dict):
            return data
        
        redacted = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                redacted[key] = cls.redact_text(value)
            elif isinstance(value, dict):
                redacted[key] = cls.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [
                    cls.redact_text(item) if isinstance(item, str)
                    else cls.redact_dict(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                redacted[key] = value
        
        return redacted


class StructuredLogger:
    """Structured logger with context and PII redaction."""
    
    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self.pii_redactor = PIIRedactor()
    
    def _get_context(self) -> Dict[str, Any]:
        """Get current context."""
        return {
            'request_id': request_id_context.get(),
            'project_id': project_id_context.get(),
            'user_id': user_id_context.get(),
            'timestamp': time.time()
        }
    
    def _format_message(self, message: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format log message with context."""
        log_data = {
            'message': self.pii_redactor.redact_text(message),
            'context': self._get_context()
        }
        
        if extra:
            log_data['extra'] = self.pii_redactor.redact_dict(extra)
        
        return log_data
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        log_data = self._format_message(message, extra)
        self.logger.info(json.dumps(log_data, default=str))
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        log_data = self._format_message(message, extra)
        self.logger.warning(json.dumps(log_data, default=str))
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message."""
        log_data = self._format_message(message, extra)
        if exc_info:
            log_data['exc_info'] = True
        self.logger.error(json.dumps(log_data, default=str), exc_info=exc_info)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        log_data = self._format_message(message, extra)
        self.logger.debug(json.dumps(log_data, default=str))


class RequestTracer:
    """Request tracing utility."""
    
    def __init__(self):
        """Initialize request tracer."""
        self.active_traces: Dict[str, Dict[str, Any]] = {}
    
    def start_trace(self, request_id: Optional[str] = None, **context) -> str:
        """Start a new trace."""
        if not request_id:
            request_id = str(uuid.uuid4())
        
        trace_data = {
            'request_id': request_id,
            'start_time': time.time(),
            'context': context,
            'spans': [],
            'status': 'active'
        }
        
        self.active_traces[request_id] = trace_data
        
        # Set context variables
        request_id_context.set(request_id)
        if 'project_id' in context:
            project_id_context.set(context['project_id'])
        if 'user_id' in context:
            user_id_context.set(context['user_id'])
        
        return request_id
    
    def add_span(self, request_id: str, span_name: str, **span_data) -> str:
        """Add a span to the trace."""
        if request_id not in self.active_traces:
            return ""
        
        span_id = str(uuid.uuid4())
        span = {
            'span_id': span_id,
            'span_name': span_name,
            'start_time': time.time(),
            'data': span_data,
            'status': 'active'
        }
        
        self.active_traces[request_id]['spans'].append(span)
        return span_id
    
    def end_span(self, request_id: str, span_id: str, **end_data):
        """End a span."""
        if request_id not in self.active_traces:
            return
        
        trace = self.active_traces[request_id]
        for span in trace['spans']:
            if span['span_id'] == span_id:
                span['end_time'] = time.time()
                span['duration'] = span['end_time'] - span['start_time']
                span['status'] = 'completed'
                span['end_data'] = end_data
                break
    
    def end_trace(self, request_id: str, **end_data) -> Optional[Dict[str, Any]]:
        """End a trace and return trace data."""
        if request_id not in self.active_traces:
            return None
        
        trace = self.active_traces[request_id]
        trace['end_time'] = time.time()
        trace['duration'] = trace['end_time'] - trace['start_time']
        trace['status'] = 'completed'
        trace['end_data'] = end_data
        
        # Remove from active traces
        completed_trace = self.active_traces.pop(request_id)
        
        return completed_trace
    
    def get_trace(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get trace data."""
        return self.active_traces.get(request_id)
    
    def get_active_traces(self) -> Dict[str, Dict[str, Any]]:
        """Get all active traces."""
        return self.active_traces.copy()


def with_tracing(span_name: str, include_args: bool = False, include_result: bool = False):
    """Decorator for adding tracing to functions."""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            request_id = request_id_context.get()
            if not request_id:
                # No active trace, execute normally
                return await func(*args, **kwargs)
            
            # Start span
            span_data = {}
            if include_args:
                span_data['args'] = str(args)[:200]  # Limit size
                span_data['kwargs'] = {k: str(v)[:200] for k, v in kwargs.items()}
            
            span_id = tracer.add_span(request_id, span_name, **span_data)
            
            try:
                result = await func(*args, **kwargs)
                
                # End span with result
                end_data = {}
                if include_result:
                    end_data['result'] = str(result)[:200]  # Limit size
                
                tracer.end_span(request_id, span_id, success=True, **end_data)
                
                return result
            
            except Exception as e:
                tracer.end_span(request_id, span_id, success=False, error=str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            request_id = request_id_context.get()
            if not request_id:
                return func(*args, **kwargs)
            
            span_data = {}
            if include_args:
                span_data['args'] = str(args)[:200]
                span_data['kwargs'] = {k: str(v)[:200] for k, v in kwargs.items()}
            
            span_id = tracer.add_span(request_id, span_name, **span_data)
            
            try:
                result = func(*args, **kwargs)
                
                end_data = {}
                if include_result:
                    end_data['result'] = str(result)[:200]
                
                tracer.end_span(request_id, span_id, success=True, **end_data)
                
                return result
            
            except Exception as e:
                tracer.end_span(request_id, span_id, success=False, error=str(e))
                raise
        
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class MetricsCollector:
    """Metrics collection for agent operations."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: Dict[str, Dict[str, Any]] = {
            'counters': {},
            'gauges': {},
            'histograms': {},
            'timers': {}
        }
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        key = self._get_metric_key(name, tags)
        if key not in self.metrics['counters']:
            self.metrics['counters'][key] = 0
        self.metrics['counters'][key] += value
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        key = self._get_metric_key(name, tags)
        self.metrics['gauges'][key] = value
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram value."""
        key = self._get_metric_key(name, tags)
        if key not in self.metrics['histograms']:
            self.metrics['histograms'][key] = []
        self.metrics['histograms'][key].append(value)
        
        # Keep only last 1000 values
        if len(self.metrics['histograms'][key]) > 1000:
            self.metrics['histograms'][key] = self.metrics['histograms'][key][-1000:]
    
    def start_timer(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Start a timer and return timer ID."""
        timer_id = str(uuid.uuid4())
        key = self._get_metric_key(name, tags)
        
        if key not in self.metrics['timers']:
            self.metrics['timers'][key] = {}
        
        self.metrics['timers'][key][timer_id] = {
            'start_time': time.time(),
            'name': name,
            'tags': tags or {}
        }
        
        return timer_id
    
    def end_timer(self, name: str, timer_id: str, tags: Optional[Dict[str, str]] = None) -> float:
        """End a timer and record the duration."""
        key = self._get_metric_key(name, tags)
        
        if (key in self.metrics['timers'] and 
            timer_id in self.metrics['timers'][key]):
            
            timer_data = self.metrics['timers'][key][timer_id]
            duration = time.time() - timer_data['start_time']
            
            # Record as histogram
            self.record_histogram(f"{name}_duration", duration, tags)
            
            # Clean up timer
            del self.metrics['timers'][key][timer_id]
            
            return duration
        
        return 0.0
    
    def _get_metric_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Get metric key with tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        summary = {
            'counters': self.metrics['counters'].copy(),
            'gauges': self.metrics['gauges'].copy(),
            'histograms': {},
            'active_timers': sum(len(timers) for timers in self.metrics['timers'].values())
        }
        
        # Calculate histogram statistics
        for key, values in self.metrics['histograms'].items():
            if values:
                summary['histograms'][key] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'p50': self._percentile(values, 0.5),
                    'p95': self._percentile(values, 0.95),
                    'p99': self._percentile(values, 0.99)
                }
        
        return summary
    
    def _percentile(self, values: list, percentile: float) -> float:
        """Calculate percentile."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


# Global instances
tracer = RequestTracer()
metrics = MetricsCollector()


def get_logger(name: str) -> StructuredLogger:
    """Get structured logger instance."""
    return StructuredLogger(name)