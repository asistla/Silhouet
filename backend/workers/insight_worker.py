import os
from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import User
from workers.message_queue import push_broadcast

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@db:5432/silhouet")
REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://redis:6379/0")

celery_app = Celery('insight_worker', broker=REDIS_BROKER_URL)

# DB session setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@celery_app.task
def push_insight(text: str):
    """
    Push a broadcast insight to all active users (for MVP: all users in DB).
    """
    db = SessionLocal()
    try:
        all_users = db.query(User.user_id).all()
        user_ids = [str(uid) for (uid,) in all_users]

        message = {
            "text": text
        }
        push_broadcast(message, user_ids)

        print(f"[insight_worker] Broadcasted insight to {len(user_ids)} users.")

    finally:
        db.close()
