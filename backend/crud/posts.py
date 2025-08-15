# backend/crud/posts.py
from sqlalchemy.orm import Session
import uuid
# Removed httpx import - no longer needed for direct call
# Removed MODEL_SERVICE_URL constant - task handles it

from models import Post
from schemas import PostCreate

# Import the Celery task
from workers.celery_worker import process_post_sentiment_task # <<< NEW IMPORT

def create_post(db: Session, post_text: str, user_id: uuid.UUID):
    # 1. Create the post entry in the database
    db_post = Post(user_id=user_id, raw_text=post_text)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    # 2. Enqueue the sentiment analysis task
    process_post_sentiment_task.delay(str(db_post.id), db_post.raw_text)
    print(f"Post {db_post.id}: Sentiment analysis task enqueued for user {user_id}.")

    return db_post

def get_posts_by_user(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(Post).filter(Post.user_id == user_id).offset(skip).limit(limit).all()
