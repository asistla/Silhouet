from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone

from .. import models, schemas
from ..dependencies import get_db

router = APIRouter()

# =========================
# Advertisers
# =========================
@router.post("/advertisers", response_model=schemas.AdvertiserResponse)
def create_advertiser(advertiser: schemas.AdvertiserCreate, db: Session = Depends(get_db)):
    db_adv = models.Advertiser(**advertiser.dict())
    db.add(db_adv)
    db.commit()
    db.refresh(db_adv)
    return db_adv


@router.get("/advertisers/{advertiser_id}", response_model=schemas.AdvertiserResponse)
def get_advertiser(advertiser_id: uuid.UUID, db: Session = Depends(get_db)):
    adv = db.query(models.Advertiser).filter(models.Advertiser.id == advertiser_id).first()
    if not adv:
        raise HTTPException(status_code=404, detail="Advertiser not found")
    return adv


# =========================
# Campaigns
# =========================
@router.post("/campaigns", response_model=schemas.CampaignResponse)
def create_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    db_campaign = models.Campaign(**campaign.dict())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


@router.get("/campaigns/{campaign_id}", response_model=schemas.CampaignResponse)
def get_campaign(campaign_id: uuid.UUID, db: Session = Depends(get_db)):
    camp = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return camp


# =========================
# Ad Creatives
# =========================
@router.post("/ads", response_model=schemas.AdCreativeResponse)
def create_ad_creative(ad: schemas.AdCreativeCreate, db: Session = Depends(get_db)):
    db_ad = models.AdCreative(**ad.dict())
    db.add(db_ad)
    db.commit()
    db.refresh(db_ad)
    return db_ad


@router.get("/ads/{ad_id}", response_model=schemas.AdCreativeResponse)
def get_ad_creative(ad_id: uuid.UUID, db: Session = Depends(get_db)):
    ad = db.query(models.AdCreative).filter(models.AdCreative.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    return ad


# =========================
# Insights
# =========================
@router.post("/insights", response_model=schemas.InsightResponse)
def create_insight(insight: schemas.InsightCreate, db: Session = Depends(get_db)):
    db_insight = models.Insight(**insight.dict())
    db.add(db_insight)
    db.commit()
    db.refresh(db_insight)
    return db_insight


@router.get("/insights/{insight_id}", response_model=schemas.InsightResponse)
def get_insight(insight_id: uuid.UUID, db: Session = Depends(get_db)):
    ins = db.query(models.Insight).filter(models.Insight.id == insight_id).first()
    if not ins:
        raise HTTPException(status_code=404, detail="Insight not found")
    return ins
