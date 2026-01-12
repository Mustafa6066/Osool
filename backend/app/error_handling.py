"""
Comprehensive Error Handling for Osool Backend
-----------------------------------------------
User-friendly error messages with proper logging and monitoring support.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ERROR RESPONSE MODELS
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Structured error detail for API responses."""
    error_code: str
    message: str
    message_ar: str
    user_message: str
    user_message_ar: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = datetime.utcnow().isoformat()
    request_id: Optional[str] = None


class OsoolException(Exception):
    """Base exception for all Osool errors."""

    def __init__(
        self,
        message: str,
        message_ar: str,
        user_message: str,
        user_message_ar: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.message_ar = message_ar
        self.user_message = user_message
        self.user_message_ar = user_message_ar
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


# ---------------------------------------------------------------------------
# SPECIFIC ERROR TYPES
# ---------------------------------------------------------------------------

class PropertyNotFoundError(OsoolException):
    """Property not found in database."""
    def __init__(self, property_id: int):
        super().__init__(
            message=f"Property {property_id} not found",
            message_ar=f"العقار رقم {property_id} غير موجود",
            user_message="We couldn't find this property. It may have been sold or removed.",
            user_message_ar="لم نتمكن من العثور على هذا العقار. ربما تم بيعه أو إزالته.",
            error_code="PROPERTY_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"property_id": property_id}
        )


class PropertyUnavailableError(OsoolException):
    """Property is not available for sale."""
    def __init__(self, property_id: int, reason: str = "sold"):
        super().__init__(
            message=f"Property {property_id} is unavailable: {reason}",
            message_ar=f"العقار رقم {property_id} غير متاح: {reason}",
            user_message=f"This property is no longer available ({reason}). Let me find you similar options.",
            user_message_ar=f"هذا العقار لم يعد متاحاً ({reason}). دعني أجد لك خيارات مشابهة.",
            error_code="PROPERTY_UNAVAILABLE",
            status_code=status.HTTP_409_CONFLICT,
            details={"property_id": property_id, "reason": reason}
        )


class AIServiceError(OsoolException):
    """AI service (Claude/OpenAI) error."""
    def __init__(self, service: str, original_error: str):
        super().__init__(
            message=f"{service} service error: {original_error}",
            message_ar=f"خطأ في خدمة {service}: {original_error}",
            user_message="I'm having trouble processing your request. Please try again in a moment.",
            user_message_ar="أواجه مشكلة في معالجة طلبك. يرجى المحاولة مرة أخرى بعد قليل.",
            error_code="AI_SERVICE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service, "original_error": original_error}
        )


class RateLimitError(OsoolException):
    """Rate limit exceeded."""
    def __init__(self, limit: int, window: str):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            message_ar=f"تم تجاوز حد الطلبات: {limit} طلب لكل {window}",
            user_message=f"You've reached the request limit ({limit} per {window}). Please wait a moment.",
            user_message_ar=f"لقد وصلت إلى حد الطلبات ({limit} لكل {window}). يرجى الانتظار قليلاً.",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"limit": limit, "window": window}
        )


class AuthenticationError(OsoolException):
    """Authentication failed."""
    def __init__(self, reason: str = "invalid_credentials"):
        super().__init__(
            message=f"Authentication failed: {reason}",
            message_ar=f"فشل التحقق: {reason}",
            user_message="Authentication failed. Please check your credentials and try again.",
            user_message_ar="فشل التحقق. يرجى التحقق من بيانات الدخول والمحاولة مرة أخرى.",
            error_code="AUTHENTICATION_FAILED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"reason": reason}
        )


class ValidationError(OsoolException):
    """Request validation error."""
    def __init__(self, field: str, issue: str):
        super().__init__(
            message=f"Validation error on field '{field}': {issue}",
            message_ar=f"خطأ في التحقق من الحقل '{field}': {issue}",
            user_message=f"There's an issue with your input: {issue}",
            user_message_ar=f"هناك مشكلة في المدخلات: {issue}",
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": field, "issue": issue}
        )


class BlockchainError(OsoolException):
    """Blockchain service error."""
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Blockchain {operation} failed: {reason}",
            message_ar=f"فشلت عملية البلوكتشين {operation}: {reason}",
            user_message="There was an issue verifying on the blockchain. Our team will resolve this shortly.",
            user_message_ar="حدثت مشكلة في التحقق عبر البلوكتشين. سيقوم فريقنا بحل هذا قريباً.",
            error_code="BLOCKCHAIN_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"operation": operation, "reason": reason}
        )


