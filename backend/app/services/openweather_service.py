from __future__ import annotations

from typing import Any

import requests
from fastapi import HTTPException

from app.config import settings


class OpenWeatherService:
    def __init__(self) -> None:
        self.base_url = settings.openweather_base_url.rstrip("/")
        self.api_key = settings.openweather_api_key

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENWEATHER_API_KEY is missing. Add it in backend/.env",
            )

    def geocode(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        self._ensure_api_key()
        url = f"{self.base_url}/geo/1.0/direct"
        params = {"q": query, "limit": limit, "appid": self.api_key}
        response = requests.get(url, params=params, timeout=12)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Geocoding API failed with status {response.status_code}",
            )
        return response.json()

    def fetch_weather(self, latitude: float, longitude: float) -> dict[str, Any]:
        self._ensure_api_key()
        url = f"{self.base_url}/data/2.5/weather"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
        }
        response = requests.get(url, params=params, timeout=12)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Weather API failed with status {response.status_code}",
            )
        payload = response.json()

        rain = payload.get("rain", {}) or {}
        rainfall_mm = rain.get("1h", rain.get("3h", 0.0))

        weather_list = payload.get("weather", [{}])
        first_weather = weather_list[0] if weather_list else {}

        return {
            "temperature_c": float(payload.get("main", {}).get("temp", 0.0)),
            "humidity_pct": float(payload.get("main", {}).get("humidity", 0.0)),
            "wind_speed_mps": float(payload.get("wind", {}).get("speed", 0.0)),
            "wind_direction_deg": float(payload.get("wind", {}).get("deg", 0.0)),
            "rainfall_mm": float(rainfall_mm or 0.0),
            "weather_main": str(first_weather.get("main", "Unknown")),
            "weather_description": str(first_weather.get("description", "")),
            "country_code": str(payload.get("sys", {}).get("country", "")),
            "city_name": str(payload.get("name", "Unknown")),
        }
