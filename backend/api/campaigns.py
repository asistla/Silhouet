# backend/api/campaigns.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from database import get_db
from schemas import CampaignCreate, CampaignResponse
from crud import campaigns as crud_campaigns
from models import User
from auth import RoleChecker

# Dependency to check for 'admin' or 'advertiser' roles
allow_campaign_management = RoleChecker(['admin', 'advertiser'])

router = APIRouter(
    prefix="/campaigns",
    tags=["campaigns"],
    dependencies=[Depends(allow_campaign_management)],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    campaign: CampaignCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_campaign_management)
):
    """
    Create a new ad or insight campaign.
    - **Advertisers** can create 'ad' campaigns.
    - **Admins** can create 'insight' or 'ad' campaigns.
    """
    if current_user.role == 'advertiser' and campaign.campaign_type != 'ad':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Advertisers can only create 'ad' campaigns."
        )
    
    advertiser_id = current_user.user_id if campaign.campaign_type == 'ad' else None
    created_campaign = crud_campaigns.create_campaign(db=db, campaign=campaign, advertiser_id=advertiser_id)
    return created_campaign

@router.get("/{campaign_id}", response_model=CampaignResponse)
def read_campaign(campaign_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a single campaign by its ID.
    """
    db_campaign = crud_campaigns.get_campaign(db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return db_campaign

@router.get("/", response_model=List[CampaignResponse])
def read_campaigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of all campaigns.
    """
    all_campaigns = crud_campaigns.get_campaigns(db, skip=skip, limit=limit)
    return all_campaigns

@router.patch("/{campaign_id}/status", response_model=CampaignResponse)
def update_campaign_status(
    campaign_id: uuid.UUID,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update the status of a campaign (e.g., 'active', 'paused', 'archived').
    """
    updated_campaign = crud_campaigns.update_campaign_status(db, campaign_id=campaign_id, status=status)
    if updated_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated_campaign
