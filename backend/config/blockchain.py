import os
from dotenv import load_dotenv

load_dotenv()

class BlockchainConfig:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development") # development (Amoy) or production (Mainnet)
    
    # RPC URLs
    AMOY_RPC = os.getenv("ALCHEMY_RPC_AMOY", "https://rpc-amoy.polygon.technology/")
    MAINNET_RPC = os.getenv("ALCHEMY_RPC_MAINNET", "https://polygon-rpc.com/")
    
    # Contract Addresses
    USDC_AMOY = "0x41e94eb019c0762f9bfcf9fb1e58725bfb0e7582"
    USDC_MAINNET = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
    
    @classmethod
    def get_rpc_url(cls):
        if cls.ENVIRONMENT == "production":
            return cls.MAINNET_RPC
        return cls.AMOY_RPC

    @classmethod
    def get_explorer_url(cls, tx_hash: str):
         if cls.ENVIRONMENT == "production":
            return f"https://polygonscan.com/tx/{tx_hash}"
         return f"https://amoy.polygonscan.com/tx/{tx_hash}"
