"""
AgriSmart Strategic Portfolio — Main Flask Application
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from config import Config
from services.weather import WeatherService
from services.geocoder import GeocoderService
from services.mandi import MandiService
from services.predictor import CropPredictor
from services.strategy import StrategyEngine
import traceback

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# ─── Service Initialization ────────────────────────────────────────
weather_service = WeatherService(Config.OPENWEATHER_API_KEY)
geocoder_service = GeocoderService()
mandi_service = MandiService(Config.DATAGOV_API_KEY)
predictor = CropPredictor(Config.MODEL_PATH, Config.LABEL_ENCODER_PATH)
strategy_engine = StrategyEngine(Config)


# ─── Page Routes ───────────────────────────────────────────────────
@app.route("/")
def index():
    """Serve the main SPA."""
    return render_template("index.html")


# ─── API Routes ────────────────────────────────────────────────────
@app.route("/api/geocode", methods=["POST"])
def geocode():
    """Resolve city/district name to lat/lon."""
    data = request.get_json()
    location = data.get("location", "")
    if not location:
        return jsonify({"error": "Location is required"}), 400

    result = geocoder_service.resolve(location)
    if result is None:
        return jsonify({"error": f"Could not resolve location: {location}"}), 404
    return jsonify(result)


@app.route("/api/weather", methods=["POST"])
def weather():
    """Fetch live weather data for coordinates."""
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400

    result = weather_service.fetch(lat, lon)
    if result is None:
        return jsonify({"error": "Weather service unavailable"}), 503
    return jsonify(result)


@app.route("/api/predict", methods=["POST"])
def predict():
    """Run the XGBoost crop prediction pipeline."""
    data = request.get_json()
    required = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        predictions = predictor.predict(data)
        return jsonify(predictions)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/strategy", methods=["POST"])
def strategy():
    """Full strategic pipeline: predict → enrich with mandi data → generate strategy."""
    data = request.get_json()

    try:
        # Phase 2: Biological Inference
        predictions = predictor.predict(data)

        # Phase 3: Economic & Strategic Filtering
        crop_names = [p["crop"] for p in predictions["top_crops"]]
        mandi_prices = mandi_service.fetch_prices(crop_names)
        result = strategy_engine.generate(predictions, mandi_prices, data)

        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/mandi", methods=["POST"])
def mandi_prices():
    """Fetch live Mandi prices for specific crops."""
    data = request.get_json()
    crops = data.get("crops", [])
    if not crops:
        return jsonify({"error": "crops list is required"}), 400

    prices = mandi_service.fetch_prices(crops)
    return jsonify(prices)


if __name__ == "__main__":
    app.run(debug=Config.DEBUG, port=5000)
