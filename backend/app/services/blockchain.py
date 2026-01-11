"""
Osool Blockchain Service
------------------------
Admin service for interacting with OsoolRegistry smart contract.
This service signs transactions on behalf of verified EGP payments.

IMPORTANT: This is the ONLY authorized signer for blockchain updates.
All monetary transactions happen via InstaPay/Fawry, not crypto.

Compliance: CBE Law 194 of 2020
"""

import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Network Configuration
RPC_URL = os.getenv("POLYGON_RPC_URL", "https://rpc-amoy.polygon.technology/")
CHAIN_ID = int(os.getenv("CHAIN_ID", "80002"))  # Polygon Amoy Testnet

# Admin Wallet (Deployer - has onlyOwner access)
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
if not PRIVATE_KEY:
    print("[!] WARNING: PRIVATE_KEY not set in .env - blockchain writes will fail")
    ADMIN_ADDRESS = None
else:
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    ADMIN_ADDRESS = web3.eth.account.from_key(PRIVATE_KEY).address
    print(f"[+] Admin wallet loaded: {ADMIN_ADDRESS}")

# Contract Configuration
CONTRACT_ADDRESS = os.getenv("OSOOL_REGISTRY_ADDRESS", "")

# Minimal ABI for the functions we need
CONTRACT_ABI = [
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
        "inputs": [
            {"internalType": "uint256", "name": "_id", "type": "uint256"}
        ],
        "name": "markSold",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_id", "type": "uint256"}
        ],
        "name": "cancelReservation",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_id", "type": "uint256"}
        ],
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
        "inputs": [
            {"internalType": "uint256", "name": "_id", "type": "uint256"}
        ],
        "name": "isAvailable",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class BlockchainService:
    """
    Service for interacting with OsoolRegistry smart contract.
    All write operations require admin authorization.

    Modes:
    1. PRODUCTION: Real blockchain transactions (requires OSOOL_REGISTRY_ADDRESS)
    2. SIMULATION: Mock mode for development/testing
    """

    def __init__(self):
        """
        Initialize blockchain service with automatic simulation fallback.

        Simulation mode can be enabled by setting BLOCKCHAIN_SIMULATION_MODE=true
        in the environment. This is useful for development and testing without
        deployed contracts.
        """
        # Phase 3: Simulation mode check
        self.simulation_mode = os.getenv("BLOCKCHAIN_SIMULATION_MODE", "false").lower() == "true"

        if self.simulation_mode:
            print("[!] BLOCKCHAIN SIMULATION MODE ENABLED - No real transactions will be sent")
            self.web3 = None
            self.contract = None
            return

        # Production mode
        self.web3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.contract = None

        if CONTRACT_ADDRESS and self.web3.is_connected():
            self.contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(CONTRACT_ADDRESS),
                abi=CONTRACT_ABI
            )
            print(f"[+] Connected to OsoolRegistry at {CONTRACT_ADDRESS}")
        else:
            print("[!] Contract not initialized - set OSOOL_REGISTRY_ADDRESS or enable BLOCKCHAIN_SIMULATION_MODE")
    
    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        return self.web3.is_connected()
    
    def get_property(self, property_id: int) -> dict:
        """Get property details from blockchain"""
        # Phase 3: Simulation mode - return mock property data
        if self.simulation_mode:
            return {
                "id": property_id,
                "documentHash": f"QmSIM{'0' * 40}{property_id:08x}",
                "priceEGP": 1000000,
                "status": "AVAILABLE",
                "owner": "0x0000000000000000000000000000000000000000",
                "reservedBy": "0x0000000000000000000000000000000000000000",
                "listedAt": 1700000000,
                "reservedAt": 0,
                "soldAt": 0,
                "simulation": True
            }

        if not self.contract:
            return {"error": "Contract not initialized"}

        try:
            prop = self.contract.functions.getProperty(property_id).call()
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
    
    def is_available(self, property_id: int) -> bool:
        """Check if property is available for reservation"""
        # Phase 3: Simulation mode - always available
        if self.simulation_mode:
            return True

        if not self.contract:
            return False

        try:
            return self.contract.functions.isAvailable(property_id).call()
        except Exception:
            return False
    
    def reserve_property(self, property_id: int, buyer_address: str) -> dict:
        """
        Reserve a property on the blockchain.
        Called ONLY after EGP payment is verified via InstaPay/Fawry.

        Args:
            property_id: The on-chain property ID
            buyer_address: The buyer's wallet address (for identity linking)

        Returns:
            dict with tx_hash on success, error on failure
        """
        # Phase 3: Simulation mode - return mock success
        if self.simulation_mode:
            mock_tx_hash = f"0xSIM{'0' * 56}{property_id:08x}"
            print(f"[SIM] Property {property_id} reserved (buyer: {buyer_address[:8]}..., TX: {mock_tx_hash})")
            return {
                "success": True,
                "tx_hash": mock_tx_hash,
                "property_id": property_id,
                "buyer": buyer_address,
                "simulation": True
            }

        if not self.contract or not PRIVATE_KEY:
            return {"error": "Blockchain service not configured"}

        try:
            # Build transaction
            nonce = self.web3.eth.get_transaction_count(ADMIN_ADDRESS)
            
            # Gas Station Logic: Dynamic Gas Price + 20% buffer for fast confirmation
            current_gas_price = self.web3.eth.gas_price
            fast_gas_price = int(current_gas_price * 1.2)
            
            tx = self.contract.functions.markReserved(
                property_id, 
                Web3.to_checksum_address(buyer_address)
            ).build_transaction({
                'chainId': CHAIN_ID,
                'gas': 300000, # Safety limit
                'gasPrice': fast_gas_price,
                'nonce': nonce,
            })
            
            # Sign with admin private key
            signed_tx = self.web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            
            # Send to network
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            print(f"[+] Property {property_id} reserved on chain! TX: {self.web3.to_hex(tx_hash)}")
            
            return {
                "success": True,
                "tx_hash": self.web3.to_hex(tx_hash),
                "property_id": property_id,
                "buyer": buyer_address
            }
            
        except Exception as e:
            print(f"[!] Blockchain Error: {e}")
            return {"error": str(e)}
    
    def finalize_sale(self, property_id: int) -> dict:
        """
        Finalize property sale after full bank transfer.
        Transfers on-chain ownership to the reserver.
        """
        # Phase 3: Simulation mode - return mock success
        if self.simulation_mode:
            mock_tx_hash = f"0xSIM{'0' * 56}{property_id:08x}SOLD"
            print(f"[SIM] Property {property_id} finalized (TX: {mock_tx_hash})")
            return {
                "success": True,
                "tx_hash": mock_tx_hash,
                "property_id": property_id,
                "simulation": True
            }

        if not self.contract or not PRIVATE_KEY:
            return {"error": "Blockchain service not configured"}

        try:
            nonce = self.web3.eth.get_transaction_count(ADMIN_ADDRESS)
            
            tx = self.contract.functions.markSold(property_id).build_transaction({
                'chainId': CHAIN_ID,
                'gas': 200000,
                'gasPrice': self.web3.to_wei('30', 'gwei'),
                'nonce': nonce,
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            print(f"[+] Property {property_id} SOLD! TX: {self.web3.to_hex(tx_hash)}")
            
            return {
                "success": True,
                "tx_hash": self.web3.to_hex(tx_hash),
                "property_id": property_id
            }
            
        except Exception as e:
            print(f"[!] Blockchain Error: {e}")
            return {"error": str(e)}
    
    def cancel_reservation(self, property_id: int) -> dict:
        """Cancel a reservation (for disputes or timeout)"""
        # Phase 3: Simulation mode - return mock success
        if self.simulation_mode:
            mock_tx_hash = f"0xSIM{'0' * 56}{property_id:08x}CANC"
            print(f"[SIM] Reservation cancelled for property {property_id} (TX: {mock_tx_hash})")
            return {
                "success": True,
                "tx_hash": mock_tx_hash,
                "property_id": property_id,
                "simulation": True
            }

        if not self.contract or not PRIVATE_KEY:
            return {"error": "Blockchain service not configured"}

        try:
            nonce = self.web3.eth.get_transaction_count(ADMIN_ADDRESS)
            
            tx = self.contract.functions.cancelReservation(property_id).build_transaction({
                'chainId': CHAIN_ID,
                'gas': 200000,
                'gasPrice': self.web3.to_wei('30', 'gwei'),
                'nonce': nonce,
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            print(f"[+] Reservation cancelled for property {property_id}")
            
            return {
                "success": True,
                "tx_hash": self.web3.to_hex(tx_hash),
                "property_id": property_id
            }
            
        except Exception as e:
            print(f"[!] Blockchain Error: {e}")
            return {"error": str(e)}


# Singleton instance
blockchain_service = BlockchainService()
