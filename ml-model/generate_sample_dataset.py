from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate_dataset(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Global bounds for training coverage.
    latitude = rng.uniform(-90.0, 90.0, rows)
    longitude = rng.uniform(-180.0, 180.0, rows)

    month = rng.integers(1, 13, rows)
    month_lengths = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], dtype=int)
    month_start = np.concatenate(([0], np.cumsum(month_lengths[:-1])))
    day_in_month = rng.integers(1, 32, rows)
    day_in_month = np.minimum(day_in_month, month_lengths[month - 1])
    day_of_year = month_start[month - 1] + day_in_month

    abs_lat = np.abs(latitude)
    hemisphere = np.where(latitude >= 0.0, 1.0, -1.0)
    seasonal_cycle = np.sin((day_of_year / 365.0) * 2.0 * np.pi - (np.pi / 2.0))

    # Climate proxies with latitude + seasonality.
    temperature_base = 32.0 - (0.52 * abs_lat)
    seasonal_temp = (7.0 + (abs_lat / 90.0) * 11.0) * seasonal_cycle * hemisphere
    temperature_c = (temperature_base + seasonal_temp + rng.normal(0.0, 4.5, rows)).clip(-35.0, 52.0)

    humidity_pct = (
        70.0
        - 0.85 * (temperature_c - 15.0)
        + rng.normal(0.0, 15.0, rows)
        + (20.0 * np.cos((abs_lat / 90.0) * np.pi))
    ).clip(5.0, 100.0)

    wind_speed_mps = rng.gamma(shape=2.3, scale=1.9, size=rows).clip(0, 30)
    wind_direction_deg = rng.uniform(0, 360, rows)

    rain_scale = (0.3 + (humidity_pct / 100.0) * 4.3 + (1.0 - abs_lat / 90.0) * 1.7).clip(0.2, 8.0)
    rainfall_mm = rng.exponential(scale=rain_scale, size=rows).clip(0, 150)

    # Synthetic risk generator: hot + dry + windy + low rain -> high risk.
    linear = (
        0.082 * (temperature_c - 15.0)
        + 0.034 * (100.0 - humidity_pct)
        + 0.108 * wind_speed_mps
        - 0.185 * np.log1p(rainfall_mm)
        + 0.080 * seasonal_cycle
        + rng.normal(0.0, 0.62, rows)
    )

    fire_probability = 1.0 / (1.0 + np.exp(-linear / 4.1))
    fire_occurrence = (fire_probability >= 0.56).astype(int)

    return pd.DataFrame(
        {
            "temperature_c": temperature_c,
            "humidity_pct": humidity_pct,
            "wind_speed_mps": wind_speed_mps,
            "wind_direction_deg": wind_direction_deg,
            "rainfall_mm": rainfall_mm,
            "latitude": latitude,
            "longitude": longitude,
            "month": month,
            "day_of_year": day_of_year,
            "fire_probability": fire_probability,
            "fire_occurrence": fire_occurrence,
            "country_code": "GLOBAL",
        }
    )


def main() -> None:
    project_root = Path(__file__).resolve().parent
    output = project_root / "data" / "wildfire_training_data.csv"
    output.parent.mkdir(parents=True, exist_ok=True)

    df = generate_dataset(rows=50000, seed=44)
    df.to_csv(output, index=False)
    print(f"Dataset written: {output}")
    print(df.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
