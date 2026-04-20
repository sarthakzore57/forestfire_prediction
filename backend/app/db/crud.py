from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db import models


def create_history_item(
    db: Session,
    *,
    location_name: str,
    latitude: float,
    longitude: float,
    risk_score: float,
    risk_category: str,
    model_used: str,
    weather_snapshot: dict,
) -> models.SearchHistory:
    row = models.SearchHistory(
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
        risk_score=risk_score,
        risk_category=risk_category,
        model_used=model_used,
        weather_snapshot=json.dumps(weather_snapshot),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_history(db: Session, limit: int = 100) -> list[models.SearchHistory]:
    return (
        db.query(models.SearchHistory)
        .order_by(desc(models.SearchHistory.created_at))
        .limit(limit)
        .all()
    )


def list_pinned_locations(db: Session) -> list[models.PinnedLocation]:
    return db.query(models.PinnedLocation).order_by(desc(models.PinnedLocation.created_at)).all()


def get_pinned_by_id(db: Session, location_id: int) -> models.PinnedLocation | None:
    return db.query(models.PinnedLocation).filter(models.PinnedLocation.id == location_id).first()


def create_pinned_location(
    db: Session,
    *,
    location_name: str,
    latitude: float,
    longitude: float,
    country_code: str,
    notes: str,
) -> models.PinnedLocation:
    row = models.PinnedLocation(
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
        country_code=country_code,
        notes=notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_pinned_location(db: Session, location_id: int) -> bool:
    row = get_pinned_by_id(db, location_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def update_pinned_prediction(
    db: Session,
    *,
    location_id: int,
    risk_score: float,
    risk_category: str,
) -> models.PinnedLocation | None:
    row = get_pinned_by_id(db, location_id)
    if not row:
        return None
    row.last_risk_score = risk_score
    row.last_risk_category = risk_category
    row.last_checked_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row
