# Forest Fire Prediction System

A complete end-to-end web app for predicting wildfire risk using real-time environmental data + machine learning.

## Features

- Search any location using OpenWeatherMap geocoding
- Select location from interactive Leaflet map
- Fetch live weather/environmental factors
- ML-based risk prediction (Random Forest, scikit-learn)
- Rule-based fallback when ML artifacts are unavailable
- Risk output as:
  - Probability score (0.0 to 1.0)
  - Category (Low / Medium / High)
- Color-coded risk indicators on UI
- Save search history
- Pin locations for ongoing monitoring
- Auto-refresh pinned locations every few minutes
- Browser notifications on high risk or significant change
- Responsive multi-page frontend:
  - Home
  - History
  - Saved Locations

## Project Structure

```text
forest fire/
├── frontend/
│   ├── index.html
│   ├── history.html
│   ├── saved.html
│   └── assets/
│       ├── css/styles.css
│       └── js/
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── schemas.py
│       ├── db/
│       └── services/
├── ml-model/
│   ├── generate_sample_dataset.py
│   ├── train_model.py
│   ├── predict_sample.py
│   ├── data/
│   └── artifacts/
├── api/
│   └── endpoints.md
└── database/
    └── README.md
```

## Tech Stack

- Frontend: HTML, CSS, Vanilla JS, Leaflet
- Backend: FastAPI + SQLAlchemy + SQLite
- ML: Python, scikit-learn (RandomForestClassifier)
- External API: OpenWeatherMap (Geocoding + Current Weather)

## Prerequisites

- Python 3.10+
- OpenWeatherMap API key (free tier)

## Setup

1. Create backend environment and install dependencies:

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
copy .env.example .env
```

Then edit `backend/.env` and set:

- `OPENWEATHER_API_KEY=your_real_key`

3. Generate dataset + train model:

```bash
cd ..\ml-model
python generate_sample_dataset.py
python train_model.py
```

4. Start backend (serves frontend too):

```bash
cd ..\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Open app in browser:

- `http://localhost:8000/`

## API Endpoints

Core endpoints requested:

- `POST /predict`
- `GET /weather`
- `GET /history`

Also available:

- `GET /geocode`
- `GET /api/config`
- `GET /api/saved-locations`
- `POST /api/saved-locations`
- `DELETE /api/saved-locations/{id}`

Note: `/api/*` aliases are also exposed for structured frontend usage.

## Request/Response Example

`POST /predict`

```json
{
  "location_name": "Fresno, US",
  "latitude": 36.7378,
  "longitude": -119.7871
}
```

Response:

```json
{
  "location_name": "Fresno, US",
  "latitude": 36.7378,
  "longitude": -119.7871,
  "weather": {
    "temperature_c": 33.2,
    "humidity_pct": 21,
    "wind_speed_mps": 4.6,
    "wind_direction_deg": 186,
    "rainfall_mm": 0,
    "weather_main": "Clear",
    "weather_description": "clear sky",
    "country_code": "US",
    "city_name": "Fresno"
  },
  "risk_score": 0.78,
  "risk_category": "High",
  "model_used": "ml-random-forest",
  "region_supported": true,
  "warning": null
}
```

## Global Prediction Mode

The default training dataset and metadata are global. By default, the backend uses ML predictions worldwide.

You can tune region behavior in `backend/.env`:

- `STRICT_REGION_CHECK=false`
- `PREDICTION_REGION_NAME=Global`
- `SUPPORTED_COUNTRIES=*` (or comma-separated ISO country codes to restrict)

## Beginner-Friendly Notes

- Start from `backend/app/main.py` to understand route flow.
- ML logic is centralized in `backend/app/services/predictor.py`.
- Rule fallback is in `backend/app/services/rule_engine.py`.
- Frontend API calls are in `frontend/assets/js/api.js`.
- Pin auto-refresh logic is in `frontend/assets/js/saved.js`.

## Deployment (Bonus)

- Backend can be deployed on Render or Railway.
- Set environment variables in cloud settings (`OPENWEATHER_API_KEY`, paths, DB URL).
- For production DB, switch from SQLite to PostgreSQL/MongoDB.

## Future Enhancements

- Integrate NDVI/satellite features
- Add soil moisture and solar radiation data sources
- Add auth and per-user saved locations
- Add email/SMS alert channels
- Add scheduled background workers for pinned monitoring
