import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import User
from workers.message_queue import push_broadcast
from .celery_app import celery_app  # Import the shared app

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@db:5432/silhouet")

# DB session setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@celery_app.task
def push_insight(claims: list[str]):
    """
    Push a broadcast insight for each claim to all active users.
    """
    if not claims:
        return None

    db = SessionLocal()
    try:
        all_users = db.query(User.user_id).all()
        user_ids = [str(uid) for (uid,) in all_users]

        if not user_ids:
            print("[insight_worker] No users found to broadcast to.")
            return

        for claim_text in claims:
            message = {
                "text": claim_text
            }
            push_broadcast(message, user_ids)

        print(f"[insight_worker] Broadcasted {len(claims)} insights to {len(user_ids)} users.")

    finally:
        db.close()
