# backend/crud/users.py
from sqlalchemy.orm import Session
from models import User
from schemas import UserCreate
import uuid
from datetime import datetime, timezone
from silhouet_config import PERSONALITY_KEYS
from sqlalchemy.exc import IntegrityError

def get_user_by_public_key(db: Session, public_key: str):
    return db.query(User).filter(User.public_key == public_key).first()

def get_or_create_user(db: Session, user: UserCreate):
    """
    Retrieves a user by public_key, or creates a new one if it doesn't exist.
    """
    db_user = get_user_by_public_key(db, public_key=user.public_key)
    if db_user:
        return db_user

    new_user_id = uuid.uuid4()
    user_data = user.model_dump() # Get data from Pydantic request
    user_data["total_posts_count"] = 0 # Initialize post count

    # Initialize all personality average scores to 0.5
    for key in PERSONALITY_KEYS:
        user_data[f"avg_{key}_score"] = 0.5

    user_data["user_id"] = new_user_id # Set the generated UUID

    # Set creation and update timestamps (nullable=False in model)
    current_utc_time = datetime.now(timezone.utc)
    user_data["created_at"] = current_utc_time
    user_data["updated_at"] = current_utc_time

    try:
        # Create a new User ORM object with all necessary data
        new_user = User(**user_data)
        db.add(new_user)
        db.commit()
        db.refresh(new_user) # Refresh to get any database-generated defaults if applicable
        return {"user_id": new_user.user_id, "public_key": user.public_key, "created_at": user_data["created_at"]}
    except Exception as e:
        db.rollback()
        raise e

def get_user_by_id(db: Session, user_id: uuid.UUID):
    return db.query(User).filter(User.user_id == user_id).first()

def update_user_scores(db: Session, user: User, new_scores: dict):
    """
    Updates a user's average scores with new scores from a post.
    """
    if not user:
        return None

    current_post_count = user.total_posts_count
    
    for key in PERSONALITY_KEYS:
        new_score = new_scores.get(key)
        if new_score is not None:
            # Get the current average score from the user object
            current_avg_attr = f"avg_{key}_score"
            current_avg = getattr(user, current_avg_attr, 0.5)

            # Calculate the new average
            new_avg = ((current_avg * current_post_count) + new_score) / (current_post_count + 1)
            
            # Set the updated average score on the user object
            setattr(user, current_avg_attr, new_avg)

    # Increment the total post count
    user.total_posts_count += 1
    
    # Set the updated_at timestamp
    user.updated_at = datetime.now(timezone.utc)

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise e
