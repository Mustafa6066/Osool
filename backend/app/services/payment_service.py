"""
Osool Secure Payment Verification Service
-----------------------------------------
Abstracts the complexity of EGP payment gateway integration (e.g., Paymob, Fawry).
In a production environment, this service handles secure API calls, webhooks,
and transaction reconciliation.
"""

import os
import hmac
import hashlib
import logging
from typing import Dict, Any
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Payment Gateway Configuration (Paymob example)
PAYMOB_API_KEY = os.getenv("PAYMOB_API_KEY", "")
PAYMOB_INTEGRATION_ID = os.getenv("PAYMOB_INTEGRATION_ID", "")
PAYMOB_WEBHOOK_SECRET = os.getenv("PAYMOB_WEBHOOK_SECRET", "")


class PaymentStatus(Enum):
    """Payment transaction status."""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentService:
    """
    Handles secure, production-grade EGP payment verification.
    
    Supports:
    - InstaPay deposits
    - Fawry payments
    - Bank transfers
    
    In production, this integrates with payment gateway APIs.
    Dev mode: falls back to mock verification when API keys are absent.
    """
    
    def __init__(self):
        """Initialize the payment service with gateway credentials."""
        self.api_key = PAYMOB_API_KEY
        self.integration_id = PAYMOB_INTEGRATION_ID
        self.webhook_secret = PAYMOB_WEBHOOK_SECRET
        self._is_production = os.getenv("ENVIRONMENT") == "production"
        
        if not self.api_key:
            if self._is_production:
                logger.error("[!] PAYMOB_API_KEY not configured in PRODUCTION — payments will fail!")
            else:
                logger.warning("[!] PAYMOB_API_KEY not configured — using dev mock verification")

    def verify_egp_deposit(self, reference: str, expected_amount: float) -> Dict[str, Any]:
        """
        Verifies a reservation deposit payment via the EGP gateway API.
        
        Args:
            reference: The transaction reference number provided by the user.
            expected_amount: The minimum amount expected for the deposit.
            
        Returns:
            A dictionary containing the verification status and details.
        """
        # --- INPUT VALIDATION ---
        if not reference or len(reference) < 10:
            return {
                "status": PaymentStatus.FAILED,
                "message": "Invalid reference format. Reference must be at least 10 characters.",
                "tx_id": None,
                "verified_amount": 0
            }
        
        if not reference.startswith("EGP"):
            return {
                "status": PaymentStatus.FAILED,
                "message": "Invalid reference format. Expected EGP-prefixed reference.",
                "tx_id": None,
                "verified_amount": 0
            }
        
        if expected_amount < 10000:  # Minimum deposit threshold
            return {
                "status": PaymentStatus.FAILED,
                "message": "Deposit amount too low. Minimum deposit is 10,000 EGP.",
                "tx_id": None,
                "verified_amount": 0
            }

        # --- REAL VERIFICATION via Paymob ---
        if self.api_key:
            try:
                from app.services.paymob_service import paymob_service
                is_verified = paymob_service.verify_transaction(reference)
                
                if not is_verified:
                    logger.warning(f"Payment verification FAILED for reference: {reference}")
                    return {
                        "status": PaymentStatus.FAILED,
                        "message": "Payment could not be verified via gateway.",
                        "tx_id": None,
                        "verified_amount": 0
                    }
                
                tx_id = f"TX-{reference}"
                logger.info(f"[+] Payment verified via gateway: {reference} -> {tx_id}")
                
                return {
                    "status": PaymentStatus.VERIFIED,
                    "message": "EGP deposit successfully verified via gateway.",
                    "tx_id": tx_id,
                    "verified_amount": expected_amount
                }
                
            except Exception as e:
                logger.error(f"Payment gateway verification error: {e}")
                return {
                    "status": PaymentStatus.FAILED,
                    "message": "Payment gateway temporarily unavailable. Please try again.",
                    "tx_id": None,
                    "verified_amount": 0
                }
        
        # --- DEV FALLBACK ---
        if self._is_production:
            logger.error("Payment gateway not configured in production!")
            return {
                "status": PaymentStatus.FAILED,
                "message": "Payment gateway not configured. Contact support.",
                "tx_id": None,
                "verified_amount": 0
            }
        
        # Dev mock: generate a deterministic fake tx_id
        tx_id = f"TX-DEV-{reference.split('-')[-1]}-{abs(hash(reference)) % 10000}"
        logger.warning(f"[DEV] Mock payment verified: {reference} -> {tx_id}")
        
        return {
            "status": PaymentStatus.VERIFIED,
            "message": "[DEV] EGP deposit mock-verified (no gateway configured).",
            "tx_id": tx_id,
            "verified_amount": expected_amount
        }

    def verify_bank_transfer(self, reference: str) -> Dict[str, Any]:
        """
        Verifies the final bank transfer for sale finalization.
        This is typically a manual or semi-automated process.
        
        Args:
            reference: The bank transfer reference number.
            
        Returns:
            A dictionary containing the verification status and details.
        """
        # --- INPUT VALIDATION ---
        if not reference or len(reference) < 15:
            return {
                "status": PaymentStatus.PENDING,
                "message": "Bank transfer verification initiated. Requires manual review.",
                "tx_id": None
            }
        
        if not reference.startswith("BANK"):
            return {
                "status": PaymentStatus.PENDING,
                "message": "Bank transfer reference not recognized. Manual verification required.",
                "tx_id": None
            }

        # Bank transfers always require manual admin approval
        # We mark them as PENDING and return for admin review
        tx_id = f"SALE-TX-{abs(hash(reference)) % 10000}"
        logger.info(f"[+] Bank transfer submitted for review: {reference} -> {tx_id}")
        
        return {
            "status": PaymentStatus.PENDING,
            "message": "Bank transfer submitted. Pending admin verification.",
            "tx_id": tx_id
        }

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the authenticity of a payment gateway webhook using HMAC-SHA256.
        
        Args:
            payload: Raw request body bytes
            signature: Signature from webhook headers
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            if self._is_production:
                logger.error("Webhook secret not configured in production! Rejecting.")
                return False
            logger.warning("[DEV] Webhook secret not configured — skipping signature verification")
            return True
        
        if not signature:
            logger.warning("Webhook received without signature — rejecting")
            return False
        
        # HMAC-SHA256 signature verification
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(expected, signature)
        
        if not is_valid:
            logger.warning("Webhook HMAC verification FAILED — potential forgery attempt")
        
        return is_valid


# Singleton instance for production use
payment_service = PaymentService()
