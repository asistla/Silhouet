# backend/crud/users.py
from sqlalchemy.orm import Session
from models import User
from schemas import UserCreate, UserCreateResponse
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

def create_user(db: Session, user_data: UserCreate) -> UserCreateResponse:
    """
    Creates a new user record in the database with a client-provided public key.
    """
    try:
        db_user_data = user_data.model_dump()
        db_user_data.update({
            "user_id": uuid.uuid4(),
            "total_posts_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        # Initialize all personality average scores to 0.5
        for key in PERSONALITY_KEYS:
            db_user_data[f"avg_{key}_score"] = 0.5

        new_user = User(**db_user_data)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return UserCreateResponse(
            user_id=new_user.user_id,
            public_key=new_user.public_key,
            created_at=new_user.created_at
        )
    except IntegrityError:
        db.rollback()
        # This likely means the public key already exists.
        return None
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
        # 1. Retrieve the challenge from Redis
        challenge_key = f"challenge:{public_key}"
        challenge = await redis_client.get(challenge_key)
        if not challenge:
            return None # Challenge expired or was never set

        # 2. Decode the public key and signature from Base64
        verify_key = VerifyKey(public_key.encode('utf-8'), encoder=Base64Encoder)
        
        # The signature is of the challenge string.
        # The signature itself is also base64 encoded by the client.
        signature_bytes = signature.encode('utf-8')

        # 3. Verify the signature
        # The signed message is the challenge string itself, which was sent to the client.
        verify_key.verify(challenge, signature_bytes, encoder=Base64Encoder)

        # 4. On successful verification, delete the challenge to prevent reuse
        await redis_client.delete(challenge_key)

        return db_user
    except BadSignatureError:
        # Signature was invalid
        return None
    except Exception as e:
        # Handle other potential errors (e.g., decoding errors)
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
