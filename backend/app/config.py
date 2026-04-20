from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
ENV_PATH = BACKEND_DIR / ".env"

load_dotenv(ENV_PATH)


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_path(env_key: str, default_relative: str) -> Path:
    raw = os.getenv(env_key, default_relative)
    path = Path(raw)
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()


class Settings:
    def __init__(self) -> None:
        self.openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")
        self.openweather_base_url: str = os.getenv(
            "OPENWEATHER_BASE_URL", "https://api.openweathermap.org"
        )

        database_url = os.getenv("DATABASE_URL", "sqlite:///../database/forest_fire.db")
        if database_url.startswith("sqlite:///") and ".." in database_url:
            # Resolve relative SQLite paths from backend directory.
            relative_part = database_url.replace("sqlite:///", "", 1)
            resolved_path = (BACKEND_DIR / relative_part).resolve()
            self.database_url = f"sqlite:///{resolved_path.as_posix()}"
        else:
            self.database_url = database_url

        self.model_path: Path = _resolve_path(
            "MODEL_PATH", "../ml-model/artifacts/fire_risk_model.joblib"
        )
        self.model_metadata_path: Path = _resolve_path(
            "MODEL_METADATA_PATH", "../ml-model/artifacts/model_metadata.json"
        )

        self.strict_region_check: bool = _parse_bool(
            os.getenv("STRICT_REGION_CHECK"), default=True
        )
        self.prediction_region_name: str = os.getenv(
            "PREDICTION_REGION_NAME", "Western United States"
        )

        countries = os.getenv("SUPPORTED_COUNTRIES", "*").strip()
        if not countries or countries.upper() in {"*", "ALL", "GLOBAL"}:
            self.supported_countries = []
        else:
            self.supported_countries = [c.strip().upper() for c in countries.split(",") if c.strip()]

        self.pin_refresh_minutes: int = int(os.getenv("PIN_REFRESH_MINUTES", "5"))


settings = Settings()
