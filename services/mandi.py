"""
Mandi Price Service — Fetches LIVE market prices from Data.gov.in API.
NO hardcoded fallback prices. Returns proper errors when API fails.
"""
import requests


class MandiService:
    """Fetch live commodity prices from Indian government Mandi APIs — real data only."""

    BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

    def __init__(self, api_key: str):
        self.api_key = api_key
        if not api_key or api_key.startswith("your_"):
            print("[MandiService] WARNING: No valid Data.gov.in API key configured!")

    def fetch_prices(self, crops: list[str]) -> dict:
        """
        Fetch live Mandi prices for a list of crops from Data.gov.in.

        Returns: {crop_name: {price, mandi, state, min_price, max_price, ...}}
        """
        if not self.api_key or self.api_key.startswith("your_"):
            return {c.lower(): {"error": "Data.gov.in API key not configured. Add it to .env."} for c in crops}

        results = {}
        for crop in crops:
            crop_lower = crop.lower().strip()
            result = self._fetch_single(crop_lower)
            results[crop_lower] = result
        return results

    def _fetch_single(self, crop: str) -> dict:
        """Fetch live price for a single crop from Data.gov.in."""
        # Map common crop names to Data.gov.in commodity names
        commodity_name = self._map_crop_name(crop)

        try:
            response = requests.get(self.BASE_URL, params={
                "api-key": self.api_key,
                "format": "json",
                "limit": 10,
                "filters[commodity]": commodity_name,
            }, timeout=15)

            if response.status_code == 200:
                data = response.json()
                records = data.get("records", [])

                if records and len(records) > 0:
                    # Get the most recent record
                    record = records[0]
                    modal_price = self._safe_float(record.get("modal_price", 0))
                    min_price = self._safe_float(record.get("min_price", 0))
                    max_price = self._safe_float(record.get("max_price", 0))

                    # Calculate volatility from price range
                    volatility = 0.0
                    if modal_price > 0:
                        volatility = round((max_price - min_price) / modal_price, 3)

                    # Infer trend from multiple records
                    trend = self._infer_trend(records)

                    # Infer supply level from number of active mandis
                    supply_level = self._infer_supply(records)

                    return {
                        "price": modal_price,
                        "min_price": min_price,
                        "max_price": max_price,
                        "mandi": record.get("market", "Unknown"),
                        "state": record.get("state", "Unknown"),
                        "district": record.get("district", "Unknown"),
                        "commodity": record.get("commodity", crop.title()),
                        "variety": record.get("variety", "Other"),
                        "arrival_date": record.get("arrival_date", "Unknown"),
                        "trend": trend,
                        "volatility": volatility,
                        "supply_level": supply_level,
                        "records_found": len(records),
                        "source": "Data.gov.in (Live)",
                    }
                else:
                    return {
                        "error": f"No Mandi data found for '{crop.title()}'. "
                                 f"Searched as '{commodity_name}'.",
                        "price": 0,
                        "source": "Data.gov.in (No records)",
                    }

            elif response.status_code == 401:
                return {"error": "Invalid Data.gov.in API key.", "price": 0}
            else:
                return {
                    "error": f"Data.gov.in API error (HTTP {response.status_code})",
                    "price": 0,
                }

        except requests.Timeout:
            return {"error": "Data.gov.in API timed out.", "price": 0}
        except requests.ConnectionError:
            return {"error": "Cannot connect to Data.gov.in. Check internet.", "price": 0}
        except requests.RequestException as e:
            return {"error": f"Mandi API error: {str(e)}", "price": 0}

    def _map_crop_name(self, crop: str) -> str:
        """Map internal crop names to Data.gov.in commodity names."""
        mapping = {
            "rice": "Rice", "wheat": "Wheat", "maize": "Maize",
            "sorghum": "Jowar(Sorghum)", "cotton": "Cotton",
            "sugarcane": "Sugarcane", "jute": "Jute",
            "groundnut": "Groundnut", "soyabean": "Soyabean",
            "cowpea": "Cowpea", "bengalgram": "Bengal Gram(Gram)(Whole)",
            "blackgram": "Black Gram (Urd Beans)(Whole)",
            "greengram": "Green Gram (Moong)(Whole)",
            "redgram": "Arhar (Tur/Red Gram)(Whole)",
            "sunflower": "Sunflower", "onion": "Onion",
            "tomato": "Tomato", "chillies": "Chillies(Green)",
            "cabbage": "Cabbage", "cauliflower": "Cauliflower",
            "brinjal": "Brinjal", "cucumber": "Cucumber(Kheera)",
            "watermelon": "Water Melon", "muskmelon": "Musk Melon",
            "carrot": "Carrot", "peas": "Peas(Green)",
            "pumpkin": "Pumpkin", "radish": "Raddish",
            "beetroot": "Beetroot", "sweet potato": "Sweet Potato",
            "pearl millet": "Bajra(Pearl Millet/Cumbu)",
            "ragi": "Ragi (Finger Millet)",
            "gingely": "Gingelly(Sesame)",
            "castor": "Castor Seed",
        }
        return mapping.get(crop.lower(), crop.title())

    def _safe_float(self, val) -> float:
        """Safely convert value to float."""
        try:
            return round(float(val), 2)
        except (ValueError, TypeError):
            return 0.0

    def _infer_trend(self, records: list) -> str:
        """Infer price trend from multiple market records."""
        if len(records) < 2:
            return "insufficient_data"
        try:
            prices = [self._safe_float(r.get("modal_price", 0)) for r in records[:5]]
            prices = [p for p in prices if p > 0]
            if len(prices) < 2:
                return "insufficient_data"
            avg_first = sum(prices[:len(prices)//2]) / max(len(prices[:len(prices)//2]), 1)
            avg_second = sum(prices[len(prices)//2:]) / max(len(prices[len(prices)//2:]), 1)
            if avg_first > avg_second * 1.05:
                return "rising"
            elif avg_first < avg_second * 0.95:
                return "falling"
            return "stable"
        except (ValueError, ZeroDivisionError):
            return "unknown"

    def _infer_supply(self, records: list) -> str:
        """Infer supply level from number of active mandis reporting."""
        unique_mandis = len(set(r.get("market", "") for r in records))
        if unique_mandis >= 8:
            return "high"
        elif unique_mandis >= 4:
            return "medium"
        else:
            return "low"
