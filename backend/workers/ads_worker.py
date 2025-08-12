import os
from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import User, Campaign  # Assuming Campaign model exists
from workers.message_queue import push_message_for_user

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@db:5432/silhouet")
REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://redis:6379/0")

celery_app = Celery('ads_worker', broker=REDIS_BROKER_URL)

# DB session setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@celery_app.task
def push_ads_for_campaign(campaign_id: str):
    """
    Fetch campaign from DB, resolve target user_ids, and push ads into their queues.
    """
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            print(f"[ads_worker] Campaign {campaign_id} not found.")
            return

        # Resolve targets based on campaign filters
        query = db.query(User.user_id)
        filters = campaign.filters or {}
        # Example filter application (you’ll adapt for your filter schema)
        if "min_age" in filters:
            query = query.filter(User.age >= filters["min_age"])
        if "max_age" in filters:
            query = query.filter(User.age <= filters["max_age"])
        if "sex" in filters:
            query = query.filter(User.sex == filters["sex"])
        # TODO: Add personality score filters here
        target_user_ids = [str(uid) for (uid,) in query.all()]

        # Push ad message to each user queue
        message = {
            "campaign_id": str(campaign.id),
            "mediaUrl": campaign.media_url,
            "targets": target_user_ids  # Optional; frontend will see this means it's an ad
        }
        for uid in target_user_ids:
            push_message_for_user(uid, message)

        print(f"[ads_worker] Pushed ad for campaign {campaign_id} to {len(target_user_ids)} users.")

    finally:
        db.close()
