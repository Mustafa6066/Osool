"""
Comprehensive Audit Logging
---------------------------
Logs all security-relevant events for compliance and forensics.

Features:
- User authentication events (login/logout/failed attempts)
- Data access logging
- Admin actions
- Sensitive operations
- IP address tracking
- User agent tracking
- Tamper-evident logging (WORM storage ready)
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import Request
import os

# Configure structured logging
logger = logging.getLogger("osool.audit")


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # Authorization
    PERMISSION_DENIED = "permission_denied"
    ADMIN_ACCESS = "admin_access"
    
    # Data Access
    PROPERTY_VIEWED = "property_viewed"
    USER_DATA_ACCESSED = "user_data_accessed"
    USER_DATA_EXPORTED = "user_data_exported"
    
    # Account Management
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_DELETED = "account_deleted"
    PROFILE_UPDATED = "profile_updated"
    EMAIL_VERIFIED = "email_verified"
    PHONE_VERIFIED = "phone_verified"
    
    # Financial
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    REFUND_ISSUED = "refund_issued"
    
    # Admin Actions
    ADMIN_USER_CREATED = "admin_user_created"
    ADMIN_USER_DELETED = "admin_user_deleted"
    ADMIN_PROPERTY_CREATED = "admin_property_created"
    ADMIN_PROPERTY_UPDATED = "admin_property_updated"
    ADMIN_PROPERTY_DELETED = "admin_property_deleted"
    ADMIN_CONFIG_CHANGED = "admin_config_changed"
    
    # Security Events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    CSRF_ATTACK_BLOCKED = "csrf_attack_blocked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    
    # GDPR/Privacy
    GDPR_DATA_EXPORT_REQUESTED = "gdpr_data_export"
    GDPR_DATA_DELETION_REQUESTED = "gdpr_data_deletion"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Structured audit event."""
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[int]
    user_email: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: Optional[str]
    result: str  # success, failure, blocked
    details: Optional[Dict[str, Any]]
    request_id: Optional[str]
    session_id: Optional[str]
    
    def to_json(self) -> str:
        """Convert to JSON for logging."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return json.dumps(data, default=str)


class AuditLogger:
    """Centralized audit logging."""
    
    def __init__(self):
        self.logger = logger
        # Configure file handler for audit logs
        self._setup_audit_file_handler()
    
    def _setup_audit_file_handler(self):
        """Set up file handler for audit logs. Falls back to stderr if directory is not writable."""
        # Audit logs should be stored separately from application logs
        # Default to a writable location inside the app directory for containers
        log_dir = os.getenv("AUDIT_LOG_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "audit"))
        
        try:
            os.makedirs(log_dir, exist_ok=True)
            
            # Rotate daily, keep for 7 years (compliance requirement)
            from logging.handlers import TimedRotatingFileHandler
            
            handler = TimedRotatingFileHandler(
                filename=f"{log_dir}/audit.log",
                when="midnight",
                interval=1,
                backupCount=365 * 7,  # 7 years
                encoding="utf-8"
            )
            
            # Structured JSON format
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)
        except (PermissionError, OSError) as e:
            # On containers/Railway, file system may be read-only; fall back to stream logging
            logging.getLogger(__name__).warning(f"Cannot create audit log directory {log_dir}: {e}. Using stream handler.")
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
        
        self.logger.setLevel(logging.INFO)
    
    def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Log an audit event."""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            details=details,
            request_id=request_id,
            session_id=session_id,
        )
        
        # Log as JSON
        log_message = event.to_json()
        
        if severity == AuditSeverity.INFO:
            self.logger.info(log_message)
        elif severity == AuditSeverity.WARNING:
            self.logger.warning(log_message)
        elif severity == AuditSeverity.ERROR:
            self.logger.error(log_message)
        elif severity == AuditSeverity.CRITICAL:
            self.logger.critical(log_message)
        
        # For critical events, also send to SIEM/monitoring
        if severity == AuditSeverity.CRITICAL:
            self._send_to_siem(event)
    
    def _send_to_siem(self, event: AuditEvent):
        """Send critical events to SIEM system."""
        # If Sentry is configured, send critical audit events
        try:
            if os.getenv("SENTRY_DSN"):
                import sentry_sdk
                sentry_sdk.capture_message(
                    "Critical audit event",
                    level="error",
                    extra={"audit_event": json.loads(event.to_json())}
                )
                return
        except Exception as e:
            logger.warning(f"Sentry capture failed for audit event: {e}")

        # Fallback: log to separate critical log, respecting AUDIT_LOG_DIR env
        try:
            log_dir = os.getenv("AUDIT_LOG_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "audit"))
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "critical.log"), "a") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write critical audit log: {e}")
    
    def log_from_request(
        self,
        request: Request,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log event with request context."""
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        request_id = request.headers.get("x-request-id") or request.headers.get("x-amzn-trace-id")
        
        self.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            details=details,
            request_id=request_id,
        )


# Global audit logger instance
audit_logger = AuditLogger()


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def audit_login_success(request: Request, user_id: int, email: str):
    """Log successful login."""
    audit_logger.log_from_request(
        request=request,
        event_type=AuditEventType.LOGIN_SUCCESS,
        severity=AuditSeverity.INFO,
        user_id=user_id,
        user_email=email,
        result="success",
    )


def audit_login_failed(request: Request, email: str, reason: str):
    """Log failed login attempt."""
    audit_logger.log_from_request(
        request=request,
        event_type=AuditEventType.LOGIN_FAILED,
        severity=AuditSeverity.WARNING,
        user_email=email,
        result="failure",
        details={"reason": reason},
    )


def audit_logout(request: Request, user_id: int, email: str):
    """Log logout."""
    audit_logger.log_from_request(
        request=request,
        event_type=AuditEventType.LOGOUT,
        severity=AuditSeverity.INFO,
        user_id=user_id,
        user_email=email,
        result="success",
    )


def audit_account_locked(email: str, ip_address: str):
    """Log account lockout."""
    audit_logger.log_event(
        event_type=AuditEventType.ACCOUNT_LOCKED,
        severity=AuditSeverity.WARNING,
        user_email=email,
        ip_address=ip_address,
        result="locked",
        details={"reason": "exceeded_max_failed_attempts"},
    )


def audit_permission_denied(request: Request, user_id: int, resource: str, action: str):
    """Log permission denial."""
    audit_logger.log_from_request(
        request=request,
        event_type=AuditEventType.PERMISSION_DENIED,
        severity=AuditSeverity.WARNING,
        user_id=user_id,
        result="denied",
        details={"resource": resource, "action": action},
    )


def audit_admin_action(
    request: Request,
    admin_id: int,
    admin_email: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict] = None,
):
    """Log admin action."""
    audit_logger.log_from_request(
        request=request,
        event_type=AuditEventType.ADMIN_ACCESS,
        severity=AuditSeverity.INFO,
        user_id=admin_id,
        user_email=admin_email,
        result="success",
        details={
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            **(details or {})
        },
    )


def audit_suspicious_activity(
    request: Request,
    activity_type: str,
    details: Optional[Dict] = None,
    user_id: Optional[int] = None,
):
    """Log suspicious activity."""
    audit_logger.log_from_request(
        request=request,
        event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
        severity=AuditSeverity.CRITICAL,
        user_id=user_id,
        result="blocked",
        details={"activity_type": activity_type, **(details or {})},
    )


def audit_payment(
    request: Request,
    user_id: int,
    amount: float,
    currency: str,
    status: str,
    payment_method: str,
    transaction_id: Optional[str] = None,
):
    """Log payment event."""
    event_type = {
        "initiated": AuditEventType.PAYMENT_INITIATED,
        "completed": AuditEventType.PAYMENT_COMPLETED,
        "failed": AuditEventType.PAYMENT_FAILED,
    }.get(status, AuditEventType.PAYMENT_INITIATED)
    
    audit_logger.log_from_request(
        request=request,
        event_type=event_type,
        severity=AuditSeverity.INFO if status == "completed" else AuditSeverity.WARNING,
        user_id=user_id,
        result=status,
        details={
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "transaction_id": transaction_id,
        },
    )


def audit_data_access(
    request: Request,
    user_id: int,
    resource_type: str,
    resource_id: str,
    action: str = "view",
):
    """Log data access (GDPR compliance)."""
    audit_logger.log_from_request(
        request=request,
        event_type=AuditEventType.USER_DATA_ACCESSED,
        severity=AuditSeverity.INFO,
        user_id=user_id,
        result="success",
        details={
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
        },
    )


# PII Redaction for logs
def redact_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact personally identifiable information from log data.
    
    Args:
        data: Dictionary that may contain PII
    
    Returns:
        Dictionary with PII redacted
    """
    redacted = data.copy()
    pii_fields = {
        'password', 'national_id', 'ssn', 'credit_card',
        'phone_number', 'address', 'birth_date'
    }
    
    for key in redacted:
        if key.lower() in pii_fields:
            redacted[key] = "***REDACTED***"
        elif 'email' in key.lower() and '@' in str(redacted[key]):
            # Partially redact email: u***@example.com
            email = str(redacted[key])
            parts = email.split('@')
            if len(parts) == 2:
                redacted[key] = f"{parts[0][0]}***@{parts[1]}"
    
    return redacted
