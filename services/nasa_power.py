"""
NASA POWER Service — Fetches historical climate data from NASA's
Prediction Of Worldwide Energy Resources (POWER) API.
FREE — No API key required.
Provides historical averages for temperature, precipitation, humidity
to supplement live weather data.
"""
import requests
from datetime import datetime, timedelta


class NasaPowerService:
    """Fetch historical climate data from NASA POWER API (no key required)."""

    BASE_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"

    # Parameters we care about
    PARAMETERS = [
        "T2M",          # Temperature at 2 Meters (°C)
        "T2M_MAX",      # Maximum Temperature at 2 Meters (°C)
        "T2M_MIN",      # Minimum Temperature at 2 Meters (°C)
        "PRECTOTCORR",  # Precipitation Corrected (mm/day)
        "RH2M",         # Relative Humidity at 2 Meters (%)
        "WS2M",         # Wind Speed at 2 Meters (m/s)
        "ALLSKY_SFC_SW_DWN",  # All Sky Surface Shortwave Downward Irradiance (kW-hr/m²/day)
    ]

    def __init__(self):
        pass

    def fetch_historical(self, lat: float, lon: float, years_back: int = 3) -> dict | None:
        """
        Fetch historical monthly climate averages for a location.
        Uses the last N years of data from NASA POWER.

        Returns: {
            "avg_temperature": float,
            "avg_max_temperature": float,
            "avg_min_temperature": float,
            "avg_precipitation": float (mm/day),
            "annual_rainfall_estimate": float (mm/year),
            "avg_humidity": float,
            "avg_wind_speed": float,
            "avg_solar_radiation": float,
            "monthly_data": {...},
            "source": "NASA POWER API"
        } or None
        """
        end_year = datetime.now().year - 1  # Most recent complete year
        start_year = end_year - years_back + 1

        try:
            response = requests.get(self.BASE_URL, params={
                "parameters": ",".join(self.PARAMETERS),
                "community": "AG",  # Agroclimatology community
                "longitude": round(lon, 4),
                "latitude": round(lat, 4),
                "start": start_year,
                "end": end_year,
                "format": "JSON",
            }, timeout=30)

            if response.status_code != 200:
                print(f"[NasaPower] API returned status {response.status_code}")
                return {"error": f"NASA POWER API error (HTTP {response.status_code})"}

            data = response.json()

            if "properties" not in data or "parameter" not in data["properties"]:
                return {"error": "Invalid response from NASA POWER API"}

            params = data["properties"]["parameter"]

            # Calculate averages across all months
            avg_temp = self._average_parameter(params.get("T2M", {}))
            avg_max_temp = self._average_parameter(params.get("T2M_MAX", {}))
            avg_min_temp = self._average_parameter(params.get("T2M_MIN", {}))
            avg_precip = self._average_parameter(params.get("PRECTOTCORR", {}))
            avg_humidity = self._average_parameter(params.get("RH2M", {}))
            avg_wind = self._average_parameter(params.get("WS2M", {}))
            avg_solar = self._average_parameter(params.get("ALLSKY_SFC_SW_DWN", {}))

            # Build monthly breakdown for the most recent year
            monthly_data = self._extract_monthly(params, end_year)

            return {
                "avg_temperature": round(avg_temp, 1),
                "avg_max_temperature": round(avg_max_temp, 1),
                "avg_min_temperature": round(avg_min_temp, 1),
                "avg_precipitation_daily": round(avg_precip, 2),
                "annual_rainfall_estimate": round(avg_precip * 365, 1),
                "avg_humidity": round(avg_humidity, 1),
                "avg_wind_speed": round(avg_wind, 1),
                "avg_solar_radiation": round(avg_solar, 2),
                "monthly_data": monthly_data,
                "data_period": f"{start_year}-{end_year}",
                "source": "NASA POWER API",
            }

        except requests.Timeout:
            print("[NasaPower] Request timed out")
            return {"error": "NASA POWER API request timed out."}
        except requests.ConnectionError:
            print("[NasaPower] Connection error")
            return {"error": "Cannot connect to NASA POWER API. Check internet."}
        except requests.RequestException as e:
            print(f"[NasaPower] Error: {e}")
            return {"error": f"NASA POWER error: {str(e)}"}
        except (KeyError, ValueError) as e:
            print(f"[NasaPower] Data parsing error: {e}")
            return {"error": f"Error parsing NASA POWER data: {str(e)}"}

    def _average_parameter(self, monthly_dict: dict) -> float:
        """Calculate average of monthly values, excluding -999 (missing data)."""
        values = [v for v in monthly_dict.values() if isinstance(v, (int, float)) and v > -900]
        return sum(values) / len(values) if values else 0.0

    def _extract_monthly(self, params: dict, year: int) -> dict:
        """Extract monthly data for a specific year."""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        result = {}
        for i, month_name in enumerate(months, 1):
            key = f"{year}{i:02d}"
            temp = params.get("T2M", {}).get(key, None)
            precip = params.get("PRECTOTCORR", {}).get(key, None)
            humidity = params.get("RH2M", {}).get(key, None)

            if temp is not None and temp > -900:
                result[month_name] = {
                    "temperature": round(temp, 1),
                    "precipitation": round(precip, 2) if precip and precip > -900 else None,
                    "humidity": round(humidity, 1) if humidity and humidity > -900 else None,
                }
        return result
