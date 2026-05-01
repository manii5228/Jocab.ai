# AgriSmart Strategic Portfolio v2.0

> **Explainable Intelligence** — Balancing biological suitability (ML), economic profitability (Live Mandi Prices), and long-term sustainability (Regenerative Agriculture).

Built by [Jacob.ai](https://github.com/manii5228) Research Lab.

---

## 🌾 Overview

AgriSmart is a precision agriculture platform that combines XGBoost ML inference with live market intelligence to generate **actionable crop recommendations** for Indian farmers and agricultural researchers.

### Core Features

- **Live Environmental Sensing** — OpenWeather API integration for real-time rainfall, temperature, humidity
- **Market Intelligence** — Live Mandi price cross-referencing with export-potential flagging
- **Trust-Based UI** — Actionable Badges (Export-Ready, Stable Price, Low Water)
- **Research Mode (XAI)** — SHAP/Feature Importance graphs for transparent decision-making
- **Regenerative Agriculture** — Automatic soil-depleting crop detection with companion legume pairing

---

## 🧠 The Strategic Algorithm

### Phase 1: Data Ingestion & Enrichment
1. User provides Location (City/District) and Soil N-P-K
2. Geopy resolves city name → Lat/Lon coordinates
3. OpenWeather API provides live Rainfall, Temperature, Humidity

### Phase 2: Biological Inference
4. XGBoost Classifier (22 crops, 7 features) generates Top-5 confidence scores

### Phase 3: Economic & Strategic Filtering
5. Live Mandi prices fetched from Data.gov.in
6. **Profit Index** = `Confidence × Live Price`
7. Export Stars identification + Regenerative pairing

### Phase 4: Output Rendering
8. Strategic Recommendation with Trust Badges
9. Research Mode: Feature Importance, SHAP, Market Equilibrium charts

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/manii5228/Jacob.ai.git
cd Jacob.ai

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env with your API keys

# Run the application
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🔑 API Keys (Optional)

| Service | Purpose | Get Key |
|---------|---------|---------|
| OpenWeather | Live weather data | [openweathermap.org/api](https://openweathermap.org/api) |
| Data.gov.in | Live Mandi prices | [data.gov.in](https://data.gov.in/) |

> **Note:** The app works without API keys using intelligent simulation.

---

## 📁 Project Structure

```
Jacob.ai/
├── app.py                  # Flask application
├── config.py               # Configuration & crop knowledge base
├── requirements.txt        # Python dependencies
├── services/
│   ├── geocoder.py         # Geopy location resolution
│   ├── weather.py          # OpenWeather API integration
│   ├── mandi.py            # Mandi price service
│   ├── predictor.py        # XGBoost crop predictor
│   └── strategy.py         # Strategy engine (Profit Index, Badges, Regen)
├── models/                 # Auto-generated XGBoost model artifacts
├── templates/
│   └── index.html          # Main SPA template
└── static/
    ├── css/
    │   ├── design-system.css   # Agro-Scientific Precision design tokens
    │   └── app.css             # Application styles
    └── js/
        └── app.js              # Frontend SPA logic + Chart.js
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask, Python 3.10+ |
| ML Engine | XGBoost, scikit-learn |
| Geocoding | Geopy (Nominatim) |
| Weather | OpenWeather API |
| Market Data | Data.gov.in API |
| Frontend | Vanilla HTML/CSS/JS |
| Charts | Chart.js 4.x |
| Design System | Custom (Agro-Scientific Precision) |
| Typography | Inter + Space Grotesk |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
