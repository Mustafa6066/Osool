"""
Osool Paymob Service
--------------------
Handles payment verification with Paymob's API.
"""

import os
import logging
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PaymobService:
    def __init__(self):
        self.api_key = os.getenv("PAYMOB_API_KEY")
        self.integration_id = os.getenv("PAYMOB_INTEGRATION_ID")
        self.base_url = "https://accept.paymob.com/api"

    async def _get_auth_token(self) -> Optional[str]:
        """Authenticate with Paymob to get an auth token."""
        if not self.api_key:
            logger.warning("PAYMOB_API_KEY not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/auth/tokens",
                    json={"api_key": self.api_key}
                )
                response.raise_for_status()
                return response.json().get("token")
        except httpx.TimeoutException:
            logger.error("Paymob auth request timed out")
            return None
        except Exception as e:
            logger.error("Paymob auth failed: %s", e)
            return None

    async def verify_transaction(self, transaction_id_or_ref: str) -> bool:
        """
        Verifies if a transaction was successful.
        Always fails safe — never accepts unverified transactions.
        """
        if not self.api_key:
            logger.error("PAYMOB_API_KEY not set — transaction verification rejected")
            return False

        token = await self._get_auth_token()
        if not token:
            logger.error("Could not obtain Paymob auth token — verification rejected")
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.base_url}/acceptance/transactions/{transaction_id_or_ref}",
                    headers=headers
                )

                if response.status_code == 404:
                    logger.warning("Transaction %s not found on Paymob", transaction_id_or_ref)
                    return False

                response.raise_for_status()
                data = response.json()

                is_success = data.get("success", False)
                is_pending = data.get("pending", False)

                if is_success and not is_pending:
                    logger.info("Paymob verification successful for %s", transaction_id_or_ref)
                    return True
                else:
                    logger.warning(
                        "Paymob transaction %s: success=%s, pending=%s",
                        transaction_id_or_ref, is_success, is_pending,
                    )
                    return False

        except httpx.TimeoutException:
            logger.error("Paymob verification timed out for %s", transaction_id_or_ref)
            return False
        except Exception as e:
            logger.error("Paymob verification error for %s: %s", transaction_id_or_ref, e)
            return False

    def verify_hmac(self, data: dict, hmac_signature: str) -> bool:
        """
        Verify Paymob HMAC signature securely.
        """
        import hmac
        import hashlib

        secret = os.getenv("PAYMOB_HMAC_SECRET")
        if not secret:
            logger.error("PAYMOB_HMAC_SECRET not configured — HMAC verification rejected")
            return False

        # Paymob Keys sorted alphabetically
        keys = [
            "amount_cents", "created_at", "currency", "error_occured", "has_parent_transaction",
            "id", "integration_id", "is_3d_secure", "is_auth", "is_capture", "is_refunded",
            "is_standalone_payment", "is_voided", "order.id", "owner", "pending", 
            "source_data.pan", "source_data.sub_type", "source_data.type", "success"
        ]
        
        # Extract and Concatenate
        concatenated_string = ""
        obj = data.get('obj', {})
        
        for key in keys:
            # Handle nested keys like "order.id"
            if "." in key:
                parent, child = key.split(".")
                val = obj.get(parent, {}).get(child, "")
            else:
                val = obj.get(key, "")
            
            # Convert booleans to "true"/"false" strings to match Paymob spec
            if isinstance(val, bool):
                val = "true" if val else "false"
            
            concatenated_string += str(val)
            
        # Calculate Hash
        calculated_hmac = hmac.new(
            secret.encode('utf-8'),
            concatenated_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(calculated_hmac.lower(), hmac_signature.lower())

    async def get_payment_key(self, amount_cents: int, order_id: str, billing_data: dict) -> Optional[str]:
        """Step 3: Request Payment Key"""
        token = await self._get_auth_token()
        if not token:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/acceptance/payment_keys",
                    json={
                        "auth_token": token,
                        "amount_cents": str(amount_cents),
                        "expiration": 3600,
                        "order_id": order_id,
                        "billing_data": billing_data,
                        "currency": "EGP",
                        "integration_id": self.integration_id,
                        "lock_order_when_paid": "false"
                    }
                )
                response.raise_for_status()
                return response.json().get("token")
        except Exception as e:
            logger.error("Paymob payment key request failed: %s", e)
            return None

    async def initiate_payment(self, amount_egp: float, user_email: str, user_phone: str, first_name: str, last_name: str) -> dict:
        """
        Full Flow: Auth -> Register Order -> Get Payment Key
        Returns the payment token and iframe URL.
        """
        token = await self._get_auth_token()
        if not token:
            return {"error": "Payment gateway authentication failed"}

        amount_cents = int(amount_egp * 100)

        # 2. Register Order
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                order_res = await client.post(
                    f"{self.base_url}/ecommerce/orders",
                    json={
                        "auth_token": token,
                        "delivery_needed": "false",
                        "amount_cents": str(amount_cents),
                        "currency": "EGP",
                        "items": []
                    }
                )
                order_res.raise_for_status()
                order_id = order_res.json().get("id")
        except Exception as e:
            logger.error("Paymob order registration failed: %s", e)
            return {"error": "Failed to create payment order"}

        # 3. Get Payment Key
        # Paymob requires billing data, even if dummy for digital goods
        billing_data = {
            "apartment": "NA", 
            "email": user_email, 
            "floor": "NA", 
            "first_name": first_name, 
            "street": "Digital Transaction", 
            "building": "NA", 
            "phone_number": user_phone, 
            "shipping_method": "PKG", 
            "postal_code": "00000", 
            "city": "Cairo", 
            "country": "EG", 
            "last_name": last_name, 
            "state": "Cairo"
        }
        
        payment_key = await self.get_payment_key(amount_cents, str(order_id), billing_data)
        
        if not payment_key:
            return {"error": "Failed to generate payment key"}

        # Get iframe ID from environment (fail-fast for production security)
        iframe_id = os.getenv("PAYMOB_IFRAME_ID")
        if not iframe_id:
            raise ValueError(
                "PAYMOB_IFRAME_ID environment variable must be set. "
                "No fallback provided for security. "
                "Obtain your iframe ID from Paymob dashboard."
            )

        return {
            "payment_key": payment_key,
            "order_id": order_id,
            "iframe_url": f"https://accept.paymob.com/api/acceptance/iframes/{iframe_id}?payment_token={payment_key}"
        }

# Singleton
paymob_service = PaymobService()
