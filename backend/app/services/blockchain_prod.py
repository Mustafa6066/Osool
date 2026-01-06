"""
Production Blockchain Service (Alchemy + Relayer)
-------------------------------------------------
Connects to Polygon Mainnet/Amoy via Alchemy RPC.
Implements a 'Relayer' pattern where the backend wallet pays gas fees
for Minting and Transfers, ensuring a seamless UX.
"""

import os
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv

load_dotenv()

class BlockchainServiceProd:
    def __init__(self):
        # 1. Configuration
        self.rpc_url = os.getenv("ALCHEMY_RPC_URL", "https://rpc-amoy.polygon.technology/")
        self.chain_id = int(os.getenv("CHAIN_ID", 80002)) # Amoy Default
        self.contract_address = os.getenv("ELITE_PLATFORM_ADDRESS")
        self.private_key = os.getenv("PRIVATE_KEY") # Admin/Relayer Key
        
        # 2. Initialize Web3
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0) # For Polygon/POA chains
        
        # 3. Load Contract
        if self.contract_address and self.web3.is_connected():
            # Load ABI (Assuming deployment.json exists or hardcoded common ABI)
            try:
                with open("backend/blockchain/deployment.json", "r") as f:
                    data = json.load(f)
                    self.abi = data["abi"]
            except:
                print("⚠️ Deployment artifact not found, using generic ABI or failing.")
                # Minimal ABI for critical functions
                self.abi = [
                    {"type": "function", "name": "mintFractionalShares", "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}, {"name": "propertyId", "type": "uint256"}], "outputs": []},
                    {"type": "function", "name": "balanceOf", "inputs": [{"name": "account", "type": "address"}, {"name": "id", "type": "uint256"}], "outputs": [{"name": "", "type": "uint256"}]}
                ]
                
            self.contract = self.web3.eth.contract(address=self.contract_address, abi=self.abi)
            print(f"✅ [Prod] Connected to Alchemy RPC: {self.rpc_url}")
        else:
            print("❌ [Prod] Blockchain Connection Failed or Address Missing")

    def get_gas_price(self):
        """Gas Station: Returns dynamic gas price + 10% buffer"""
        try:
            current = self.web3.eth.gas_price
            return int(current * 1.1)
        except:
            return self.web3.to_wei('50', 'gwei') # Fallback

    def execute_relayer_transaction(self, function_call):
        """
        Executes a transaction via the backend Relayer wallet.
        User does not pay gas.
        """
        if not self.private_key:
            return {"error": "Relayer Private Key missing"}

        try:
            account = self.web3.eth.account.from_key(self.private_key)
            nonce = self.web3.eth.get_transaction_count(account.address)
            
            # Build TX
            tx = function_call.build_transaction({
                'chainId': self.chain_id,
                'gas': 500000, # Managed limit
                'gasPrice': self.get_gas_price(),
                'nonce': nonce,
                'from': account.address
            })
            
            # Sign & Send
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                return {"success": True, "tx_hash": self.web3.to_hex(tx_hash)}
            else:
                return {"error": "Transaction reverted on-chain", "tx_hash": self.web3.to_hex(tx_hash)}
                
        except Exception as e:
            print(f"❌ [Relayer] TX Failed: {e}")
            return {"error": str(e)}

    def mint_fractional_shares(self, property_id: int, investor_address: str, amount: int):
        """
        Mints ERC1155 tokens to the investor. 
        Cost is covered by Osool (Relayed).
        """
        if not self.contract:
            return {"error": "Contract not initialized"}
            
        print(f"🚀 Minting {amount} shares of Property {property_id} to {investor_address}")
        
        # Function to call: mintFractionalShares(to, amount, id)
        # Note: Function signature depends on Solidity. Assuming standard pattern.
        # If Solidity differs, this needs adjustment. 
        # Using generic 'mint' or 'transfer' logic.
        
        # Checking ABI for correct function name would be ideal.
        # Assuming 'mintFractionalShares' exists from User Request context.
        
        return self.execute_relayer_transaction(
            self.contract.functions.mintFractionalShares(
                self.web3.to_checksum_address(investor_address),
                amount,
                property_id
            )
        )

blockchain_service_prod = BlockchainServiceProd()
