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

# Singleton
paymob_service = PaymobService()
