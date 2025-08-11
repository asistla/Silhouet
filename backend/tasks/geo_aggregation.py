from celery import Celery
from database import SessionLocal
from aggregation.geo_scores import (
    aggregate_from_users, aggregate_from_lower,
    pincode_to_city, city_to_district, district_to_state, state_to_country,
    PINCODE_FREQ_HOURS, CITY_FREQ_HOURS, DISTRICT_FREQ_HOURS, STATE_FREQ_HOURS, COUNTRY_FREQ_HOURS
)

app = Celery("geo_aggregation")

@app.task
def aggregate_pincode_scores():
    with SessionLocal() as session:
        aggregate_from_users(session, "pincode", "pincode")

@app.task
def aggregate_city_scores():
    with SessionLocal() as session:
        aggregate_from_lower(session, "city", "pincode", pincode_to_city)

@app.task
def aggregate_district_scores():
    with SessionLocal() as session:
        aggregate_from_lower(session, "district", "city", city_to_district)

@app.task
def aggregate_state_scores():
    with SessionLocal() as session:
        aggregate_from_lower(session, "state", "district", district_to_state)

@app.task
def aggregate_country_scores():
    with SessionLocal() as session:
        aggregate_from_lower(session, "country", "state", state_to_country)
