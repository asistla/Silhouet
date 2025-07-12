# backend/schemas.py
from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
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
