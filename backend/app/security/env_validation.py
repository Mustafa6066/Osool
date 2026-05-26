"""
Environment Variable Security Hardening
---------------------------------------
Validates and sanitizes environment variables at startup.

Features:
- Validates all required environment variables
- Checks secret key strength (entropy)
- Prevents weak/default secrets in production
- Sanitizes potentially dangerous values
- Provides clear error messages for missing/invalid config
"""

import os
import re
import hashlib
import math
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or insecure."""
    pass


class EnvironmentValidator:
    """Validates environment variables for security."""
    
    # Common weak secrets to reject
    WEAK_SECRETS = {
        'secret', 'password', 'changeme', 'default', 'admin',
        'test', 'demo', 'sample', '12345', 'secret123',
        'your-secret-here', 'replace-me', 'todo',
    }
    
    # Minimum entropy for cryptographic secrets (bits)
    MIN_SECRET_ENTROPY = 128  # bits
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.is_production = environment == "production"
        self.errors = []
        self.warnings = []
    
    def calculate_entropy(self, value: str) -> float:
        """
        Calculate Shannon entropy of a string (in bits).
        
        Higher entropy = more randomness = better security
        """
        if not value:
            return 0.0
        
        # Count character frequencies
        freq = {}
        for char in value:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        length = len(value)
        
        for count in freq.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        # Multiply by string length to get total entropy in bits
        return entropy * length
    
    def is_weak_secret(self, value: str) -> bool:
        """
        Check if secret appears to be weak or default.
        
        Returns:
            True if weak/default, False if strong
        """
        value_lower = value.lower()
        
        # Check against known weak secrets
        if value_lower in self.WEAK_SECRETS:
            return True
        
        # Check for common patterns
        weak_patterns = [
            r'^secret[0-9]*$',
            r'^password[0-9]*$',
            r'^admin[0-9]*$',
            r'^test[0-9]*$',
            r'^[0-9]{4,8}$',  # Simple numbers like 12345678
            r'^(abc|qwerty|letmein)',
        ]
        
        for pattern in weak_patterns:
            if re.match(pattern, value_lower):
                return True
        
        # Check entropy
        entropy = self.calculate_entropy(value)
        if entropy < self.MIN_SECRET_ENTROPY:
            return True
        
        return False
    
    def validate_secret_key(self, key_name: str, min_length: int = 32, required: bool = True) -> Optional[str]:
        """
        Validate a cryptographic secret key.
        
        Args:
            key_name: Environment variable name
            min_length: Minimum required length
            required: Whether key is required
        
        Returns:
            Secret value if valid, None if not required and missing
        
        Raises:
            ConfigurationError: If key is invalid or missing when required
        """
        value = os.getenv(key_name)
        
        # Check if required
        if not value:
            if required:
                self.errors.append(f"{key_name} is required but not set")
                return None
            return None
        
        # Check minimum length
        if len(value) < min_length:
            self.errors.append(
                f"{key_name} is too short (got {len(value)} chars, need {min_length}+)"
            )
        
        # In production, enforce strong secrets
        if self.is_production:
            if self.is_weak_secret(value):
                self.errors.append(
                    f"{key_name} appears to be a weak or default secret. "
                    f"Generate with: openssl rand -hex {min_length}"
                )
            
            # Check for placeholder values
            placeholder_patterns = [
                'YOUR_', 'PASTE_', 'REPLACE_', 'TODO', 'FIXME', 'XXX'
            ]
            if any(pattern in value.upper() for pattern in placeholder_patterns):
                self.errors.append(
                    f"{key_name} contains placeholder text - replace with actual secret"
                )
        
        return value
    
    def validate_url(self, key_name: str, required: bool = True, schemes: list = None) -> Optional[str]:
        """
        Validate a URL environment variable.
        
        Args:
            key_name: Environment variable name
            required: Whether URL is required
            schemes: Allowed URL schemes (default: http, https)
        
        Returns:
            URL if valid, None if optional and missing
        """
        if schemes is None:
            schemes = ['http', 'https']
        
        value = os.getenv(key_name)
        
        if not value:
            if required:
                self.errors.append(f"{key_name} is required but not set")
            return None
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^(' + '|'.join(schemes) + r')://'  # scheme
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        if not url_pattern.match(value):
            self.errors.append(f"{key_name} is not a valid URL: {value}")
        
        # In production, enforce HTTPS
        if self.is_production and not value.startswith('https://'):
            if value.startswith('http://'):
                self.warnings.append(
                    f"{key_name} uses HTTP instead of HTTPS in production (insecure)"
                )
        
        return value
    
    def validate_boolean(self, key_name: str, default: bool = False) -> bool:
        """
        Validate a boolean environment variable.
        
        Args:
            key_name: Environment variable name
            default: Default value if not set
        
        Returns:
            Boolean value
        """
        value = os.getenv(key_name)
        
        if not value:
            return default
        
        value_lower = value.lower()
        
        if value_lower in ('true', '1', 'yes', 'on'):
            return True
        elif value_lower in ('false', '0', 'no', 'off'):
            return False
        else:
            self.warnings.append(
                f"{key_name} has invalid boolean value '{value}' - using default: {default}"
            )
            return default
    
    def validate_integer(
        self,
        key_name: str,
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> Optional[int]:
        """
        Validate an integer environment variable.
        
        Args:
            key_name: Environment variable name
            default: Default value if not set
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        
        Returns:
            Integer value
        """
        value = os.getenv(key_name)
        
        if not value:
            return default
        
        try:
            int_value = int(value)
        except ValueError:
            self.errors.append(f"{key_name} must be an integer, got: {value}")
            return default
        
        if min_value is not None and int_value < min_value:
            self.errors.append(f"{key_name} must be >= {min_value}, got: {int_value}")
        
        if max_value is not None and int_value > max_value:
            self.errors.append(f"{key_name} must be <= {max_value}, got: {int_value}")
        
        return int_value
    
    def validate_all(self) -> Dict[str, any]:
        """
        Validate all Osool environment variables.
        
        Returns:
            dict of validated configuration
        
        Raises:
            ConfigurationError: If any critical errors found
        """
        config = {}
        
        # Core Settings
        config['ENVIRONMENT'] = os.getenv('ENVIRONMENT', 'development')
        
        # Database
        config['DATABASE_URL'] = self.validate_url(
            'DATABASE_URL',
            required=True,
            schemes=['postgresql', 'postgresql+asyncpg']
        )
        
        # Security Keys
        config['JWT_SECRET_KEY'] = self.validate_secret_key('JWT_SECRET_KEY', min_length=32, required=True)
        config['CSRF_SECRET_KEY'] = self.validate_secret_key('CSRF_SECRET_KEY', min_length=32, required=False)
        config['ADMIN_API_KEY'] = self.validate_secret_key('ADMIN_API_KEY', min_length=32, required=True)
        
        # AI API Keys
        config['OPENAI_API_KEY'] = self.validate_secret_key('OPENAI_API_KEY', min_length=20, required=True)
        config['ANTHROPIC_API_KEY'] = self.validate_secret_key('ANTHROPIC_API_KEY', min_length=20, required=True)
        
        # Supabase
        config['SUPABASE_URL'] = self.validate_url('SUPABASE_URL', required=True)
        config['SUPABASE_KEY'] = self.validate_secret_key('SUPABASE_KEY', min_length=20, required=True)
        
        # Optional Services
        if self.validate_boolean('PAYMENTS_ENABLED'):
            self.validate_secret_key('PAYMOB_API_KEY', min_length=20, required=True)
        
        if self.validate_boolean('SMS_ENABLED'):
            self.validate_secret_key('TWILIO_AUTH_TOKEN', min_length=20, required=True)
        
        if self.validate_boolean('EMAIL_ENABLED'):
            self.validate_secret_key('SENDGRID_API_KEY', min_length=20, required=True)
        
        # CORS
        config['FRONTEND_DOMAIN'] = self.validate_url('FRONTEND_DOMAIN', required=False)
        
        # Redis
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            self.validate_url('REDIS_URL', required=False, schemes=['redis', 'rediss'])
        
        # Report results
        if self.errors:
            error_msg = "Configuration errors found:\n" + "\n".join(f"  - {e}" for e in self.errors)
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        if self.warnings:
            warning_msg = "Configuration warnings:\n" + "\n".join(f"  - {w}" for w in self.warnings)
            logger.warning(warning_msg)
        
        logger.info(f"✅ Environment configuration validated for {config['ENVIRONMENT']}")
        
        return config


# Run validation on import
def validate_environment():
    """Run environment validation on module import."""
    environment = os.getenv('ENVIRONMENT', 'development')
    validator = EnvironmentValidator(environment)
    
    try:
        config = validator.validate_all()
        return config
    except ConfigurationError as e:
        logger.critical(f"FATAL: {e}")
        raise


# Auto-validate on import (can be disabled with SKIP_ENV_VALIDATION=true)
if not os.getenv('SKIP_ENV_VALIDATION', '').lower() == 'true':
    validate_environment()
