# backend/models.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint, Index, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from silhouet_config import PERSONALITY_KEYS # Import from shared config
from pydantic import BaseModel

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_key = Column(String, unique=True, index=True)

    # Demographic Data
    age = Column(Integer)
    sex = Column(String(50))
    gender = Column(String(50))
    religion = Column(String(100))
    ethnicity = Column(String(100))

    # Geographical Data (supplied by user during registration)
    pincode = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    nationality = Column(String(100), nullable=False)

    # User's cumulative aggregate scores (private to the user)
    total_posts_count = Column(Integer, default=0, nullable=False)

    # Dynamically add Columns for each personality key's average score
    # Using a loop to define these columns based on PERSONALITY_KEYS
    # This simplifies adding/removing keys later.
    # Ensure default value is 0.5 as per specification.
    for key in PERSONALITY_KEYS:
        locals()[f"avg_{key}_score"] = Column(Float, default=0.5, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Add indexes for geographical and demographic lookups
    __table_args__ = (
        Index('idx_users_pincode', 'pincode'),
        Index('idx_users_city', 'city'),
        Index('idx_users_district', 'district'),
        Index('idx_users_state', 'state'),
        Index('idx_users_country', 'country'),
        Index('idx_users_age', 'age'),
        Index('idx_users_sex', 'sex'),
        Index('idx_users_gender', 'gender'),
        Index('idx_users_religion', 'religion'),
        Index('idx_users_ethnicity', 'ethnicity'),
        Index('idx_users_nationality', 'nationality'),
    )

class AggregatedGeoScore(Base):
    __tablename__ = "aggregated_geo_scores"

    id = Column(Integer, primary_key=True, autoincrement=True) # SERIAL PRIMARY KEY
    geo_level = Column(String(50), nullable=False)       # 'pincode', 'city', etc.
    geo_identifier = Column(String(200), nullable=False) # e.g., '500081', 'Hyderabad'
    last_updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    # total_entities_contributing: total *users* for pincode, total *pincodes* for city, etc.
    total_entities_contributing = Column(Integer, default=0, nullable=False)

    # Dynamically add Columns for each personality key's average score
    for key in PERSONALITY_KEYS:
        locals()[f"avg_{key}_score"] = Column(Float, default=0.5, nullable=False)

    # Unique constraint for ensuring only one entry per geo_level and identifier
    __table_args__ = (
        UniqueConstraint('geo_level', 'geo_identifier', name='unique_geo_level_identifier'),
        Index('idx_agg_geo_level_identifier', 'geo_level', 'geo_identifier'),
    )

class Post(Base):
    __tablename__ = "posts"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(PG_UUID(as_uuid=True), index=True)
    raw_text = Column(String, nullable=False)
    # <<< ADD THESE NEW COLUMNS
    category = Column(String, nullable=True) # Optional in Pydantic means nullable in DB
    sentiment_scores_json = Column(JSONB, nullable=True) # To store the dictionary of scores
   # If JSONB doesn't work out of the box, you can use TEXT and store json.dumps()
   # sentiment_scores_json = Column(TEXT, nullable=True) 
   # >>>
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# =====================
# Advertiser & Campaign Models
# =====================

class Advertiser(Base):
    __tablename__ = "advertisers"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    campaigns = relationship("Campaign", back_populates="advertiser", cascade="all, delete-orphan")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    advertiser_id = Column(PG_UUID(as_uuid=True), ForeignKey('advertisers.id'), nullable=False)
    filter_definition = Column(JSONB, nullable=False)  # e.g., {"anxiety_score_gt": 0.7, "geo": "city:London"}
    duration_days = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=False)  # deliveries per user
    status = Column(String(50), default="pending", nullable=False)  # pending, active, completed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    advertiser = relationship("Advertiser", back_populates="campaigns")
    ads = relationship("AdCreative", back_populates="campaign", cascade="all, delete-orphan")


class AdCreative(Base):
    __tablename__ = "ads"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(PG_UUID(as_uuid=True), ForeignKey('campaigns.id'), nullable=False)
    media_url = Column(String, nullable=False)
    text = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    campaign = relationship("Campaign", back_populates="ads")

#===============
#Insights models
#===============

class Insight(Base):
    __tablename__ = "insights"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
