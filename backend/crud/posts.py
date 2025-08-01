# backend/crud/posts.py
from sqlalchemy.orm import Session
import uuid
# Removed httpx import - no longer needed for direct call
# Removed MODEL_SERVICE_URL constant - task handles it

from models import Post
from schemas import PostCreate

# Import the Celery task
from celery_worker import process_post_sentiment_task # <<< NEW IMPORT

def create_post(db: Session, post: PostCreate):
    # 1. Create the post entry in the database
    db_post = Post(user_id=post.user_id, raw_text=post.raw_text)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    # 2. Enqueue the sentiment analysis task
    # We pass the post ID as a string because UUID objects can cause serialization issues
    # when passed directly to Celery's default JSON serializer.
    process_post_sentiment_task.delay(str(db_post.id), db_post.raw_text) # <<< ENQUEUE TASK
    print(f"Post {db_post.id}: Sentiment analysis task enqueued.")

    # The create_post function now returns immediately, even before sentiment analysis is done.
    return db_post

def get_posts_by_user(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(Post).filter(Post.user_id == user_id).offset(skip).limit(limit).all()
