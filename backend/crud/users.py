# backend/crud/users.py
from sqlalchemy.orm import Session
from models import User
from schemas import UserCreate
import uuid

def get_user_by_public_key(db: Session, public_key: str):
    return db.query(User).filter(User.public_key == public_key).first()

def create_user(db: Session, user: UserCreate):
    # For a PoC, we let SQLAlchemy generate the UUID for 'id' default
    db_user = User(public_key=user.public_key)
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Refresh to get the generated 'id' and 'created_at'
    return db_user

def get_user_by_id(db: Session, user_id: uuid.UUID):
    return db.query(User).filter(User.id == user_id).first()
