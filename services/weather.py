"""
Weather Service — Fetches LIVE atmospheric data from OpenWeather API.
NO simulated/hardcoded data. Requires a valid API key.
"""
import requests


class WeatherService:
    """Fetch current weather data from OpenWeather API — real data only."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str):
        self.api_key = api_key
        if not api_key or api_key.startswith("your_"):
            print("[WeatherService] WARNING: No valid OpenWeather API key configured!")

    def fetch(self, lat: float, lon: float) -> dict | None:
        """
        Fetch current weather for given coordinates from OpenWeather API.
        Returns None with error info if the API call fails.
        """
        if not self.api_key or self.api_key.startswith("your_"):
            return {"error": "OpenWeather API key not configured. Add it to .env file."}

        try:
            response = requests.get(self.BASE_URL, params={
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
            }, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # Extract rainfall (from rain.1h or rain.3h if available)
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
                    "feels_like": round(data["main"]["feels_like"], 1),
                    "city_name": data.get("name", "Unknown"),
                    "source": "OpenWeather API (Live)",
                }

            elif response.status_code == 401:
                print(f"[WeatherService] Invalid API key — status 401")
                return {"error": "Invalid OpenWeather API key. Please check your .env file."}
            else:
                print(f"[WeatherService] API returned status {response.status_code}")
                return {"error": f"OpenWeather API error (HTTP {response.status_code})"}

        except requests.Timeout:
            print("[WeatherService] Request timed out")
            return {"error": "OpenWeather API request timed out. Try again."}
        except requests.ConnectionError:
            print("[WeatherService] Connection error")
            return {"error": "Cannot connect to OpenWeather API. Check your internet."}
        except requests.RequestException as e:
            print(f"[WeatherService] Request error: {e}")
            return {"error": f"Weather service error: {str(e)}"}
