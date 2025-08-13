# backend/crud/campaigns.py
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from typing import List, Optional
import uuid

from models import Campaign, User
from schemas import CampaignCreate

def create_campaign(db: Session, campaign: CampaignCreate, advertiser_id: Optional[uuid.UUID] = None) -> Campaign:
    """
    Creates a new campaign (ad or insight).
    """
    db_campaign = Campaign(
        advertiser_id=advertiser_id,
        name=campaign.name,
        campaign_type=campaign.campaign_type,
        status=campaign.status,
        content=campaign.content,
        targeting_criteria=campaign.targeting_criteria,
        budget=campaign.budget,
        start_date=campaign.start_date,
        end_date=campaign.end_date
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

def get_campaign(db: Session, campaign_id: uuid.UUID) -> Optional[Campaign]:
    """
    Retrieves a single campaign by its ID.
    """
    return db.query(Campaign).filter(Campaign.id == campaign_id).first()

def get_campaigns(db: Session, skip: int = 0, limit: int = 100) -> List[Campaign]:
    """
    Retrieves a list of all campaigns.
    """
    return db.query(Campaign).offset(skip).limit(limit).all()

def get_active_campaigns(db: Session, campaign_type: str) -> List[Campaign]:
    """
    Retrieves all active campaigns of a specific type ('ad' or 'insight').
    """
    return db.query(Campaign).filter(
        Campaign.status == 'active',
        Campaign.campaign_type == campaign_type
    ).all()

def update_campaign_status(db: Session, campaign_id: uuid.UUID, status: str) -> Optional[Campaign]:
    """
    Updates the status of a campaign.
    """
    db_campaign = get_campaign(db, campaign_id)
    if db_campaign:
        db_campaign.status = status
        db.commit()
        db.refresh(db_campaign)
    return db_campaign

def increment_campaign_impressions(db: Session, campaign_id: uuid.UUID, count: int = 1):
    """
    Increments the impression count for a campaign.
    """
    db.execute(
        update(Campaign)
        .where(Campaign.id == campaign_id)
        .values(impressions_count=Campaign.impressions_count + count)
    )
    db.commit()

def delete_campaign(db: Session, campaign_id: uuid.UUID) -> bool:
    """
    Deletes a campaign from the database.
    """
    db_campaign = get_campaign(db, campaign_id)
    if db_campaign:
        db.delete(db_campaign)
        db.commit()
        return True
    return False
