from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split


FEATURE_COLUMNS = [
    "temperature_c",
    "humidity_pct",
    "wind_speed_mps",
    "wind_direction_deg",
    "rainfall_mm",
    "latitude",
    "longitude",
    "month",
    "day_of_year",
]
TARGET_COLUMN = "fire_occurrence"


def train(project_dir: Path) -> None:
    data_path = project_dir / "data" / "wildfire_training_data.csv"
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset missing at {data_path}. Run generate_sample_dataset.py first."
        )

    df = pd.read_csv(data_path)

    missing = [col for col in FEATURE_COLUMNS + [TARGET_COLUMN] if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=320,
        max_depth=16,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "roc_auc": float(roc_auc_score(y_test, prob)),
    }

    model_path = artifacts_dir / "fire_risk_model.joblib"
    joblib.dump(model, model_path)

    metadata = {
        "model_name": "RandomForestClassifier",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "feature_columns": FEATURE_COLUMNS,
        "lat_min": float(df["latitude"].min()),
        "lat_max": float(df["latitude"].max()),
        "lon_min": float(df["longitude"].min()),
        "lon_max": float(df["longitude"].max()),
        "supported_countries": ["*"],
        "prediction_region_name": "Global",
        "metrics": metrics,
        "sample_count": int(len(df)),
    }

    metadata_path = artifacts_dir / "model_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Model saved to: {model_path}")
    print(f"Metadata saved to: {metadata_path}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"ROC AUC: {metrics['roc_auc']:.4f}")


def main() -> None:
    train(project_dir=Path(__file__).resolve().parent)


if __name__ == "__main__":
    main()
