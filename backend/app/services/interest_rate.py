from datetime import datetime

class InterestRateService:
    """
    Central Bank of Egypt (CBE) Interest Rate Service.
    In a real production environment, this would scrape 'cbe.org.eg' or use an API.
    For V1.0, we use a conservative 'Safe Harbor' rate updated weekly.
    """
    
    LAST_UPDATED = datetime(2026, 1, 7)
    CORRIDOR_DEPOSIT = 22.25
    CORRIDOR_LENDING = 23.25
    
    # Mortgage typically moves with Lending Rate + Margin
    BASE_MORTGAGE_RATE = 25.0 

    @staticmethod
    def get_current_mortgage_rate() -> float:
        """
        Returns the current estimated mortgage rate (%).
        """
        # Feature Flag: Connect to Live Scraper here
        return InterestRateService.BASE_MORTGAGE_RATE

interest_rate_service = InterestRateService()
