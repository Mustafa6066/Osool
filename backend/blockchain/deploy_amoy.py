"""
Deploy ElitePropertyPlatform to Polygon Amoy
--------------------------------------------
Uses web3.py and solcx to compile and deploy the contract.
"""

import os
import json
from web3 import Web3
from solcx import compile_source, install_solc
from dotenv import load_dotenv

load_dotenv()

# Configuration
RPC_URL = os.getenv("ALCHEMY_RPC_URL", "https://rpc-amoy.polygon.technology/")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
PROD_ADDRESS = os.getenv("PROD_ADDRESS") # Address to potentially use as admin/relayer

def deploy():
    if not PRIVATE_KEY:
        print("❌ PRIVATE_KEY is missing in .env")
        return

    # 1. Connect to Amoy
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ Failed to connect to Polygon Amoy")
        return
    
    print(f"✅ Connected to Amoy. Chain ID: {w3.eth.chain_id}")
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"🚀 Deploying from: {account.address}")
    
    # 2. Compile Contract
    print("⏳ Compiling ElitePropertyPlatform.sol...")
    try:
        install_solc('0.8.20')
        with open("backend/blockchain/ElitePropertyPlatform.sol", "r") as f:
            source = f.read()
            
        compiled = compile_source(
            source,
            output_values=['abi', 'bin'],
            solc_version='0.8.20'
        )
        contract_id = '<stdin>:ElitePropertyPlatform'
        contract_interface = compiled[contract_id]
    except Exception as e:
        print(f"❌ Compilation Failed: {e}")
        return

    # 3. Deploy
    Contract = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )
    
    # Build Constructor TX
    # Assuming constructor takes (address _admin)
    construct_txn = Contract.constructor(account.address).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 3000000,
        'gasPrice': w3.eth.gas_price
    })
    
    signed = w3.eth.account.sign_transaction(construct_txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"✉️ Deployment TX sent: {w3.to_hex(tx_hash)}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"🎉 Deployed at: {receipt.contractAddress}")
    
    # Save Artifacts
    artifact = {
        "address": receipt.contractAddress,
        "abi": contract_interface['abi']
    }
    with open("backend/blockchain/deployment.json", "w") as f:
        json.dump(artifact, f, indent=2)

if __name__ == "__main__":
    deploy()
