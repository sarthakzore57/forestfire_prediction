from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.config import settings
from app.services.rule_engine import risk_category, score_from_rules


@dataclass
class PredictionResult:
    score: float
    category: str
    model_used: str
    region_supported: bool
    warning: str | None = None


class FirePredictor:
    def __init__(self, model_path: Path, metadata_path: Path) -> None:
        self.model = None
        self.metadata: dict[str, Any] = {}
        self.model_available = False

        if model_path.exists():
            self.model = joblib.load(model_path)
            self.model_available = True

        if metadata_path.exists():
            with metadata_path.open("r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    def _in_bounds(self, latitude: float, longitude: float, country_code: str) -> bool:
        lat_min = self.metadata.get("lat_min")
        lat_max = self.metadata.get("lat_max")
        lon_min = self.metadata.get("lon_min")
        lon_max = self.metadata.get("lon_max")

        in_box = True
        if None not in (lat_min, lat_max, lon_min, lon_max):
            in_box = lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max

        if settings.supported_countries:
            return in_box and country_code.upper() in settings.supported_countries
        return in_box

    def _build_features(
        self,
        *,
        weather: dict[str, float | str],
        latitude: float,
        longitude: float,
    ) -> pd.DataFrame:
        now = datetime.utcnow()
        month = now.month
        day_of_year = now.timetuple().tm_yday
        payload = {
            "temperature_c": float(weather["temperature_c"]),
            "humidity_pct": float(weather["humidity_pct"]),
            "wind_speed_mps": float(weather["wind_speed_mps"]),
            "wind_direction_deg": float(weather["wind_direction_deg"]),
            "rainfall_mm": float(weather["rainfall_mm"]),
            "latitude": float(latitude),
            "longitude": float(longitude),
            "month": float(month),
            "day_of_year": float(day_of_year),
        }

        columns = self.metadata.get("feature_columns")
        if isinstance(columns, list) and columns:
            return pd.DataFrame([payload], columns=columns)
        return pd.DataFrame([payload])

    def predict(
        self,
        *,
        weather: dict[str, float | str],
        latitude: float,
        longitude: float,
        country_code: str,
    ) -> PredictionResult:
        rule_score, rule_category = score_from_rules(
            temperature_c=float(weather["temperature_c"]),
            humidity_pct=float(weather["humidity_pct"]),
            wind_speed_mps=float(weather["wind_speed_mps"]),
            rainfall_mm=float(weather["rainfall_mm"]),
        )

        region_supported = self._in_bounds(latitude, longitude, country_code)
        can_use_ml = self.model_available and (region_supported or not settings.strict_region_check)

        if can_use_ml:
            features = self._build_features(weather=weather, latitude=latitude, longitude=longitude)
            if hasattr(self.model, "predict_proba"):
                score = float(self.model.predict_proba(features)[0][1])
            else:
                score = float(self.model.predict(features)[0])
            score = max(0.0, min(1.0, score))

            warning = None
            if not region_supported:
                warning = (
                    f"Location is outside ML training region ({settings.prediction_region_name}). "
                    "Using ML inference with relaxed region check."
                )
            return PredictionResult(
                score=score,
                category=risk_category(score),
                model_used="ml-random-forest",
                region_supported=region_supported,
                warning=warning,
            )

        warning = None
        if not region_supported:
            warning = (
                f"Location is outside ML training region ({settings.prediction_region_name}). "
                "Using rule-based fallback."
            )

        if settings.strict_region_check and not region_supported:
            return PredictionResult(
                score=rule_score,
                category=rule_category,
                model_used="rule-based",
                region_supported=False,
                warning=warning,
            )

        if not self.model_available:
            warning = "ML model artifact not found. Using rule-based fallback."

        return PredictionResult(
            score=rule_score,
            category=rule_category,
            model_used="rule-based",
            region_supported=region_supported,
            warning=warning,
        )


predictor = FirePredictor(settings.model_path, settings.model_metadata_path)