class DatabaseError(OsoolException):
    """Database operation error."""
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Database {operation} failed: {reason}",
            message_ar=f"فشلت عملية قاعدة البيانات {operation}: {reason}",
            user_message="We're experiencing technical difficulties. Please try again in a moment.",
            user_message_ar="نواجه صعوبات تقنية. يرجى المحاولة مرة أخرى بعد قليل.",
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"operation": operation, "reason": reason}
        )


class CostLimitError(OsoolException):
    """AI cost limit exceeded."""
    def __init__(self, current_cost: float, limit: float):
        super().__init__(
            message=f"Cost limit exceeded: ${current_cost:.2f} / ${limit:.2f}",
            message_ar=f"تم تجاوز حد التكلفة: ${current_cost:.2f} / ${limit:.2f}",
            user_message="Your session has reached the usage limit. Please start a new conversation.",
            user_message_ar="وصلت جلستك إلى حد الاستخدام. يرجى بدء محادثة جديدة.",
            error_code="COST_LIMIT_EXCEEDED",
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            details={"current_cost": current_cost, "limit": limit}
        )


# ---------------------------------------------------------------------------
# ERROR HANDLERS
# ---------------------------------------------------------------------------

async def osool_exception_handler(request: Request, exc: OsoolException) -> JSONResponse:
    """Handle OsoolException and return user-friendly error."""

    # Log the error
    logger.error(
        f"OsoolException: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path
        }
    )

    # Create error response
    error_detail = ErrorDetail(
        error_code=exc.error_code,
        message=exc.message,
        message_ar=exc.message_ar,
        user_message=exc.user_message,
        user_message_ar=exc.user_message_ar,
        details=exc.details,
        request_id=request.headers.get("X-Request-ID")
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_detail.dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""

    errors = exc.errors()
    first_error = errors[0] if errors else {}

    logger.warning(
        f"Validation error: {first_error}",
        extra={"path": request.url.path, "errors": errors}
    )

    error_detail = ErrorDetail(
        error_code="VALIDATION_ERROR",
        message=f"Validation error: {first_error.get('msg', 'Invalid input')}",
        message_ar=f"خطأ في التحقق: {first_error.get('msg', 'مدخلات غير صالحة')}",
        user_message="Please check your input and try again.",
        user_message_ar="يرجى التحقق من المدخلات والمحاولة مرة أخرى.",
        details={"validation_errors": errors},
        request_id=request.headers.get("X-Request-ID")
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_detail.dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""

    # Log full traceback for debugging
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "traceback": traceback.format_exc()
        }
    )

    error_detail = ErrorDetail(
        error_code="INTERNAL_SERVER_ERROR",
        message=str(exc),
        message_ar="خطأ داخلي في الخادم",
        user_message="An unexpected error occurred. Our team has been notified.",
        user_message_ar="حدث خطأ غير متوقع. تم إبلاغ فريقنا.",
        details={"type": type(exc).__name__},
        request_id=request.headers.get("X-Request-ID")
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_detail.dict()
    )


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def handle_ai_error(service: str, error: Exception) -> None:
    """Raise appropriate error for AI service failures."""
    error_msg = str(error)

    # Check for specific error types
    if "rate_limit" in error_msg.lower():
        raise AIServiceError(service, "Rate limit exceeded")
    elif "timeout" in error_msg.lower():
        raise AIServiceError(service, "Request timeout")
    elif "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
        raise AIServiceError(service, "Authentication failed")
    else:
        raise AIServiceError(service, error_msg)


def handle_database_error(operation: str, error: Exception) -> None:
    """Raise appropriate error for database failures."""
    error_msg = str(error)

    # Check for specific error types
    if "connection" in error_msg.lower():
        raise DatabaseError(operation, "Connection failed")
    elif "timeout" in error_msg.lower():
        raise DatabaseError(operation, "Query timeout")
    else:
        raise DatabaseError(operation, error_msg)


def handle_blockchain_error(operation: str, error: Exception) -> None:
    """Raise appropriate error for blockchain failures."""
    error_msg = str(error)

    # Check for specific error types
    if "network" in error_msg.lower() or "connection" in error_msg.lower():
        raise BlockchainError(operation, "Network connection failed")
    elif "gas" in error_msg.lower():
        raise BlockchainError(operation, "Insufficient gas")
    elif "revert" in error_msg.lower():
        raise BlockchainError(operation, "Transaction reverted")
    else:
        raise BlockchainError(operation, error_msg)
