"""
Weather Service — Fetches live atmospheric data from OpenWeather API.
"""
import requests


class WeatherService:
    """Fetch current weather data from OpenWeather API."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch(self, lat: float, lon: float) -> dict | None:
        """
        Fetch current weather for given coordinates.

        Returns: {
            "temperature": float (°C),
            "humidity": float (%),
            "rainfall": float (mm),
            "description": str,
            "wind_speed": float (m/s),
            "pressure": float (hPa),
        } or None
        """
        if not self.api_key or self.api_key == "your_openweather_api_key_here":
            # Return simulated data when no API key is configured
            return self._simulate(lat, lon)

        try:
            response = requests.get(self.BASE_URL, params={
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
            }, timeout=10)

            if response.status_code == 200:
                data = response.json()
                rainfall = 0.0
                if "rain" in data:
                    rainfall = data["rain"].get("1h", data["rain"].get("3h", 0.0))

                return {
                    "temperature": round(data["main"]["temp"], 1),
                    "humidity": round(data["main"]["humidity"], 1),
                    "rainfall": round(rainfall, 1),
                    "description": data["weather"][0]["description"],
                    "wind_speed": round(data["wind"]["speed"], 1),
                    "pressure": round(data["main"]["pressure"], 1),
                }
            else:
                print(f"[WeatherService] API returned {response.status_code}")
                return self._simulate(lat, lon)
        except requests.RequestException as e:
            print(f"[WeatherService] Error: {e}")
            return self._simulate(lat, lon)

    def _simulate(self, lat: float, lon: float) -> dict:
        """Generate realistic simulated weather data based on coordinates."""
        import random
        random.seed(int(lat * 100 + lon * 100))

        # Simulate based on Indian geography
        if lat > 25:  # Northern India
            temp = random.uniform(18, 35)
            rainfall = random.uniform(2, 40)
        elif lat > 15:  # Central India
            temp = random.uniform(22, 38)
            rainfall = random.uniform(5, 60)
        else:  # Southern India
            temp = random.uniform(24, 34)
            rainfall = random.uniform(8, 80)

        return {
            "temperature": round(temp, 1),
            "humidity": round(random.uniform(45, 85), 1),
            "rainfall": round(rainfall, 1),
            "description": random.choice([
                "scattered clouds", "light rain", "clear sky",
                "overcast clouds", "moderate rain", "mist",
            ]),
            "wind_speed": round(random.uniform(1, 8), 1),
            "pressure": round(random.uniform(1005, 1020), 1),
            "simulated": True,
        }
