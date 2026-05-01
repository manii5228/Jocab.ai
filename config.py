"""
AgriSmart Strategic Portfolio — Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "agrismart-dev-key-change-in-prod")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # API Keys
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    DATAGOV_API_KEY = os.getenv("DATAGOV_API_KEY", "")

    # Model paths
    MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
    MODEL_PATH = os.path.join(MODEL_DIR, "crop_model.joblib")
    LABEL_ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.joblib")

    # Crop knowledge base
    EXPORT_STARS = {
        "rice": True, "turmeric": True, "black pepper": True,
        "cardamom": True, "chilli": True, "ginger": True,
        "millets": True, "sesame": True, "groundnut": True,
        "cotton": True, "jute": True, "coffee": True, "tea": True,
    }

    SOIL_DEPLETING = {
        "maize": "cowpea", "cotton": "groundnut", "rice": "cowpea",
        "sugarcane": "soybean", "wheat": "chickpea", "tobacco": "pigeon pea",
        "potato": "mustard",
    }

    LOW_WATER_CROPS = {
        "millets", "sorghum", "chickpea", "pigeon pea", "mustard",
        "groundnut", "sesame", "barley", "pearl millet", "lentil",
    }
