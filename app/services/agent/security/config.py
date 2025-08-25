"""
Security configuration management for the agent system.
Handles secure storage of credentials, access controls, and environment-based security settings.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class EncryptionMethod(Enum):
    """Supported encryption methods for credential storage."""
    NONE = "none"
    AES_256 = "aes_256"
    ENVIRONMENT = "environment"
    VAULT = "vault"


@dataclass
class CredentialConfig:
    """Configuration for a single credential."""
    name: str
    encryption_method: EncryptionMethod
    storage_location: str
    required: bool = True
    description: str = ""
    environment_variable: Optional[str] = None


@dataclass
class AccessControlConfig:
    """Access control configuration."""
    enable_project_isolation: bool = True
    enable_session_validation: bool = True
    enable_user_permissions: bool = True
    session_timeout_minutes: int = 60
    max_concurrent_sessions: int = 10
    allowed_operations: List[str] = field(default_factory=lambda: ["read", "write"])
    admin_operations: List[str] = field(default_factory=lambda: ["admin", "delete"])


@dataclass
class SecurityConfig:
    """Main security configuration."""
    security_level: SecurityLevel
    credentials: Dict[str, CredentialConfig]
    access_control: AccessControlConfig
    pii_protection_enabled: bool = True
    audit_logging_enabled: bool = True
    encryption_key_rotation_days: int = 90
    secure_headers_enabled: bool = True
    rate_limiting_enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self):
        """Validate security configuration."""
        if self.security_level == SecurityLevel.PRODUCTION:
            # Production-specific validations
            for name, cred in self.credentials.items():
                if cred.required and cred.encryption_method == EncryptionMethod.NONE:
                    raise ValueError(
                        f"Credential '{name}' cannot use no encryption in production"
                    )
        
        if self.access_control.session_timeout_minutes < 5:
            raise ValueError("Session timeout must be at least 5 minutes")


class CredentialManager:
    """Manages secure storage and retrieval of credentials."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CredentialManager")
        self._credential_cache: Dict[str, str] = {}
    
    def get_credential(self, name: str) -> Optional[str]:
        """
        Retrieve a credential by name.
        
        Args:
            name: Credential name
            
        Returns:
            Credential value or None if not found
            
        Raises:
            ValueError: If credential is required but not found
        """
        if name in self._credential_cache:
            return self._credential_cache[name]
        
        if name not in self.config.credentials:
            self.logger.error(f"Unknown credential requested: {name}")
            return None
        
        cred_config = self.config.credentials[name]
        value = self._retrieve_credential(cred_config)
        
        if value is None and cred_config.required:
            raise ValueError(f"Required credential '{name}' not found")
        
        if value:
            self._credential_cache[name] = value
        
        return value
    
    def _retrieve_credential(self, config: CredentialConfig) -> Optional[str]:
        """Retrieve credential based on its configuration."""
        try:
            if config.encryption_method == EncryptionMethod.ENVIRONMENT:
                return self._get_from_environment(config)
            elif config.encryption_method == EncryptionMethod.AES_256:
                return self._get_from_encrypted_storage(config)
            elif config.encryption_method == EncryptionMethod.VAULT:
                return self._get_from_vault(config)
            elif config.encryption_method == EncryptionMethod.NONE:
                return self._get_from_plain_storage(config)
            else:
                self.logger.error(f"Unsupported encryption method: {config.encryption_method}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve credential '{config.name}': {e}")
            return None
    
    def _get_from_environment(self, config: CredentialConfig) -> Optional[str]:
        """Get credential from environment variable."""
        env_var = config.environment_variable or config.name.upper()
        value = os.getenv(env_var)
        
        if value:
            self.logger.info(f"Retrieved credential '{config.name}' from environment")
        else:
            self.logger.warning(f"Environment variable '{env_var}' not found")
        
        return value
    
    def _get_from_encrypted_storage(self, config: CredentialConfig) -> Optional[str]:
        """Get credential from encrypted storage."""
        # TODO: Implement AES-256 decryption
        self.logger.warning(f"AES-256 decryption not implemented for '{config.name}'")
        return None
    
    def _get_from_vault(self, config: CredentialConfig) -> Optional[str]:
        """Get credential from external vault (e.g., HashiCorp Vault)."""
        # TODO: Implement vault integration
        self.logger.warning(f"Vault integration not implemented for '{config.name}'")
        return None
    
    def _get_from_plain_storage(self, config: CredentialConfig) -> Optional[str]:
        """Get credential from plain text storage (development only)."""
        if self.config.security_level == SecurityLevel.PRODUCTION:
            self.logger.error(f"Plain text storage not allowed in production for '{config.name}'")
            return None
        
        try:
            with open(config.storage_location, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            self.logger.warning(f"Credential file not found: {config.storage_location}")
            return None
    
    def clear_cache(self):
        """Clear credential cache."""
        self._credential_cache.clear()
        self.logger.info("Credential cache cleared")


class SecurityConfigLoader:
    """Loads security configuration from various sources."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SecurityConfigLoader")
    
    def load_config(
        self, 
        config_path: Optional[str] = None,
        environment: Optional[str] = None
    ) -> SecurityConfig:
        """
        Load security configuration.
        
        Args:
            config_path: Path to configuration file
            environment: Environment name (overrides detection)
            
        Returns:
            SecurityConfig instance
        """
        # Determine security level
        security_level = self._determine_security_level(environment)
        
        # Load base configuration
        base_config = self._load_base_config(config_path, security_level)
        
        # Load environment-specific overrides
        env_config = self._load_environment_config(security_level)
        
        # Merge configurations
        merged_config = self._merge_configs(base_config, env_config)
        
        return SecurityConfig(**merged_config)
    
    def _determine_security_level(self, environment: Optional[str]) -> SecurityLevel:
        """Determine security level from environment."""
        if environment:
            try:
                return SecurityLevel(environment.lower())
            except ValueError:
                self.logger.warning(f"Unknown environment '{environment}', defaulting to development")
        
        # Auto-detect from environment variables
        env = os.getenv("ENVIRONMENT", "development").lower()
        
        try:
            return SecurityLevel(env)
        except ValueError:
            self.logger.warning(f"Unknown environment '{env}', defaulting to development")
            return SecurityLevel.DEVELOPMENT
    
    def _load_base_config(
        self, 
        config_path: Optional[str], 
        security_level: SecurityLevel
    ) -> Dict[str, Any]:
        """Load base security configuration."""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded security config from {config_path}")
                return config
            except Exception as e:
                self.logger.error(f"Failed to load config from {config_path}: {e}")
        
        # Return default configuration
        return self._get_default_config(security_level)
    
    def _load_environment_config(self, security_level: SecurityLevel) -> Dict[str, Any]:
        """Load environment-specific configuration overrides."""
        env_config = {}
        
        # Load from environment variables with SECURITY_ prefix
        for key, value in os.environ.items():
            if key.startswith("SECURITY_"):
                config_key = key[9:].lower()  # Remove SECURITY_ prefix
                
                # Try to parse as JSON, fallback to string
                try:
                    env_config[config_key] = json.loads(value)
                except json.JSONDecodeError:
                    env_config[config_key] = value
        
        return env_config
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge base and override configurations."""
        merged = base.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _get_default_config(self, security_level: SecurityLevel) -> Dict[str, Any]:
        """Get default security configuration for the given security level."""
        # Default credentials configuration
        credentials = {
            "ollama_api_key": CredentialConfig(
                name="ollama_api_key",
                encryption_method=EncryptionMethod.ENVIRONMENT,
                storage_location="",
                required=False,
                description="Ollama API key (if required)",
                environment_variable="OLLAMA_API_KEY"
            ),
            "database_url": CredentialConfig(
                name="database_url",
                encryption_method=EncryptionMethod.ENVIRONMENT,
                storage_location="",
                required=True,
                description="Database connection URL",
                environment_variable="DATABASE_URL"
            ),
            "vector_store_api_key": CredentialConfig(
                name="vector_store_api_key",
                encryption_method=EncryptionMethod.ENVIRONMENT,
                storage_location="",
                required=False,
                description="Vector store API key",
                environment_variable="VECTOR_STORE_API_KEY"
            ),
            "jwt_secret": CredentialConfig(
                name="jwt_secret",
                encryption_method=EncryptionMethod.ENVIRONMENT,
                storage_location="",
                required=True,
                description="JWT signing secret",
                environment_variable="JWT_SECRET"
            )
        }
        
        # Adjust encryption methods based on security level
        if security_level == SecurityLevel.PRODUCTION:
            for cred in credentials.values():
                if cred.encryption_method == EncryptionMethod.NONE:
                    cred.encryption_method = EncryptionMethod.ENVIRONMENT
        
        # Access control configuration
        access_control = AccessControlConfig(
            enable_project_isolation=True,
            enable_session_validation=security_level != SecurityLevel.DEVELOPMENT,
            enable_user_permissions=security_level in [SecurityLevel.STAGING, SecurityLevel.PRODUCTION],
            session_timeout_minutes=60 if security_level == SecurityLevel.PRODUCTION else 120,
            max_concurrent_sessions=5 if security_level == SecurityLevel.PRODUCTION else 10
        )
        
        return {
            "security_level": security_level,
            "credentials": {name: cred.__dict__ for name, cred in credentials.items()},
            "access_control": access_control.__dict__,
            "pii_protection_enabled": security_level != SecurityLevel.DEVELOPMENT,
            "audit_logging_enabled": security_level in [SecurityLevel.STAGING, SecurityLevel.PRODUCTION],
            "encryption_key_rotation_days": 30 if security_level == SecurityLevel.PRODUCTION else 90,
            "secure_headers_enabled": security_level != SecurityLevel.DEVELOPMENT,
            "rate_limiting_enabled": security_level in [SecurityLevel.STAGING, SecurityLevel.PRODUCTION]
        }


# Global security configuration instance
_security_config: Optional[SecurityConfig] = None
_credential_manager: Optional[CredentialManager] = None


def get_security_config() -> SecurityConfig:
    """Get the global security configuration instance."""
    global _security_config
    
    if _security_config is None:
        loader = SecurityConfigLoader()
        _security_config = loader.load_config()
    
    return _security_config


def get_credential_manager() -> CredentialManager:
    """Get the global credential manager instance."""
    global _credential_manager
    
    if _credential_manager is None:
        config = get_security_config()
        _credential_manager = CredentialManager(config)
    
    return _credential_manager


def get_credential(name: str) -> Optional[str]:
    """Convenience function to get a credential."""
    manager = get_credential_manager()
    return manager.get_credential(name)


def initialize_security(config_path: Optional[str] = None, environment: Optional[str] = None):
    """Initialize security configuration."""
    global _security_config, _credential_manager
    
    loader = SecurityConfigLoader()
    _security_config = loader.load_config(config_path, environment)
    _credential_manager = CredentialManager(_security_config)
    
    logger.info(f"Security initialized for {_security_config.security_level.value} environment")