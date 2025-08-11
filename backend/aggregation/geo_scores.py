import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from models import User, AggregatedGeoScore
from settings import PERSONALITY_KEYS
from database import SessionLocal

# Config
PINCODE_FREQ_HOURS = int(os.getenv("AGG_PINCODE_FREQ_HOURS", 2))
CITY_FREQ_HOURS = int(os.getenv("AGG_CITY_FREQ_HOURS", 4))
DISTRICT_FREQ_HOURS = int(os.getenv("AGG_DISTRICT_FREQ_HOURS", 6))
STATE_FREQ_HOURS = int(os.getenv("AGG_STATE_FREQ_HOURS", 24))
COUNTRY_FREQ_HOURS = int(os.getenv("AGG_COUNTRY_FREQ_HOURS", 24))
RETENTION_MULTIPLIER = int(os.getenv("AGG_RETENTION_MULTIPLIER", 2))


def cleanup_old_scores(session, level, hours):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    session.query(AggregatedGeoScore).filter(
        AggregatedGeoScore.geo_level == level,
        AggregatedGeoScore.created_at < cutoff
    ).delete(synchronize_session=False)


def aggregate_from_users(session, geo_level, geo_field):
    now = datetime.now(timezone.utc)
    for geo_id, in session.query(getattr(User, geo_field)).distinct():
        if not geo_id:
            continue
        users = session.query(User).filter(getattr(User, geo_field) == geo_id).all()
        if not users:
            continue
        data = {f"avg_{k}_score": sum(getattr(u, f"avg_{k}_score") for u in users) / len(users)
                for k in PERSONALITY_KEYS}
        session.add(AggregatedGeoScore(
            geo_level=geo_level,
            geo_identifier=geo_id,
            created_at=now,
            total_entities_contributing=len(users),
            **data
        ))
    cleanup_old_scores(session, geo_level, hours=globals()[f"{geo_level.upper()}_FREQ_HOURS"] * RETENTION_MULTIPLIER)
    session.commit()


def aggregate_from_lower(session, geo_level, lower_level, map_func):
    now = datetime.now(timezone.utc)
    latest_time = session.query(func.max(AggregatedGeoScore.created_at)).filter_by(geo_level=lower_level).scalar()
    if not latest_time:
        return
    mapping = map_func(session)
    for geo_id in set(mapping.values()):
        lowers = [lid for lid, gid in mapping.items() if gid == geo_id]
        lower_scores = session.query(AggregatedGeoScore).filter(
            AggregatedGeoScore.geo_level == lower_level,
            AggregatedGeoScore.geo_identifier.in_(lowers),
            AggregatedGeoScore.created_at == latest_time
        ).all()
        if not lower_scores:
            continue
        data = {f"avg_{k}_score": sum(getattr(s, f"avg_{k}_score") for s in lower_scores) / len(lower_scores)
                for k in PERSONALITY_KEYS}
        session.add(AggregatedGeoScore(
            geo_level=geo_level,
            geo_identifier=geo_id,
            created_at=now,
            total_entities_contributing=len(lower_scores),
            **data
        ))
    cleanup_old_scores(session, geo_level, hours=globals()[f"{geo_level.upper()}_FREQ_HOURS"] * RETENTION_MULTIPLIER)
    session.commit()


# Mapping helpers
def pincode_to_city(session):
    return {u.pincode: u.city for u in session.query(User.pincode, User.city).distinct() if u.pincode and u.city}

def city_to_district(session):
    return {u.city: u.district for u in session.query(User.city, User.district).distinct() if u.city and u.district}

def district_to_state(session):
    return {u.district: u.state for u in session.query(User.district, User.state).distinct() if u.district and u.state}

def state_to_country(session):
    return {u.state: u.country for u in session.query(User.state, User.country).distinct() if u.state and u.country}
