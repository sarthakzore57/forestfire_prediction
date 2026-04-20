from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import PROJECT_ROOT, settings
from app.db import crud
from app.db.database import Base, engine, get_db
from app.schemas import (
    GeocodeItem,
    HistoryItem,
    MessageResponse,
    PinCreateRequest,
    PinResponse,
    PredictRequest,
    PredictResponse,
    WeatherData,
)
from app.services.openweather_service import OpenWeatherService
from app.services.predictor import predictor


app = FastAPI(title="Forest Fire Prediction System", version="1.0.0")
weather_service = OpenWeatherService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


frontend_dir = PROJECT_ROOT / "frontend"
assets_dir = frontend_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/", include_in_schema=False)
def serve_home() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/history-page", include_in_schema=False)
def serve_history() -> FileResponse:
    return FileResponse(frontend_dir / "history.html")


@app.get("/saved", include_in_schema=False)
def serve_saved() -> FileResponse:
    return FileResponse(frontend_dir / "saved.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/config")
def get_config() -> dict:
    return {
        "pin_refresh_minutes": settings.pin_refresh_minutes,
        "strict_region_check": settings.strict_region_check,
        "prediction_region_name": settings.prediction_region_name,
        "supported_countries": settings.supported_countries,
    }


@app.get("/api/geocode", response_model=list[GeocodeItem])
@app.get("/geocode", response_model=list[GeocodeItem], include_in_schema=False)
def geocode(query: str = Query(..., min_length=2, max_length=120)):
    candidates = weather_service.geocode(query=query, limit=5)
    mapped = []
    for item in candidates:
        mapped.append(
            {
                "name": item.get("name", "Unknown"),
                "state": item.get("state"),
                "country": item.get("country", ""),
                "lat": item.get("lat"),
                "lon": item.get("lon"),
            }
        )
    return mapped


@app.get("/api/weather", response_model=WeatherData)
@app.get("/weather", response_model=WeatherData, include_in_schema=False)
def weather(latitude: float, longitude: float):
    payload = weather_service.fetch_weather(latitude=latitude, longitude=longitude)
    return payload


@app.post("/api/predict", response_model=PredictResponse)
@app.post("/predict", response_model=PredictResponse, include_in_schema=False)
def predict(request: PredictRequest, db: Session = Depends(get_db)):
    latitude = request.latitude
    longitude = request.longitude
    location_name = request.location_name or request.location_query

    if (latitude is None or longitude is None) and request.location_query:
        candidates = weather_service.geocode(query=request.location_query, limit=1)
        if not candidates:
            raise HTTPException(status_code=404, detail="Location not found")
        first = candidates[0]
        latitude = float(first["lat"])
        longitude = float(first["lon"])
        location_name = f"{first.get('name', 'Unknown')}, {first.get('country', '')}".strip(", ")

    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=422,
            detail="latitude and longitude are required when location_query is missing",
        )

    weather_data = weather_service.fetch_weather(latitude=latitude, longitude=longitude)
    model_prediction = predictor.predict(
        weather=weather_data,
        latitude=latitude,
        longitude=longitude,
        country_code=weather_data.get("country_code", ""),
    )

    if not location_name:
        city_name = weather_data.get("city_name")
        country = weather_data.get("country_code")
        location_name = f"{city_name}, {country}" if city_name else f"{latitude:.3f}, {longitude:.3f}"

    crud.create_history_item(
        db,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
        risk_score=model_prediction.score,
        risk_category=model_prediction.category,
        model_used=model_prediction.model_used,
        weather_snapshot=weather_data,
    )

    if request.pinned_location_id is not None:
        crud.update_pinned_prediction(
            db,
            location_id=request.pinned_location_id,
            risk_score=model_prediction.score,
            risk_category=model_prediction.category,
        )

    return {
        "location_name": location_name,
        "latitude": latitude,
        "longitude": longitude,
        "weather": weather_data,
        "risk_score": model_prediction.score,
        "risk_category": model_prediction.category,
        "model_used": model_prediction.model_used,
        "region_supported": model_prediction.region_supported,
        "warning": model_prediction.warning,
    }


@app.get("/api/history", response_model=list[HistoryItem])
@app.get("/history", response_model=list[HistoryItem], include_in_schema=False)
def history(limit: int = 100, db: Session = Depends(get_db)):
    rows = crud.get_history(db, limit=limit)
    return rows


@app.get("/api/saved-locations", response_model=list[PinResponse])
def list_saved_locations(db: Session = Depends(get_db)):
    rows = crud.list_pinned_locations(db)
    return rows


@app.post("/api/saved-locations", response_model=PinResponse)
def create_saved_location(request: PinCreateRequest, db: Session = Depends(get_db)):
    row = crud.create_pinned_location(
        db,
        location_name=request.location_name,
        latitude=request.latitude,
        longitude=request.longitude,
        country_code=request.country_code,
        notes=request.notes,
    )
    return row


@app.delete("/api/saved-locations/{location_id}", response_model=MessageResponse)
def delete_saved_location(location_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_pinned_location(db, location_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pinned location not found")
    return {"message": "Pinned location deleted"}
