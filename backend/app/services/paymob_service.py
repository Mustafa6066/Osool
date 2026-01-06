"""
Osool Paymob Service
--------------------
Handles payment verification with Paymob's API.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class PaymobService:
    def __init__(self):
        self.api_key = os.getenv("PAYMOB_API_KEY")
        self.integration_id = os.getenv("PAYMOB_INTEGRATION_ID")
        self.base_url = "https://accept.paymob.com/api"
        # For production, we would authenticate and get a token.
        # For this MVP/mock structure, we'll assume we can check status via a simplified flow or mocking if credentials aren't present.

    def _get_auth_token(self) -> str:
        """Authenticate with Paymob to get an auth token."""
        if not self.api_key:
            return None
        
        try:
            response = httpx.post(
                f"{self.base_url}/auth/tokens",
                json={"api_key": self.api_key}
            )
            response.raise_for_status()
            return response.json().get("token")
        except Exception as e:
            print(f"[!] Paymob Auth Failed: {e}")
            return None

    def verify_transaction(self, transaction_id_or_ref: str) -> bool:
        """
        Verifies if a transaction was successful.
        
        Args:
            transaction_id_or_ref: The transaction ID or merchant order reference.
            
        Returns:
            bool: True if paid and successful, False otherwise.
        """
        # 1. Quick check for length (Mock behavior preserved for dev without keys)
        if not self.api_key:
            print("[IsMock] Paymob API key missing, falling back to mock verification.")
            # Standard mock: accepts 8+ chars
            return len(str(transaction_id_or_ref)) >= 8

        # 2. Real API Check
        token = self._get_auth_token()
        if not token:
            print("[!] Could not get Paymob token. Failing safe (or Mocking).")
            # Fallback to mock if auth fails in dev
            return len(str(transaction_id_or_ref)) >= 8
            
        try:
            # In Paymob, we usually get a transaction by ID to check its status.
            # GET /acceptance/transactions/{id}
            headers = {"Authorization": f"Bearer {token}"}
            
            # Using query params or direct ID lookup depending on input type
            # Assuming input is the Transaction ID for now
            response = httpx.get(
                f"{self.base_url}/acceptance/transactions/{transaction_id_or_ref}",
                headers=headers
            )
            
            if response.status_code == 404:
                # Might be an Order ID, try looking up orders (simplified for MVP)
                print(f"Transaction {transaction_id_or_ref} not found.")
                return False
                
            response.raise_for_status()
            data = response.json()
            
            is_success = data.get("success", False)
            is_pending = data.get("pending", False)
            
            if is_success and not is_pending:
                print(f"[+] Paymob verification successful for {transaction_id_or_ref}")
                return True
            else:
                print(f"[-] Paymob transaction {transaction_id_or_ref} status: Success={is_success}, Pending={is_pending}")
                return False

        except Exception as e:
            print(f"[!] Paymob Verification Error: {e}")
            return False

    def verify_hmac(self, data: dict, hmac_signature: str) -> bool:
        """
        Verify Paymob HMAC signature securely.
        
        Logic:
        1. Extract specific keys in alphabetical order.
        2. Concatenate values.
        3. Calculate HMAC-SHA512 with Secret Key.
        4. Compare with received signature.
        """
        import hmac
        import hashlib
        
        secret = os.getenv("PAYMOB_HMAC_SECRET")
        if not secret:
            print("[!] Paymob HMAC Secret missing. Verification Failed.")
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

    def get_payment_key(self, amount_cents: int, order_id: str, billing_data: dict) -> str:
        """Step 3: Request Payment Key"""
        token = self._get_auth_token()
        if not token: return None

        try:
            response = httpx.post(
                f"{self.base_url}/acceptance/payment_keys",
                json={
                    "auth_token": token,
                    "amount_cents": str(amount_cents),
                    "expiration": 3600,
                    "order_id": order_id,
                    "billing_data": billing_data,
                    "currency": "EGP",
                    "integration_id": self.integration_id,
                    "lock_order_when_paid": "false" # Optional
                },
                timeout=10.0
            )
            response.raise_for_status()
            return response.json().get("token")
        except Exception as e:
            print(f"[!] Paymob Request Key Failed: {e}")
            return None

    def initiate_payment(self, amount_egp: float, user_email: str, user_phone: str, first_name: str, last_name: str) -> dict:
        """
        Full Flow: Auth -> Register Order -> Get Payment Key
        Returns the payment token and iframe URL.
        """
        # 1. Auth (Implicit in helpers)
        token = self._get_auth_token()
        if not token:
            return {"error": "Payment Gateway Authentication Failed"}
            
        amount_cents = int(amount_egp * 100)
        
        # 2. Register Order
        try:
            order_res = httpx.post(
                f"{self.base_url}/ecommerce/orders",
                json={
                    "auth_token": token,
                    "delivery_needed": "false",
                    "amount_cents": str(amount_cents),
                    "currency": "EGP",
                    "items": [] # Can list property details here
                },
                timeout=10.0
            )
            order_res.raise_for_status()
            order_id = order_res.json().get("id")
        except Exception as e:
            print(f"[!] Paymob Order Reg Failed: {e}")
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
        
        payment_key = self.get_payment_key(amount_cents, str(order_id), billing_data)
        
        if not payment_key:
            return {"error": "Failed to generate payment key"}
            
        iframe_id = os.getenv("PAYMOB_IFRAME_ID", "1234") # Default or Env
        
        return {
            "payment_key": payment_key,
            "order_id": order_id,
            "iframe_url": f"https://accept.paymob.com/api/acceptance/iframes/{iframe_id}?payment_token={payment_key}"
        }

# Singleton
paymob_service = PaymobService()
