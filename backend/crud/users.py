# backend/crud/users.py
from sqlalchemy.orm import Session
from models import User, AdvertiserProfile
from schemas import UserCreate, UserCreateResponse, AdvertiserCreate, AdvertiserCreateResponse, AdvertiserProfileResponse
import uuid
from datetime import datetime, timezone
from silhouet_config import PERSONALITY_KEYS
from sqlalchemy.exc import IntegrityError
from nacl.signing import VerifyKey
from nacl.encoding import Base64Encoder
from nacl.exceptions import BadSignatureError
import redis.asyncio as redis

def get_user_by_public_key(db: Session, public_key: str):
    return db.query(User).filter(User.public_key == public_key).first()

def create_user(db: Session, user_data: UserCreate, role: str = 'user') -> User:
    """
    Creates a new user record in the database. Can specify a role.
    Returns the full User ORM object.
    """
    try:
        db_user_data = user_data.model_dump()
        # Remove any fields from the input that aren't in the User model
        # This is important for the AdvertiserCreate schema which has extra fields
        user_fields = {c.name for c in User.__table__.columns}
        filtered_user_data = {k: v for k, v in db_user_data.items() if k in user_fields}

        filtered_user_data.update({
            "user_id": uuid.uuid4(),
            "role": role,
            "total_posts_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        for key in PERSONALITY_KEYS:
            filtered_user_data[f"avg_{key}_score"] = 0.5

        new_user = User(**filtered_user_data)
        db.add(new_user)
        # We might not commit right away if part of a larger transaction
        return new_user
    except Exception as e:
        db.rollback()
        raise e

def create_advertiser(db: Session, advertiser_data: AdvertiserCreate) -> AdvertiserCreateResponse:
    """
    Creates an advertiser, which includes a User record and an AdvertiserProfile record.
    This is a transactional operation.
    """
    # Check if public key already exists to provide a clearer error
    if get_user_by_public_key(db, public_key=advertiser_data.public_key):
        raise IntegrityError("Public key already registered.", params=None, orig=None)

    try:
        # Create the base user with the 'advertiser' role
        new_user = create_user(db, advertiser_data, role='advertiser')
        
        # Create the advertiser profile
        new_profile = AdvertiserProfile(
            user_id=new_user.user_id,
            company_name=advertiser_data.company_name
        )
        db.add(new_profile)
        
        db.commit()
        db.refresh(new_user)
        db.refresh(new_profile)

        return AdvertiserCreateResponse(
            user=UserCreateResponse(
                user_id=new_user.user_id,
                public_key=new_user.public_key,
                role=new_user.role,
                created_at=new_user.created_at
            ),
            profile=AdvertiserProfileResponse(
                id=new_profile.id,
                company_name=new_profile.company_name,
                created_at=new_profile.created_at
            )
        )
    except Exception as e:
        db.rollback()
        raise e


async def authenticate_user_challenge(db: Session, redis_client: redis.Redis, public_key: str, signature: str) -> User:
    """
    Authenticates a user by verifying their signature against a stored challenge.
    Returns the User object if successful, otherwise returns None.
    """
    db_user = get_user_by_public_key(db, public_key)
    if not db_user:
        return None
    try:
        challenge_key = f"challenge:{public_key}"
        challenge = await redis_client.get(challenge_key)
        if not challenge:
            return None
        
        verify_key = VerifyKey(public_key.encode('utf-8'), encoder=Base64Encoder)
        challenge_str = challenge.decode('utf-8') if isinstance(challenge, bytes) else challenge
        
        import base64
        signature_bytes = base64.b64decode(signature)
        verify_key.verify(challenge_str.encode('utf-8'), signature_bytes)
        
        await redis_client.delete(challenge_key)
        return db_user
    except BadSignatureError:
        return None
    except Exception as e:
        print(f"An unexpected error occurred during authentication: {e}")
        return None

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
            current_avg_attr = f"avg_{key}_score"
            current_avg = getattr(user, current_avg_attr, 0.5)
            new_avg = ((current_avg * current_post_count) + new_score) / (current_post_count + 1)
            setattr(user, current_avg_attr, new_avg)

    user.total_posts_count += 1
    user.updated_at = datetime.now(timezone.utc)

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise e
