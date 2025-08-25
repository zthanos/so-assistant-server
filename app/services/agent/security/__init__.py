"""
Security module for the agent system.
Provides data isolation, PII protection, and security configuration management.
"""

from .data_isolation import (
    DataIsolationError,
    ProjectAccessValidator,
    SessionIsolationManager,
    VectorStoreAccessControl,
    require_project_access,
    require_session_isolation
)

from .pii_protection import (
    PIIType,
    PIIPattern,
    PIIDetector,
    PIIRedactor,
    SecureContentHandler,
    PIIRedactionFilter,
    setup_pii_protection_logging
)

from .config import (
    SecurityLevel,
    EncryptionMethod,
    CredentialConfig,
    AccessControlConfig,
    SecurityConfig,
    CredentialManager,
    SecurityConfigLoader,
    get_security_config,
    get_credential_manager,
    get_credential,
    initialize_security
)

__all__ = [
    # Data isolation
    "DataIsolationError",
    "ProjectAccessValidator", 
    "SessionIsolationManager",
    "VectorStoreAccessControl",
    "require_project_access",
    "require_session_isolation",
    
    # PII protection
    "PIIType",
    "PIIPattern",
    "PIIDetector",
    "PIIRedactor",
    "SecureContentHandler",
    "PIIRedactionFilter",
    "setup_pii_protection_logging",
    
    # Security configuration
    "SecurityLevel",
    "EncryptionMethod",
    "CredentialConfig",
    "AccessControlConfig",
    "SecurityConfig",
    "CredentialManager",
    "SecurityConfigLoader",
    "get_security_config",
    "get_credential_manager",
    "get_credential",
    "initialize_security"
]