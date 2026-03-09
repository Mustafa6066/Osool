"""
SMS Service - Phase 2: Phone OTP Authentication
------------------------------------------------
Handles OTP generation and sending via Twilio for phone verification.
"""

import os
import secrets as _secrets
import logging
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class SMSService:
    """
    SMS service for sending OTP codes via Twilio.
    Integrates with Redis for temporary code storage.
    """

    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')

        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning("⚠️ Twilio credentials not configured - SMS will not work")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)

    def send_otp(self, phone_number: str) -> str:
        """
        Send OTP code to phone number and store in Redis.

        Args:
            phone_number: Egyptian phone number in E.164 format (+201234567890)

        Returns:
            The OTP code in development mode, "sent" in production.

        Raises:
            Exception if SMS send fails
        """
        # Security Fix H1: Use cryptographically secure random for OTP
        code = ''.join([str(_secrets.randbelow(10)) for _ in range(6)])

        # Store in Redis with 5-minute TTL
        from app.services.cache import cache
        cache_key = f"otp:{phone_number}"
        cache.set_json(cache_key, {"code": code}, ttl=300)

        is_dev = os.getenv('ENVIRONMENT') == 'development'

        # Send SMS via Twilio
        if not self.client:
            logger.error("Twilio client not initialized")
            # In development, return code without sending
            if is_dev:
                logger.info(f"[DEV MODE] OTP for {phone_number}: {code}")
                return code
            else:
                raise Exception("Twilio not configured")

        try:
            message = self.client.messages.create(
                body=f"Your Osool verification code is: {code}\n\nValid for 5 minutes.",
                from_=self.from_number,
                to=phone_number
            )

            logger.info(f"✅ OTP sent to {phone_number} - SID: {message.sid}")
            # Security Fix H2: Only return OTP code in development
            if is_dev:
                return code
            return "sent"

        except Exception as e:
            logger.error(f"❌ Failed to send OTP to {phone_number}: {e}")
            raise Exception(f"SMS send failed: {str(e)}")

    def send_message(self, phone_number: str, message: str) -> bool:
        """
        Send a freeform SMS message (not an OTP).

        Args:
            phone_number: E.164 formatted phone number (+201234567890)
            message: Message body to send

        Returns:
            True on success, False on failure
        """
        is_dev = os.getenv('ENVIRONMENT') == 'development'

        if not self.client:
            if is_dev:
                logger.info(f"[DEV MODE] SMS to {phone_number}: {message}")
                return True
            logger.error("Twilio client not initialized — cannot send SMS")
            return False

        try:
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number
            )
            logger.info(f"✅ SMS sent to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send SMS to {phone_number}: {e}")
            return False

    def verify_otp(self, phone_number: str, code: str) -> bool:
        """
        Verify OTP code against stored value in Redis.

        Args:
            phone_number: Phone number that received OTP
            code: User-provided OTP code

        Returns:
            True if OTP matches and is not expired, False otherwise
        """
        import hmac as _hmac
        from app.services.cache import cache
        cache_key = f"otp:{phone_number}"
        attempt_key = f"otp_attempts:{phone_number}"
        MAX_ATTEMPTS = 5

        # SECURITY: Block after MAX_ATTEMPTS failed guesses to prevent brute force.
        # A 6-digit code has 1,000,000 combinations — limiting to 5 tries makes
        # guessing statistically impossible within the 5-minute TTL.
        attempts_data = cache.get_json(attempt_key)
        attempts = attempts_data.get("count", 0) if attempts_data else 0

        if attempts >= MAX_ATTEMPTS:
            logger.warning(f"⛔ OTP for {phone_number} is locked after {attempts} failed attempts")
            return False

        stored_data = cache.get_json(cache_key)

        if not stored_data:
            logger.warning(f"⚠️ OTP not found or expired for {phone_number}")
            return False

        stored_code = stored_data.get('code', '')

        # Security: Use timing-safe comparison to prevent timing attacks
        if _hmac.compare_digest(stored_code, code):
            # Delete OTP and reset attempt counter after successful verification (one-time use)
            cache.delete(cache_key)
            cache.delete(attempt_key)
            logger.info(f"✅ OTP verified for {phone_number}")
            return True
        else:
            # Increment attempt counter; TTL matches OTP lifetime so it auto-expires with the OTP
            cache.set_json(attempt_key, {"count": attempts + 1}, ttl=300)
            logger.warning(f"❌ Invalid OTP for {phone_number} (attempt {attempts + 1}/{MAX_ATTEMPTS})")
            return False


# Singleton instance
sms_service = SMSService()
