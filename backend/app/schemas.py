from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GeocodeItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    state: str | None = None
    country: str
    latitude: float = Field(alias="lat")
    longitude: float = Field(alias="lon")


class WeatherData(BaseModel):
    temperature_c: float
    humidity_pct: float
    wind_speed_mps: float
    wind_direction_deg: float
    rainfall_mm: float
    weather_main: str
    weather_description: str
    country_code: str
    city_name: str


class PredictRequest(BaseModel):
    location_query: str | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    pinned_location_id: int | None = None

    @field_validator("location_query")
    @classmethod
    def normalize_query(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value or None


class PredictResponse(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    weather: WeatherData
    risk_score: float
    risk_category: str
    model_used: str
    region_supported: bool
    warning: str | None = None


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_name: str
    latitude: float
    longitude: float
    risk_score: float
    risk_category: str
    model_used: str
    created_at: datetime


class PinCreateRequest(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    country_code: str = ""
    notes: str = ""


class PinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_name: str
    latitude: float
    longitude: float
    country_code: str
    notes: str
    last_risk_score: float | None = None
    last_risk_category: str | None = None
    last_checked_at: datetime | None = None
    created_at: datetime


class MessageResponse(BaseModel):
    message: str
