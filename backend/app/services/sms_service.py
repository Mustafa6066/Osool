"""
SMS Service - Phase 2: Phone OTP Authentication
------------------------------------------------
Handles OTP generation and sending via Twilio for phone verification.
"""

import os
import random
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
            The OTP code (for development testing only)

        Raises:
            Exception if SMS send fails
        """
        # Generate 6-digit OTP
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # Store in Redis with 5-minute TTL
        from app.services.cache import cache
        cache_key = f"otp:{phone_number}"
        cache.set_json(cache_key, {"code": code}, ttl=300)

        # Send SMS via Twilio
        if not self.client:
            logger.error("Twilio client not initialized")
            # In development, return code without sending
            if os.getenv('ENVIRONMENT') == 'development':
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
            return code  # Return for dev testing

        except Exception as e:
            logger.error(f"❌ Failed to send OTP to {phone_number}: {e}")
            raise Exception(f"SMS send failed: {str(e)}")

    def verify_otp(self, phone_number: str, code: str) -> bool:
        """
        Verify OTP code against stored value in Redis.

        Args:
            phone_number: Phone number that received OTP
            code: User-provided OTP code

        Returns:
            True if OTP matches and is not expired, False otherwise
        """
        from app.services.cache import cache
        cache_key = f"otp:{phone_number}"

        stored_data = cache.get_json(cache_key)

        if not stored_data:
            logger.warning(f"⚠️ OTP not found or expired for {phone_number}")
            return False

        stored_code = stored_data.get('code')

        if stored_code == code:
            # Delete OTP after successful verification (one-time use)
            cache.redis.delete(cache_key)
            logger.info(f"✅ OTP verified for {phone_number}")
            return True
        else:
            logger.warning(f"❌ Invalid OTP for {phone_number}")
            return False


# Singleton instance
sms_service = SMSService()
