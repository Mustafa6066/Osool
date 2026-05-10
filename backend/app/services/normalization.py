import re

class PropertyNormalizer:
    @staticmethod
    def clean_price(raw_price: str) -> int:
        """Removes "EGP", "جنيه", commas, and spaces"""
        if not raw_price:
            return 0
        cleaned = re.sub(r'[^\d]', '', str(raw_price))
        return int(cleaned) if cleaned else 0

    @staticmethod
    def map_finishing(raw_status: str) -> str:
        if not raw_status:
            return "UNKNOWN"
        text = raw_status.lower()
        if "core" in text or "طوب" in text or "محارة" in text:
            return "CORE_AND_SHELL"
        if "finished" in text or "تشطيب" in text:
            return "FULLY_FINISHED"
        return "UNKNOWN"

    @staticmethod
    def normalize_area(area_text: str) -> str:
        """Maps Tagamoa, Fifth Settlement, etc., to DB standard"""
        if not area_text:
            return "other"

        text = area_text.lower()
        if any(x in text for x in ["التجمع", "الخامس", "new cairo", "fifth", "tagamoa", "cairo new"]):
            return "new cairo"
        if any(x in text for x in ["zayed", "زايد", "sheikh"]):
            return "sheikh zayed"
        if any(x in text for x in ["october", "اكتوبر", "6th"]):
            return "6th of october"

        return "other"

    @staticmethod
    def extract_size(raw_size: str) -> int:
        """Extracts square meters from text"""
        if not raw_size:
            return 0
        cleaned = re.search(r'(\d+)', str(raw_size))
        return int(cleaned.group(1)) if cleaned else 0
