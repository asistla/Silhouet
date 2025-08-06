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
    user_id: uuid.UUID # The UUID of the user creating the post
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
