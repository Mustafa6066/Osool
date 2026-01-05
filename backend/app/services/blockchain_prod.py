"""
Osool Blockchain Service (Production)
-------------------------------------
Admin service for interacting with all Osool smart contracts.
Uses a dedicated key management function (simulated KMS) for signing.

Contracts:
- OsoolRegistry: Property status and ownership records
- ElitePropertyPlatform: Fractional ownership and escrow

Compliance: CBE Law 194 of 2020
"""

import os
from web3 import Web3
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

RPC_URL = os.getenv("POLYGON_RPC_URL_PROD", "https://polygon-mainnet.infura.io/v3/YOUR_KEY")
CHAIN_ID = int(os.getenv("CHAIN_ID_PROD", "137"))  # Polygon Mainnet

# Contract Addresses (Production Deployment)
CONTRACT_ADDRESSES = {
    "registry": os.getenv("OSOOL_REGISTRY_ADDRESS", ""),
    "platform": os.getenv("ELITE_PLATFORM_ADDRESS", ""),
    "token": os.getenv("ELITE_TOKEN_ADDRESS", ""),
    "nft": os.getenv("ELITE_NFT_ADDRESS", "")
}

# Admin Wallet (The address that owns the contracts and signs transactions)
ADMIN_ADDRESS = os.getenv("ADMIN_WALLET_ADDRESS", "")


def get_admin_private_key() -> str:
    """
    Simulates fetching the private key from a secure Key Management Service (KMS).
    
    In production, this would be an API call to:
    - AWS KMS
    - Azure Key Vault
    - Google Cloud KMS
    - HashiCorp Vault
    """
    private_key = os.getenv("PRIVATE_KEY_PROD", os.getenv("PRIVATE_KEY", ""))
    if not private_key:
        raise ValueError("Production Private Key not found. Check KMS or environment variables.")
    return private_key


# ═══════════════════════════════════════════════════════════════
# CONTRACT ABIs
# ═══════════════════════════════════════════════════════════════

# Registry ABI - Core property status functions
REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "_id", "type": "uint256"},
            {"internalType": "address", "name": "_buyer", "type": "address"}
        ],
        "name": "markReserved",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_id", "type": "uint256"}],
        "name": "markSold",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_id", "type": "uint256"}],
        "name": "getProperty",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "id", "type": "uint256"},
                    {"internalType": "string", "name": "legalDocumentHash", "type": "string"},
                    {"internalType": "uint256", "name": "priceEGP", "type": "uint256"},
                    {"internalType": "uint8", "name": "status", "type": "uint8"},
                    {"internalType": "address", "name": "owner", "type": "address"},
                    {"internalType": "address", "name": "reservedBy", "type": "address"},
                    {"internalType": "uint256", "name": "listedAt", "type": "uint256"},
                    {"internalType": "uint256", "name": "reservedAt", "type": "uint256"},
                    {"internalType": "uint256", "name": "soldAt", "type": "uint256"}
                ],
                "internalType": "struct OsoolRegistry.Property",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_id", "type": "uint256"}],
        "name": "isAvailable",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    # New function to store AI-verified document hash
    {
        "inputs": [
            {"internalType": "uint256", "name": "_id", "type": "uint256"},
            {"internalType": "string", "name": "_aiHash", "type": "string"}
        ],
        "name": "setAIVerifiedHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Platform ABI - Fractional ownership functions
PLATFORM_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "_propertyId", "type": "uint256"},
            {"internalType": "address", "name": "_investor", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"}
        ],
        "name": "mintFractionalShares",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_propertyId", "type": "uint256"}],
        "name": "transferAssetToPlatform",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


