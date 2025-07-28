# backend/schemas.py
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    age: int = Field(..., description="User's age.")
    sex: str = Field(..., description="User's biological sex (e.g., 'Male', 'Female', 'Non-binary', 'Prefer not to say').")
    gender: str = Field(..., description="User's gender identity (e.g., 'Man', 'Woman', 'Non-binary', 'Prefer not to say').")
    religion: str = Field(..., description="User's religious affiliation (e.g., 'Christianity', 'Islam', 'None', 'Prefer not to say').")
    ethnicity: str = Field(..., description="User's ethnicity (e.g., 'Asian', 'Caucasian', 'African', 'Prefer not to say').")
    pincode: str = Field(..., description="User's residential pincode.")
    city: str = Field(..., description="User's city.")
    district: str = Field(..., description="User's district.")
    state: str = Field(..., description="User's state.")
    country: str = Field(..., description="User's country.")
    nationality: str = Field(..., description="User's nationality.")
    public_key: str # The user's public key string as their pseudo-identifier

class UserResponse(BaseModel):
    id: uuid.UUID
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
