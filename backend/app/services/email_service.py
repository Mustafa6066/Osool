"""
Email Service - Phase 2: Email Verification & Password Reset
-------------------------------------------------------------
Handles email sending via SendGrid for verification and password reset.
"""

import os
import secrets
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service using SendGrid for transactional emails.
    """

    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@osool.com')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

        if not self.api_key:
            logger.warning("⚠️ SendGrid API key not configured - emails will not be sent")
            self.client = None
        else:
            self.client = SendGridAPIClient(self.api_key)

    def send_verification_email(self, email: str, token: str) -> bool:
        """
        Send email verification link.

        Args:
            email: Recipient email address
            token: Verification token

        Returns:
            True if sent successfully, False otherwise
        """
        from urllib.parse import quote
        # SECURITY FIX V9: URL-encode token to prevent injection attacks
        encoded_token = quote(token, safe='')
        verification_link = f"{self.frontend_url}/verify-email?token={encoded_token}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🏠 Osool</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0;">Verify Your Email</p>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <h2>Welcome to Osool!</h2>
                <p>Thank you for signing up. Please verify your email address by clicking the button below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}"
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white; padding: 15px 30px; text-decoration: none;
                              border-radius: 5px; display: inline-block;">
                        Verify Email
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    Or copy this link: <br>
                    <a href="{verification_link}">{verification_link}</a>
                </p>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">
                    This link will expire in 24 hours. If you didn't sign up for Osool, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=email,
            subject="Verify your Osool account",
            html_content=html_content
        )

    def send_reset_email(self, email: str, token: str) -> bool:
        """
        Send password reset link.

        Args:
            email: Recipient email address
            token: Reset token

        Returns:
            True if sent successfully, False otherwise
        """
        from urllib.parse import quote
        # SECURITY FIX V9: URL-encode token to prevent injection attacks
        encoded_token = quote(token, safe='')
        reset_link = f"{self.frontend_url}/reset-password?token={encoded_token}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🏠 Osool</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0;">Reset Your Password</p>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password. Click the button below to choose a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}"
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white; padding: 15px 30px; text-decoration: none;
                              border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    Or copy this link: <br>
                    <a href="{reset_link}">{reset_link}</a>
                </p>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">
                    This link will expire in 1 hour. If you didn't request a password reset, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=email,
            subject="Reset your Osool password",
            html_content=html_content
        )

    def send_subscription_confirmation(self, email: str, period_end, amount_egp: float) -> bool:
        """Osool Pro activation receipt (bilingual)."""
        end_str = period_end.strftime("%Y-%m-%d") if hasattr(period_end, "strftime") else str(period_end)
        html_content = f"""
        <html dir="rtl">
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #064e3b; padding: 24px; border-radius: 12px; color: #ffffff;">
                <h2 style="margin-top: 0;">🎉 أهلاً بك في أصول برو!</h2>
                <p>تم تفعيل اشتراكك بنجاح. تقدر دلوقتي تستخدم كل مزايا أصول برو:
                فحوصات بلا حدود، بيانات السماسرة كاملة، وتنبيهات اللقطات.</p>
                <p><strong>قيمة الاشتراك:</strong> {amount_egp:,.0f} جنيه</p>
                <p><strong>صالح حتى:</strong> {end_str}</p>
                <hr style="border-color: #10b981;">
                <p dir="ltr" style="color: #d1fae5;">
                    Welcome to Osool Pro! Your subscription is active until {end_str}.
                    Enjoy unlimited Reality Checks, unmasked deal contacts, and La2ta alerts.
                </p>
            </div>
        </body>
        </html>
        """
        return self._send_email(
            to_email=email,
            subject="✅ اشتراك أصول برو مُفعّل | Osool Pro Activated",
            html_content=html_content,
        )

    def send_report_ready(self, email: str, report_title: str, dashboard_url: str) -> bool:
        """Notify the buyer that their purchased AI report is ready."""
        html_content = f"""
        <html dir="rtl">
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1e293b; padding: 24px; border-radius: 12px; color: #ffffff;">
                <h2 style="margin-top: 0;">📊 تقريرك جاهز!</h2>
                <p>تقرير "{report_title}" اتجهز وتقدر تحمله من لوحة التحكم.</p>
                <p style="text-align: center; margin: 24px 0;">
                    <a href="{dashboard_url}" style="background: #10b981; color: #fff;
                       padding: 12px 28px; border-radius: 8px; text-decoration: none;">
                        تحميل التقرير | Download Report
                    </a>
                </p>
                <p dir="ltr" style="color: #cbd5e1;">
                    Your report "{report_title}" is ready in your Osool dashboard.
                </p>
            </div>
        </body>
        </html>
        """
        return self._send_email(
            to_email=email,
            subject="📊 تقرير أصول جاهز للتحميل | Your Osool Report is Ready",
            html_content=html_content,
        )

    def send_subscription_expired(self, email: str, pricing_url: str) -> bool:
        """Renewal nudge after Osool Pro expiry."""
        html_content = f"""
        <html dir="rtl">
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1e293b; padding: 24px; border-radius: 12px; color: #ffffff;">
                <h2 style="margin-top: 0;">انتهى اشتراكك في أصول برو</h2>
                <p>رجعت للباقة المجانية. جدد اشتراكك عشان ترجع للفحوصات غير المحدودة
                وبيانات السماسرة الكاملة وتنبيهات اللقطات.</p>
                <p style="text-align: center; margin: 24px 0;">
                    <a href="{pricing_url}" style="background: #10b981; color: #fff;
                       padding: 12px 28px; border-radius: 8px; text-decoration: none;">
                        جدد الآن | Renew Now
                    </a>
                </p>
                <p dir="ltr" style="color: #cbd5e1;">
                    Your Osool Pro subscription has expired. Renew to restore unlimited
                    access and deal alerts.
                </p>
            </div>
        </body>
        </html>
        """
        return self._send_email(
            to_email=email,
            subject="اشتراك أصول برو انتهى — جدد الآن | Osool Pro Expired",
            html_content=html_content,
        )

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Internal method to send email via SendGrid.

        Args:
            to_email: Recipient
            subject: Email subject
            html_content: HTML body

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.client:
            is_production = os.getenv("ENVIRONMENT") == "production"
            if is_production:
                logger.error(f"[EMAIL] SendGrid not configured in production — email NOT sent to {to_email}: {subject}")
                return False
            logger.warning(f"[DEV MODE] Would send email to {to_email}: {subject}")
            return True  # Acceptable only in dev/staging

        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )

            response = self.client.send(message)
            logger.info(f"✅ Email sent to {to_email} - Status: {response.status_code}")
            return response.status_code == 202

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False


def create_verification_token(purpose: str = "verify", ttl_seconds: int = 86400) -> str:
    """
    Generate a secure random token for email verification or password reset.
    Also stores the token in Redis with an expiry TTL for time-limited validity.

    Args:
        purpose: "verify" (24h) or "reset" (1h)
        ttl_seconds: Time-to-live in seconds (default: 24 hours for verification)

    Returns:
        URL-safe token string
    """
    token = secrets.token_urlsafe(32)

    # Store in Redis with TTL so tokens auto-expire
    try:
        from app.services.cache import cache
        cache_key = f"email_token:{purpose}:{token}"
        cache.set_json(cache_key, {"valid": True}, ttl=ttl_seconds)
    except Exception:
        # If Redis unavailable, token still works via DB but without expiry
        logger.warning("Redis unavailable for email token TTL — token will not auto-expire")

    return token


def is_verification_token_valid(token: str, purpose: str = "verify") -> bool:
    """
    Check if a verification/reset token is still valid (not expired).

    Args:
        token: The token to validate
        purpose: "verify" or "reset"

    Returns:
        True if valid (exists in Redis and not expired)
    """
    try:
        from app.services.cache import cache
        cache_key = f"email_token:{purpose}:{token}"
        data = cache.get_json(cache_key)
        if data and data.get("valid"):
            return True
    except Exception:
        # Fail closed — never grant access when validity can't be confirmed
        logger.warning("Redis unavailable during token validation — rejecting token")
        return False
    return False


def consume_verification_token(token: str, purpose: str = "verify"):
    """Delete a used token from Redis (one-time use)."""
    try:
        from app.services.cache import cache
        cache_key = f"email_token:{purpose}:{token}"
        cache.delete(cache_key)
    except Exception as e:
        logger.warning("consume_verification_token: Redis cleanup failed for purpose=%s: %s", purpose, e)


# Singleton instance
email_service = EmailService()
