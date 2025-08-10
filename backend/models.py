# backend/models.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint, Index, text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from silhouet_config import PERSONALITY_KEYS # Import from shared config
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_key = Column(String, unique=True, index=True)
    role = Column(String(50), default='user', nullable=False, index=True) # Added 'role'

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
    for key in PERSONALITY_KEYS:
        locals()[f"avg_{key}_score"] = Column(Float, default=0.5, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    advertiser_profile = relationship("AdvertiserProfile", back_populates="user", uselist=False)

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

class AdvertiserProfile(Base):
    __tablename__ = "advertiser_profiles"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.user_id'), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="advertiser_profile")

class AggregatedGeoScore(Base):
    __tablename__ = "aggregated_geo_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    geo_level = Column(String(50), nullable=False)
    geo_identifier = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False) # Renamed for history
    total_entities_contributing = Column(Integer, default=0, nullable=False)

    for key in PERSONALITY_KEYS:
        locals()[f"avg_{key}_score"] = Column(Float, default=0.5, nullable=False)

    __table_args__ = (
        UniqueConstraint('geo_level', 'geo_identifier', 'created_at', name='unique_geo_level_timestamp'),
        Index('idx_agg_geo_level_identifier_time', 'geo_level', 'geo_identifier', 'created_at'),
    )

class Post(Base):
    __tablename__ = "posts"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(PG_UUID(as_uuid=True), index=True)
    raw_text = Column(String, nullable=False)
    category = Column(String, nullable=True)
    sentiment_scores_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    advertiser_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True, index=True)
    
    campaign_type = Column(String(50), nullable=False, index=True) # 'ad' or 'insight'
    name = Column(String(255), nullable=False)
    status = Column(String(50), default='draft', nullable=False, index=True) # 'draft', 'active', 'paused', 'archived'
    
    # Content can be a simple text for insights or a JSON object for ads
    content = Column(JSONB, nullable=False)
    
    # Targeting criteria stored as a flexible JSON object
    targeting_criteria = Column(JSONB, nullable=False)
    
    # Budget and scheduling for ads
    budget = Column(Float, nullable=True)
    start_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Tracking metrics
    impressions_count = Column(Integer, default=0)
    clicks_count = Column(Integer, default=0) # Optional, for future use
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
