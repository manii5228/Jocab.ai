"""
Mandi Price Service — Fetches live market prices from Data.gov.in
and provides intelligent fallback pricing.
"""
import requests
import random


class MandiService:
    """Fetch live commodity prices from Indian government Mandi APIs."""

    BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

    # Realistic fallback prices (₹/quintal) based on 2024–2025 MSP & market data
    FALLBACK_PRICES = {
        "rice": {"price": 2320, "mandi": "Karnal", "state": "Haryana", "trend": "stable"},
        "wheat": {"price": 2275, "mandi": "Indore", "state": "Madhya Pradesh", "trend": "rising"},
        "maize": {"price": 2090, "mandi": "Davangere", "state": "Karnataka", "trend": "stable"},
        "cotton": {"price": 7020, "mandi": "Rajkot", "state": "Gujarat", "trend": "falling"},
        "sugarcane": {"price": 315, "mandi": "Muzaffarnagar", "state": "Uttar Pradesh", "trend": "stable"},
        "jute": {"price": 5050, "mandi": "Kolkata", "state": "West Bengal", "trend": "rising"},
        "coffee": {"price": 9800, "mandi": "Chikmagalur", "state": "Karnataka", "trend": "rising"},
        "coconut": {"price": 3200, "mandi": "Kozhikode", "state": "Kerala", "trend": "stable"},
        "apple": {"price": 5500, "mandi": "Shimla", "state": "Himachal Pradesh", "trend": "seasonal"},
        "mango": {"price": 4200, "mandi": "Ratnagiri", "state": "Maharashtra", "trend": "seasonal"},
        "banana": {"price": 1800, "mandi": "Jalgaon", "state": "Maharashtra", "trend": "stable"},
        "grapes": {"price": 6500, "mandi": "Nasik", "state": "Maharashtra", "trend": "seasonal"},
        "watermelon": {"price": 1200, "mandi": "Medak", "state": "Telangana", "trend": "seasonal"},
        "muskmelon": {"price": 1800, "mandi": "Kolar", "state": "Karnataka", "trend": "seasonal"},
        "orange": {"price": 3500, "mandi": "Nagpur", "state": "Maharashtra", "trend": "seasonal"},
        "papaya": {"price": 1500, "mandi": "Coimbatore", "state": "Tamil Nadu", "trend": "stable"},
        "pomegranate": {"price": 8500, "mandi": "Solapur", "state": "Maharashtra", "trend": "rising"},
        "lentil": {"price": 6200, "mandi": "Indore", "state": "Madhya Pradesh", "trend": "stable"},
        "blackgram": {"price": 6950, "mandi": "Guntur", "state": "Andhra Pradesh", "trend": "rising"},
        "mungbean": {"price": 8558, "mandi": "Bikaner", "state": "Rajasthan", "trend": "rising"},
        "mothbeans": {"price": 5725, "mandi": "Jodhpur", "state": "Rajasthan", "trend": "stable"},
        "pigeonpeas": {"price": 7000, "mandi": "Gulbarga", "state": "Karnataka", "trend": "rising"},
        "kidneybeans": {"price": 9200, "mandi": "Srinagar", "state": "Jammu & Kashmir", "trend": "stable"},
        "chickpea": {"price": 5440, "mandi": "Jaipur", "state": "Rajasthan", "trend": "rising"},
        "groundnut": {"price": 5550, "mandi": "Junagadh", "state": "Gujarat", "trend": "stable"},
        "soybean": {"price": 4600, "mandi": "Indore", "state": "Madhya Pradesh", "trend": "stable"},
        "mustard": {"price": 5650, "mandi": "Alwar", "state": "Rajasthan", "trend": "rising"},
        "sesame": {"price": 7800, "mandi": "Rajkot", "state": "Gujarat", "trend": "rising"},
        "turmeric": {"price": 14500, "mandi": "Nizamabad", "state": "Telangana", "trend": "rising"},
        "ginger": {"price": 4200, "mandi": "Cochin", "state": "Kerala", "trend": "stable"},
        "chilli": {"price": 12500, "mandi": "Guntur", "state": "Andhra Pradesh", "trend": "rising"},
        "black pepper": {"price": 55000, "mandi": "Kochi", "state": "Kerala", "trend": "rising"},
        "cardamom": {"price": 120000, "mandi": "Bodinayakanur", "state": "Tamil Nadu", "trend": "rising"},
        "coriander": {"price": 7200, "mandi": "Kota", "state": "Rajasthan", "trend": "stable"},
        "millets": {"price": 2500, "mandi": "Bellary", "state": "Karnataka", "trend": "rising"},
        "sorghum": {"price": 3180, "mandi": "Solapur", "state": "Maharashtra", "trend": "stable"},
        "barley": {"price": 1850, "mandi": "Jaipur", "state": "Rajasthan", "trend": "stable"},
        "tobacco": {"price": 14500, "mandi": "Guntur", "state": "Andhra Pradesh", "trend": "stable"},
        "cowpea": {"price": 6800, "mandi": "Jodhpur", "state": "Rajasthan", "trend": "rising"},
        "pigeon pea": {"price": 7000, "mandi": "Gulbarga", "state": "Karnataka", "trend": "rising"},
        "pearl millet": {"price": 2500, "mandi": "Jodhpur", "state": "Rajasthan", "trend": "stable"},
    }

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_prices(self, crops: list[str]) -> dict:
        """
        Fetch live Mandi prices for a list of crops.

        Returns: {crop_name: {price, mandi, state, trend, volatility, supply_level}}
        """
        results = {}
        for crop in crops:
            crop_lower = crop.lower().strip()
            # Try live API first
            live = self._fetch_live(crop_lower)
            if live:
                results[crop_lower] = live
            else:
                results[crop_lower] = self._get_fallback(crop_lower)
        return results

    def _fetch_live(self, crop: str) -> dict | None:
        """Attempt to fetch live price from Data.gov.in API."""
        if not self.api_key or self.api_key == "your_datagov_api_key_here":
            return None

        try:
            response = requests.get(self.BASE_URL, params={
                "api-key": self.api_key,
                "format": "json",
                "limit": 5,
                "filters[commodity]": crop.title(),
            }, timeout=10)

            if response.status_code == 200:
                data = response.json()
                records = data.get("records", [])
                if records:
                    record = records[0]
                    price = float(record.get("modal_price", 0))
                    return {
                        "price": price,
                        "mandi": record.get("market", "Unknown"),
                        "state": record.get("state", "Unknown"),
                        "trend": self._infer_trend(records),
                        "volatility": round(random.uniform(0.05, 0.35), 2),
                        "supply_level": random.choice(["low", "medium", "high", "glut"]),
                        "live": True,
                    }
        except requests.RequestException as e:
            print(f"[MandiService] Error fetching {crop}: {e}")

        return None

    def _get_fallback(self, crop: str) -> dict:
        """Return intelligent fallback pricing with simulated variance."""
        base = self.FALLBACK_PRICES.get(crop, {
            "price": 3000, "mandi": "Local Mandi", "state": "India", "trend": "stable"
        })

        # Add realistic variance ±8%
        variance = random.uniform(-0.08, 0.08)
        price = round(base["price"] * (1 + variance))

        return {
            "price": price,
            "mandi": base["mandi"],
            "state": base["state"],
            "trend": base["trend"],
            "volatility": round(random.uniform(0.05, 0.30), 2),
            "supply_level": random.choice(["low", "medium", "high"]),
            "live": False,
        }

    def _infer_trend(self, records: list) -> str:
        """Infer price trend from multiple records."""
        if len(records) < 2:
            return "stable"
        try:
            prices = [float(r.get("modal_price", 0)) for r in records[:5]]
            avg_recent = sum(prices[:2]) / 2
            avg_older = sum(prices[2:]) / max(len(prices[2:]), 1)
            if avg_recent > avg_older * 1.05:
                return "rising"
            elif avg_recent < avg_older * 0.95:
                return "falling"
            return "stable"
        except (ValueError, ZeroDivisionError):
            return "stable"
