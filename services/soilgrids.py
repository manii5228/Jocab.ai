"""
SoilGrids Service — Fetches soil property data from ISRIC SoilGrids API.
FREE — No API key required.
Provides Nitrogen, pH, Organic Carbon, CEC, and soil texture
at any global coordinate.
"""
import requests


class SoilGridsService:
    """Fetch soil properties from ISRIC SoilGrids REST API (no key required)."""

    BASE_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

    # Properties we fetch from SoilGrids
    PROPERTIES = [
        "nitrogen",   # Total nitrogen (cg/kg)
        "phh2o",      # pH in H2O (pH * 10)
        "soc",        # Soil organic carbon (dg/kg)
        "cec",        # Cation Exchange Capacity (mmol(c)/kg)
        "clay",       # Clay content (g/kg)
        "sand",       # Sand content (g/kg)
        "silt",       # Silt content (g/kg)
    ]

    # Soil depth: 0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm, 100-200cm
    # We use 0-30cm (topsoil, most relevant for crops)
    TARGET_DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]

    def __init__(self):
        pass

    def fetch_soil_data(self, lat: float, lon: float) -> dict:
        """
        Fetch soil properties for given coordinates from SoilGrids.

        Returns: {
            "nitrogen_total": float (cg/kg from SoilGrids),
            "N": float (estimated available N in mg/kg for crop model),
            "P": float (estimated available P in mg/kg),
            "K": float (estimated available K in mg/kg),
            "ph": float,
            "organic_carbon": float (g/kg),
            "cec": float (cmol(+)/kg),
            "clay_pct": float,
            "sand_pct": float,
            "silt_pct": float,
            "soil_type": str (estimated),
            "source": "ISRIC SoilGrids v2.0",
        }
        """
        try:
            response = requests.get(self.BASE_URL, params={
                "lon": round(lon, 4),
                "lat": round(lat, 4),
                "property": self.PROPERTIES,
                "depth": self.TARGET_DEPTHS,
                "value": "mean",
            }, timeout=20)

            if response.status_code == 200:
                data = response.json()
                return self._parse_response(data)
            elif response.status_code == 400:
                return {"error": "Location outside SoilGrids coverage (likely ocean or polar region)."}
            elif response.status_code == 404:
                return {"error": "No soil data available for this location."}
            else:
                print(f"[SoilGrids] API returned status {response.status_code}")
                return {"error": f"SoilGrids API error (HTTP {response.status_code})"}

        except requests.Timeout:
            print("[SoilGrids] Request timed out")
            return {"error": "SoilGrids API request timed out. Try again."}
        except requests.ConnectionError:
            print("[SoilGrids] Connection error")
            return {"error": "Cannot connect to SoilGrids API. Check internet."}
        except requests.RequestException as e:
            print(f"[SoilGrids] Error: {e}")
            return {"error": f"SoilGrids error: {str(e)}"}

    def _parse_response(self, data: dict) -> dict:
        """Parse SoilGrids API response and extract averaged topsoil values."""
        layers = data.get("properties", {}).get("layers", [])

        raw = {}
        for layer in layers:
            prop_name = layer.get("name", "")
            depths = layer.get("depths", [])

            # Average across 0-30cm topsoil depths
            values = []
            for depth in depths:
                label = depth.get("label", "")
                if label in self.TARGET_DEPTHS:
                    mean_val = depth.get("values", {}).get("mean")
                    if mean_val is not None:
                        values.append(mean_val)

            if values:
                raw[prop_name] = sum(values) / len(values)

        # ─── Convert SoilGrids units to usable values ──────────────
        # Nitrogen: SoilGrids gives cg/kg (centigrams per kg)
        # 1 cg/kg = 10 mg/kg. But this is TOTAL N, not available N.
        # Available N is typically 1-3% of total N
        nitrogen_total_cg = raw.get("nitrogen", 0)
        nitrogen_total_mg = nitrogen_total_cg * 10  # cg/kg → mg/kg
        # Estimated available N = ~2% of total N (standard agronomic conversion)
        available_n = round(nitrogen_total_mg * 0.02, 1)
        # Clamp to reasonable range for crop model (20-200 mg/kg)
        available_n = max(20, min(200, available_n))

        # pH: SoilGrids gives pH * 10 (e.g., 65 = pH 6.5)
        ph_raw = raw.get("phh2o", 65)
        ph = round(ph_raw / 10, 1)

        # Soil Organic Carbon: SoilGrids gives dg/kg (decigrams per kg)
        # 1 dg/kg = 0.1 g/kg
        soc_dg = raw.get("soc", 0)
        soc_g = round(soc_dg * 0.1, 2)  # g/kg

        # CEC: SoilGrids gives mmol(c)/kg
        # 1 mmol(c)/kg = 0.1 cmol(+)/kg
        cec_mmol = raw.get("cec", 0)
        cec_cmol = round(cec_mmol * 0.1, 2)  # cmol(+)/kg

        # ─── Estimate Available P from Organic Carbon ──────────────
        # Olsen P estimation: ~0.5-2% of SOC correlates with available P
        # Using empirical: P_avail ≈ SOC(g/kg) × 3.5 + 10
        estimated_p = round(soc_g * 3.5 + 10, 1)
        estimated_p = max(20, min(100, estimated_p))

        # ─── Estimate Available K from CEC ─────────────────────────
        # K typically occupies 2-5% of CEC
        # K (mg/kg) ≈ CEC (cmol/kg) × 390 × 0.03 (3% of CEC as K)
        estimated_k = round(cec_cmol * 390 * 0.03, 1)
        estimated_k = max(20, min(100, estimated_k))

        # Soil texture
        clay_g = raw.get("clay", 0)
        sand_g = raw.get("sand", 0)
        silt_g = raw.get("silt", 0)
        total = clay_g + sand_g + silt_g if (clay_g + sand_g + silt_g) > 0 else 1000

        clay_pct = round(clay_g / total * 100, 1)
        sand_pct = round(sand_g / total * 100, 1)
        silt_pct = round(silt_g / total * 100, 1)

        soil_type = self._classify_soil(clay_pct, sand_pct, silt_pct)

        return {
            "nitrogen_total_mg_kg": round(nitrogen_total_mg, 1),
            "N": available_n,
            "P": estimated_p,
            "K": estimated_k,
            "ph": ph,
            "organic_carbon_g_kg": soc_g,
            "cec_cmol_kg": cec_cmol,
            "clay_pct": clay_pct,
            "sand_pct": sand_pct,
            "silt_pct": silt_pct,
            "soil_type": soil_type,
            "estimation_notes": {
                "N": f"Available N estimated at 2% of total N ({round(nitrogen_total_mg, 1)} mg/kg)",
                "P": f"Estimated from soil organic carbon ({soc_g} g/kg)",
                "K": f"Estimated from CEC ({cec_cmol} cmol(+)/kg)",
                "ph": "Direct measurement from SoilGrids (pH in H₂O)",
            },
            "source": "ISRIC SoilGrids v2.0 (0-30cm topsoil average)",
        }

    def _classify_soil(self, clay: float, sand: float, silt: float) -> str:
        """Classify soil type based on USDA texture triangle."""
        if clay >= 40:
            return "Clay"
        elif sand >= 85:
            return "Sand"
        elif silt >= 80:
            return "Silt"
        elif clay >= 27 and sand >= 20 and sand <= 45:
            return "Clay Loam"
        elif clay >= 20 and silt >= 28 and sand <= 52:
            return "Silty Clay Loam"
        elif sand >= 52 and clay >= 20:
            return "Sandy Clay Loam"
        elif clay <= 27 and silt >= 28 and silt <= 50:
            return "Loam"
        elif silt >= 50 and clay >= 12:
            return "Silty Loam"
        elif sand >= 70:
            return "Sandy Loam"
        elif silt >= 50:
            return "Silty Loam"
        else:
            return "Loam"
