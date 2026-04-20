from __future__ import annotations


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def risk_category(score: float) -> str:
    if score < 0.35:
        return "Low"
    if score < 0.65:
        return "Medium"
    return "High"


def score_from_rules(
    *,
    temperature_c: float,
    humidity_pct: float,
    wind_speed_mps: float,
    rainfall_mm: float,
) -> tuple[float, str]:
    # Higher temperature and wind increase fire risk.
    temp_factor = clamp((temperature_c - 10.0) / 30.0)
    wind_factor = clamp(wind_speed_mps / 14.0)

    # Lower humidity and less rain increase fire risk.
    dryness_factor = clamp((100.0 - humidity_pct) / 100.0)
    rain_penalty = clamp(rainfall_mm / 8.0)

    score = (
        (0.4 * temp_factor)
        + (0.3 * dryness_factor)
        + (0.25 * wind_factor)
        - (0.25 * rain_penalty)
    )
    score = clamp(score)
    return score, risk_category(score)
