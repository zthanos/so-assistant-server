"""
PII (Personally Identifiable Information) protection mechanisms.
Handles automatic PII redaction in logs and secure content handling.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PIIType(Enum):
    """Types of PII that can be detected and redacted."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    CUSTOM = "custom"


@dataclass
class PIIPattern:
    """Pattern definition for PII detection."""
    pii_type: PIIType
    pattern: str
    replacement: str
    confidence: float = 1.0
    description: str = ""


class PIIDetector:
    """Detects various types of PII in text content."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PIIDetector")
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> List[PIIPattern]:
        """Initialize PII detection patterns."""
        return [
            PIIPattern(
                pii_type=PIIType.EMAIL,
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                replacement="[EMAIL_REDACTED]",
                confidence=0.95,
                description="Email address pattern"
            ),
            PIIPattern(
                pii_type=PIIType.PHONE,
                pattern=r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
                replacement="[PHONE_REDACTED]",
                confidence=0.85,
                description="US phone number pattern"
            ),
            PIIPattern(
                pii_type=PIIType.SSN,
                pattern=r'\b\d{3}-?\d{2}-?\d{4}\b',
                replacement="[SSN_REDACTED]",
                confidence=0.90,
                description="US Social Security Number"
            ),
            PIIPattern(
                pii_type=PIIType.CREDIT_CARD,
                pattern=r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                replacement="[CREDIT_CARD_REDACTED]",
                confidence=0.80,
                description="Credit card number pattern"
            ),
            PIIPattern(
                pii_type=PIIType.IP_ADDRESS,
                pattern=r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                replacement="[IP_REDACTED]",
                confidence=0.75,
                description="IPv4 address pattern"
            ),
            # Greek-specific patterns
            PIIPattern(
                pii_type=PIIType.CUSTOM,
                pattern=r'\b\d{11}\b',  # Greek tax number (AFM)
                replacement="[TAX_ID_REDACTED]",
                confidence=0.70,
                description="Greek tax identification number"
            ),
        ]
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect PII in text and return detection results.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of PII detections with metadata
        """
        detections = []
        
        for pattern in self.patterns:
            matches = re.finditer(pattern.pattern, text, re.IGNORECASE)
            
            for match in matches:
                detection = {
                    "type": pattern.pii_type.value,
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": pattern.confidence,
                    "replacement": pattern.replacement,
                    "description": pattern.description
                }
                detections.append(detection)
        
        return detections
    
    def add_custom_pattern(self, pattern: PIIPattern) -> None:
        """Add a custom PII detection pattern."""
        self.patterns.append(pattern)
        self.logger.info(f"Added custom PII pattern: {pattern.description}")


