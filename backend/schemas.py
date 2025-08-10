# backend/schemas.py
from pydantic import BaseModel, Field, Json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

# --- User Schemas ---

class UserCreate(BaseModel):
    public_key: str = Field(..., description="User's public key, generated client-side.")
    age: Optional[int] = Field(None, description="User's age.")
    sex: Optional[str] = Field(None, description="User's biological sex.")
    gender: Optional[str] = Field(None, description="User's gender identity.")
    religion: Optional[str] = Field(None, description="User's religious affiliation.")
    ethnicity: Optional[str] = Field(None, description="User's ethnicity.")
    pincode: Optional[str] = Field(None, description="User's residential pincode.")
    city: Optional[str] = Field(None, description="User's city.")
    district: Optional[str] = Field(None, description="User's district.")
    state: Optional[str] = Field(None, description="User's state.")
    country: Optional[str] = Field(None, description="User's country.")
    nationality: Optional[str] = Field(None, description="User's nationality.")

class UserCreateResponse(BaseModel):
    user_id: uuid.UUID
    public_key: str
    role: str
    created_at: datetime

class UserResponse(BaseModel):
    user_id: uuid.UUID
    public_key: str
    role: str
    created_at: datetime
    advertiser_profile: Optional['AdvertiserProfileResponse'] = None

    class Config:
        from_attributes = True

# --- Advertiser Schemas ---

class AdvertiserProfileCreate(BaseModel):
    company_name: str

class AdvertiserProfileResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class AdvertiserCreate(UserCreate):
    company_name: str

class AdvertiserCreateResponse(BaseModel):
    user: UserCreateResponse
    profile: AdvertiserProfileResponse

# --- Auth Schemas ---

class ChallengeRequest(BaseModel):
    public_key: str

class ChallengeResponse(BaseModel):
    challenge: str
    
class UserLogin(BaseModel):
    public_key: str
    signature: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    public_key: str
    role: str # Added role


# --- Post Schemas ---

class PostCreate(BaseModel):
    raw_text: str
    category: Optional[str] = None

class PostResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    raw_text: str
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Campaign Schemas ---

class CampaignCreate(BaseModel):
    name: str
    campaign_type: str = Field(..., description="Type of campaign: 'ad' or 'insight'.")
    content: Dict[str, Any] = Field(..., description="JSON object for ad creative or insight text.")
    targeting_criteria: Dict[str, Any] = Field(..., description="JSON object defining the target audience.")
    status: str = 'draft'
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class CampaignResponse(BaseModel):
    id: uuid.UUID
    advertiser_id: Optional[uuid.UUID]
    name: str
    campaign_type: str
    status: str
    content: Dict[str, Any]
    targeting_criteria: Dict[str, Any]
    budget: Optional[float]
    start_date: datetime
    end_date: Optional[datetime]
    impressions_count: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Serving Schemas ---

class AdResponse(BaseModel):
    campaign_id: uuid.UUID
    content: Dict[str, Any]

class InsightResponse(BaseModel):
    content: str # Insights are just simple text

# This is needed for Pydantic to handle the forward reference in UserResponse
UserResponse.update_forward_refs()