class BlockchainServiceProd:
    """
    Production-grade blockchain service for Osool platform.
    
    Features:
    - KMS integration for secure key management
    - Multi-contract support (Registry + Platform)
    - Transaction receipt confirmation
    - Gas optimization using network gas prices
    """
    
    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.registry_contract = None
        self.platform_contract = None
        
        if self.web3.is_connected():
            # Initialize Registry contract
            if CONTRACT_ADDRESSES["registry"]:
                self.registry_contract = self.web3.eth.contract(
                    address=Web3.to_checksum_address(CONTRACT_ADDRESSES["registry"]), 
                    abi=REGISTRY_ABI
                )
                print(f"[+] Connected to OsoolRegistry at {CONTRACT_ADDRESSES['registry']}")
            
            # Initialize Platform contract
            if CONTRACT_ADDRESSES["platform"]:
                self.platform_contract = self.web3.eth.contract(
                    address=Web3.to_checksum_address(CONTRACT_ADDRESSES["platform"]), 
                    abi=PLATFORM_ABI
                )
                print(f"[+] Connected to ElitePlatform at {CONTRACT_ADDRESSES['platform']}")
            
            if ADMIN_ADDRESS:
                print(f"[+] Admin wallet: {ADMIN_ADDRESS}")
        else:
            print("[!] Failed to connect to blockchain RPC.")

    def _send_transaction(self, contract_function) -> Dict[str, Any]:
        """
        Helper function to sign and send a transaction using the admin key.
        
        Features:
        - KMS key retrieval
        - Dynamic gas pricing
        - Transaction receipt confirmation
        """
        try:
            private_key = get_admin_private_key()
            admin_address = self.web3.eth.account.from_key(private_key).address
            nonce = self.web3.eth.get_transaction_count(admin_address)
            
            # Build transaction with dynamic gas price
            tx = contract_function.build_transaction({
                'chainId': CHAIN_ID,
                'gas': 300000,  # Increased gas limit for complex transactions
                'gasPrice': self.web3.eth.gas_price,  # Use current network gas price
                'nonce': nonce,
            })
            
            # Sign transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            # Wait for transaction receipt for production-grade reliability
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 0:
                raise Exception("Transaction failed on-chain.")
            
            print(f"[+] Transaction confirmed: {self.web3.to_hex(tx_hash)}")
            
            return {
                "success": True,
                "tx_hash": self.web3.to_hex(tx_hash),
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed
            }
            
        except Exception as e:
            print(f"[!] Blockchain Transaction Error: {e}")
            return {"error": str(e), "success": False}

    # ═══════════════════════════════════════════════════════════════
    # REGISTRY FUNCTIONS (Core Trust Layer)
    # ═══════════════════════════════════════════════════════════════

    def reserve_property(self, property_id: int, buyer_address: str) -> Dict[str, Any]:
        """
        Mark property as reserved after EGP payment verification.
        
        Args:
            property_id: The on-chain property ID
            buyer_address: Buyer's wallet address for identity linking
        """
        if not self.registry_contract:
            return {"error": "Registry contract not initialized", "success": False}
        
        func = self.registry_contract.functions.markReserved(
            property_id, 
            self.web3.to_checksum_address(buyer_address)
        )
        return self._send_transaction(func)

    def finalize_sale(self, property_id: int) -> Dict[str, Any]:
        """
        Mark property as sold after full bank transfer.
        Transfers on-chain ownership to the reserver.
        """
        if not self.registry_contract:
            return {"error": "Registry contract not initialized", "success": False}
        
        func = self.registry_contract.functions.markSold(property_id)
        return self._send_transaction(func)

    def set_ai_verified_hash(self, property_id: int, ai_document_hash: str) -> Dict[str, Any]:
        """
        Stores the hash of the AI-vetted legal document on the registry.
        This is the core AI-Blockchain synergy.
        
        Args:
            property_id: The on-chain property ID
            ai_document_hash: SHA256 hash of the AI analysis result
        """
        if not self.registry_contract:
            return {"error": "Registry contract not initialized", "success": False}
        
        func = self.registry_contract.functions.setAIVerifiedHash(
            property_id, 
            ai_document_hash
        )
        return self._send_transaction(func)

    # ═══════════════════════════════════════════════════════════════
    # PLATFORM FUNCTIONS (Fractional Ownership Layer)
    # ═══════════════════════════════════════════════════════════════

    def mint_fractional_shares(self, property_id: int, investor_address: str, amount: int) -> Dict[str, Any]:
        """
        Mints fractional shares (tokens) to an investor after payment.
        This is the core Nawy Shares competitor feature.
        
        Args:
            property_id: The property being fractionalized
            investor_address: Investor's wallet to receive shares
            amount: Number of share tokens to mint
        """
        if not self.platform_contract:
            return {"error": "Platform contract not initialized", "success": False}
        
        func = self.platform_contract.functions.mintFractionalShares(
            property_id,
            self.web3.to_checksum_address(investor_address),
            amount
        )
        return self._send_transaction(func)

    def transfer_asset_to_platform(self, property_id: int) -> Dict[str, Any]:
        """
        Transfers the underlying asset ownership record to the platform/fund.
        This must happen before fractionalization.
        """
        if not self.platform_contract:
            return {"error": "Platform contract not initialized", "success": False}
        
        func = self.platform_contract.functions.transferAssetToPlatform(property_id)
        return self._send_transaction(func)

    # ═══════════════════════════════════════════════════════════════
    # VIEW FUNCTIONS
    # ═══════════════════════════════════════════════════════════════

    def get_property(self, property_id: int) -> Dict[str, Any]:
        """Get property details from blockchain."""
        if not self.registry_contract:
            return {"error": "Registry contract not initialized"}
        
        try:
            prop = self.registry_contract.functions.getProperty(property_id).call()
            return {
                "id": prop[0],
                "documentHash": prop[1],
                "priceEGP": prop[2],
                "status": ["AVAILABLE", "RESERVED", "SOLD"][prop[3]],
                "owner": prop[4],
                "reservedBy": prop[5],
                "listedAt": prop[6],
                "reservedAt": prop[7],
                "soldAt": prop[8]
            }
        except Exception as e:
            return {"error": str(e)}

    def is_connected(self) -> bool:
        """Check if connected to blockchain."""
        return self.web3.is_connected()


# Singleton instance for production use
blockchain_service_prod = BlockchainServiceProd()
