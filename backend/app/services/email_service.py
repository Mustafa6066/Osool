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
        verification_link = f"{self.frontend_url}/verify-email?token={token}"

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
        reset_link = f"{self.frontend_url}/reset-password?token={token}"

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

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Internal method to send email via SendGrid.

        Args:
            to_email: Recipient
            subject: Email subject
            html_content: HTML body

        Returns:
            True if sent successfully
        """
        if not self.client:
            logger.warning(f"[DEV MODE] Would send email to {to_email}: {subject}")
            return True  # Return success in dev mode

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


def create_verification_token() -> str:
    """
    Generate a secure random token for email verification or password reset.

    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(32)


# Singleton instance
email_service = EmailService()