class PIIRedactor:
    """Redacts PII from text content."""
    
    def __init__(self, detector: Optional[PIIDetector] = None):
        self.logger = logging.getLogger(f"{__name__}.PIIRedactor")
        self.detector = detector or PIIDetector()
        self.redaction_audit_log: List[Dict[str, Any]] = []
    
    def redact_text(
        self, 
        text: str, 
        preserve_format: bool = True,
        audit: bool = True
    ) -> str:
        """
        Redact PII from text content.
        
        Args:
            text: Text to redact
            preserve_format: Whether to preserve original text formatting
            audit: Whether to log redaction actions
            
        Returns:
            Text with PII redacted
        """
        if not text:
            return text
        
        detections = self.detector.detect_pii(text)
        redacted_text = text
        
        # Sort detections by position (reverse order to maintain indices)
        detections.sort(key=lambda x: x["start"], reverse=True)
        
        redaction_count = 0
        for detection in detections:
            start = detection["start"]
            end = detection["end"]
            replacement = detection["replacement"]
            
            # Preserve format by maintaining similar length if requested
            if preserve_format:
                original_length = end - start
                replacement_length = len(replacement)
                if replacement_length < original_length:
                    padding = "*" * (original_length - replacement_length)
                    replacement = replacement + padding
            
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
            redaction_count += 1
            
            # Audit logging
            if audit:
                self._log_redaction(detection, text[start:end])
        
        if redaction_count > 0:
            self.logger.info(f"Redacted {redaction_count} PII instances from text")
        
        return redacted_text
    
    def redact_dict(
        self, 
        data: Dict[str, Any], 
        exclude_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Redact PII from dictionary values.
        
        Args:
            data: Dictionary to redact
            exclude_keys: Keys to skip during redaction
            
        Returns:
            Dictionary with PII redacted from string values
        """
        exclude_keys = exclude_keys or []
        redacted_data = {}
        
        for key, value in data.items():
            if key in exclude_keys:
                redacted_data[key] = value
            elif isinstance(value, str):
                redacted_data[key] = self.redact_text(value)
            elif isinstance(value, dict):
                redacted_data[key] = self.redact_dict(value, exclude_keys)
            elif isinstance(value, list):
                redacted_data[key] = [
                    self.redact_text(item) if isinstance(item, str) 
                    else self.redact_dict(item, exclude_keys) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                redacted_data[key] = value
        
        return redacted_data
    
    def _log_redaction(self, detection: Dict[str, Any], original_text: str) -> None:
        """Log redaction action for audit purposes."""
        audit_entry = {
            "timestamp": None,  # TODO: Add timestamp
            "pii_type": detection["type"],
            "confidence": detection["confidence"],
            "original_length": len(original_text),
            "redacted_to": detection["replacement"],
            "context_hash": hash(original_text[:10] + original_text[-10:])  # Partial context
        }
        
        self.redaction_audit_log.append(audit_entry)
        
        # Log without the actual PII content
        self.logger.info(
            f"PII redaction: {detection['type']} "
            f"(confidence: {detection['confidence']}) -> {detection['replacement']}"
        )
    
    def get_redaction_stats(self) -> Dict[str, Any]:
        """Get statistics about redaction operations."""
        if not self.redaction_audit_log:
            return {"total_redactions": 0, "by_type": {}}
        
        stats = {
            "total_redactions": len(self.redaction_audit_log),
            "by_type": {},
            "average_confidence": 0.0
        }
        
        type_counts = {}
        total_confidence = 0.0
        
        for entry in self.redaction_audit_log:
            pii_type = entry["pii_type"]
            type_counts[pii_type] = type_counts.get(pii_type, 0) + 1
            total_confidence += entry["confidence"]
        
        stats["by_type"] = type_counts
        stats["average_confidence"] = total_confidence / len(self.redaction_audit_log)
        
        return stats


class SecureContentHandler:
    """Handles secure processing of sensitive content in responses."""
    
    def __init__(self, redactor: Optional[PIIRedactor] = None):
        self.logger = logging.getLogger(f"{__name__}.SecureContentHandler")
        self.redactor = redactor or PIIRedactor()
    
    def sanitize_response(
        self, 
        response: Dict[str, Any],
        sensitive_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sanitize response content for safe transmission.
        
        Args:
            response: Response dictionary to sanitize
            sensitive_fields: Fields that require extra sanitization
            
        Returns:
            Sanitized response dictionary
        """
        sensitive_fields = sensitive_fields or [
            "content", "text", "message", "description", "details"
        ]
        
        sanitized = {}
        
        for key, value in response.items():
            if key in sensitive_fields and isinstance(value, str):
                # Apply PII redaction to sensitive fields
                sanitized[key] = self.redactor.redact_text(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_response(value, sensitive_fields)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_response(item, sensitive_fields) 
                    if isinstance(item, dict)
                    else self.redactor.redact_text(item) 
                    if isinstance(item, str) and key in sensitive_fields
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def create_audit_trail(
        self, 
        operation: str, 
        user_id: str, 
        project_id: str,
        data_accessed: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create audit trail entry for data access and processing.
        
        Args:
            operation: Type of operation performed
            user_id: User who performed the operation
            project_id: Project context
            data_accessed: List of data types/sources accessed
            metadata: Additional metadata
            
        Returns:
            Audit trail entry
        """
        audit_entry = {
            "timestamp": None,  # TODO: Add timestamp
            "operation": operation,
            "user_id": user_id,
            "project_id": project_id,
            "data_accessed": data_accessed,
            "metadata": metadata or {},
            "pii_redactions": self.redactor.get_redaction_stats()
        }
        
        self.logger.info(
            f"Audit trail: {operation} by user {user_id} "
            f"on project {project_id}, accessed: {', '.join(data_accessed)}"
        )
        
        return audit_entry


# Logging filter to automatically redact PII from log messages
class PIIRedactionFilter(logging.Filter):
    """Logging filter that automatically redacts PII from log messages."""
    
    def __init__(self, redactor: Optional[PIIRedactor] = None):
        super().__init__()
        self.redactor = redactor or PIIRedactor()
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log record to redact PII from message."""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self.redactor.redact_text(record.msg, audit=False)
        
        # Also redact from args if present
        if hasattr(record, 'args') and record.args:
            redacted_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    redacted_args.append(self.redactor.redact_text(arg, audit=False))
                else:
                    redacted_args.append(arg)
            record.args = tuple(redacted_args)
        
        return True


def setup_pii_protection_logging():
    """Set up PII protection for application logging."""
    pii_filter = PIIRedactionFilter()
    
    # Add filter to root logger
    root_logger = logging.getLogger()
    root_logger.addFilter(pii_filter)
    
    # Add filter to specific loggers that might handle sensitive data
    sensitive_loggers = [
        "app.services.agent",
        "app.api.v1.endpoints",
        "app.services.llm"
    ]
    
    for logger_name in sensitive_loggers:
        logger = logging.getLogger(logger_name)
        logger.addFilter(pii_filter)
    
    logging.getLogger(__name__).info("PII protection logging filters installed")