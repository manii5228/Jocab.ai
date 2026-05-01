"""
Geocoder Service — Converts city/district names to coordinates using Geopy.
"""
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


class GeocoderService:
    """Resolve location strings to latitude/longitude via Nominatim."""

    def __init__(self):
        self.geolocator = Nominatim(user_agent="agrismart-jacob-ai/2.0")

    def resolve(self, location_str: str) -> dict | None:
        """
        Resolve a location string (e.g. 'Bangalore', 'Dharwad District')
        to lat/lon coordinates.

        Returns: {"lat": float, "lon": float, "address": str} or None
        """
        try:
            # Append 'India' for better results with Indian locations
            query = f"{location_str}, India"
            location = self.geolocator.geocode(query, timeout=10)
            if location:
                return {
                    "lat": round(location.latitude, 4),
                    "lon": round(location.longitude, 4),
                    "address": location.address,
                }
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"[GeocoderService] Error: {e}")
            return None
