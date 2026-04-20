from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np


def main() -> None:
    artifacts = Path(__file__).resolve().parent / "artifacts"
    model_path = artifacts / "fire_risk_model.joblib"

    if not model_path.exists():
        raise FileNotFoundError("Model not found. Run train_model.py first.")

    model = joblib.load(model_path)

    sample_features = np.array(
        [
            [
                34.5,  # temperature_c
                22.0,  # humidity_pct
                7.1,   # wind_speed_mps
                210.0, # wind_direction_deg
                0.0,   # rainfall_mm
                36.77, # latitude
                -119.42, # longitude
                8,     # month
                220,   # day_of_year
            ]
        ],
        dtype=float,
    )

    prob = float(model.predict_proba(sample_features)[0][1])
    print(f"Predicted fire risk probability: {prob:.4f}")


if __name__ == "__main__":
    main()
