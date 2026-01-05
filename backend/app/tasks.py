"""
Celery Tasks for Osool
----------------------
Background workers for long-running blockchain transactions.
"""

from app.celery_app import celery_app
from app.services.blockchain import blockchain_service

@celery_app.task(bind=True, max_retries=3)
def reserve_property_task(self, property_id: int, user_address: str):
    """
    Background task to reserve property on blockchain.
    
    Args:
        property_id (int): ID of the property.
        user_address (str): Wallet address of the buyer.
        
    Returns:
        dict: Result of the blockchain transaction.
    """
    try:
        # Check connection first
        if not blockchain_service.is_connected():
            raise Exception("Blockchain not connected")
            
        print(f"[Worker] Starting reservation for Property {property_id} by {user_address}")
        
        # This is the blocking call that takes 15-30 seconds
        result = blockchain_service.reserve_property(property_id, user_address)
        
        if "error" in result:
            raise Exception(result["error"])
            
        return result
        
    except Exception as e:
        print(f"[Worker] Task failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=10)
