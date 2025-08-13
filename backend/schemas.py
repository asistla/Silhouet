# backend/schemas.py
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    public_key: str = Field(..., description="User's public key, generated client-side.")
    age: Optional[int] = Field(None, description="User's age.")
    sex: Optional[str] = Field(None, description="User's biological sex (e.g., 'Male', 'Female', 'Non-binary', 'Prefer not to say').")
    gender: Optional[str] = Field(None, description="User's gender identity (e.g., 'Man', 'Woman', 'Non-binary', 'Prefer not to say').")
    religion: Optional[str] = Field(None, description="User's religious affiliation (e.g., 'Christianity', 'Islam', 'None', 'Prefer not to say').")
    ethnicity: Optional[str] = Field(None, description="User's ethnicity (e.g., 'Asian', 'Caucasian', 'African', 'Prefer not to say').")
    pincode: Optional[str] = Field(None, description="User's residential pincode.")
    city: Optional[str] = Field(None, description="User's city.")
    district: Optional[str] = Field(None, description="User's district.")
    state: Optional[str] = Field(None, description="User's state.")
    country: Optional[str] = Field(None, description="User's country.")
    nationality: Optional[str] = Field(None, description="User's nationality.")

class ChallengeRequest(BaseModel):
    public_key: str

class ChallengeResponse(BaseModel):
    challenge: str
    
class UserLogin(BaseModel):
    public_key: str
    signature: str

class UserCreateResponse(BaseModel):
    user_id: uuid.UUID
    public_key: str
    created_at: datetime

class UserResponse(BaseModel):
    user_id: uuid.UUID
    public_key: str
    created_at: datetime

    class Config:
        from_attributes = True # Allows Pydantic to read ORM models

class PostCreate(BaseModel):
    raw_text: str
    category: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    public_key: str

class PostResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    raw_text: str
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AdvertiserCreate(BaseModel):
    name: str
    contact_email: str


class AdvertiserResponse(BaseModel):
    id: uuid.UUID
    name: str
    contact_email: str
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    advertiser_id: uuid.UUID
    filter_definition: dict
    duration_days: int
    frequency: int


class CampaignResponse(BaseModel):
    id: uuid.UUID
    advertiser_id: uuid.UUID
    filter_definition: dict
    duration_days: int
    frequency: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdCreativeCreate(BaseModel):
    campaign_id: uuid.UUID
    media_url: str
    text: Optional[str] = None


class AdCreativeResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    media_url: str
    text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# =====================
# Advertiser & Campaign Schemas
# =====================

class AdvertiserCreate(BaseModel):
    name: str
    contact_email: str


class AdvertiserResponse(BaseModel):
    id: uuid.UUID
    name: str
    contact_email: str
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    advertiser_id: uuid.UUID
    filter_definition: dict
    duration_days: int
    frequency: int


class CampaignResponse(BaseModel):
    id: uuid.UUID
    advertiser_id: uuid.UUID
    filter_definition: dict
    duration_days: int
    frequency: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdCreativeCreate(BaseModel):
    campaign_id: uuid.UUID
    media_url: str
    text: Optional[str] = None


class AdCreativeResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    media_url: str
    text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

#================
#Insights schemas
#================

class InsightCreate(BaseModel):
    text: str


class InsightResponse(BaseModel):
    id: uuid.UUID
    text: str
    created_at: datetime

    class Config:
        from_attributes = True
