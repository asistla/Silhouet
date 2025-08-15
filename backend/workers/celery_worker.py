# backend/celery_worker.py
import os
from celery import Celery
import httpx
from sqlalchemy.orm import Session
import uuid
import json
import redis
from datetime import datetime
from database import SessionLocal
from models import Post, User
from crud.users import update_user_scores
from silhouet_config import PERSONALITY_KEYS

from workers.ads_worker import push_ads_for_campaign
from workers.insight_worker import push_insight

from dotenv import load_dotenv
load_dotenv()

REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://redis:6379/0")
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8001/score")

# Define the Redis Pub/Sub channel name (must match backend's listener)
PUBSUB_CHANNEL = "sentiment_updates"

# Initialize Celery app
celery_app = Celery(
    'sentiment_tasks',
    broker=REDIS_BROKER_URL,
    backend=REDIS_BROKER_URL
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

try:
    redis_publisher_client = redis.StrictRedis.from_url(REDIS_BROKER_URL, encoding="utf-8", decode_responses=False)
    redis_publisher_client.ping()
    print("Celery Worker: Redis publisher client initialized and connected.")
except Exception as e:
    print(f"Celery Worker: CRITICAL: Failed to connect Redis publisher client: {e}")
    redis_publisher_client = None

@celery_app.task(name="process_post_sentiment")
def process_post_sentiment_task(post_id: str, raw_text: str):
    print(f"Task: Processing sentiment for Post ID: {post_id}")
    
    db: Session = None
    try:
        db = SessionLocal() 
        db_post = db.query(Post).filter(Post.id == uuid.UUID(post_id)).first()

        if not db_post:
            print(f"Task: Post {post_id} not found in DB. Skipping sentiment analysis.")
            return

        response = httpx.post(MODEL_SERVICE_URL, json=({"text": raw_text}))
        response.raise_for_status()
        sentiment_data = json.loads(response.json())
        returned_scores = sentiment_data.get("scores")

        if returned_scores and isinstance(returned_scores, dict):
            db_post.sentiment_scores_json = json.dumps(returned_scores)
            db.add(db_post)
            db.commit()
            db.refresh(db_post)
            print(f"Task: Post {post_id}: Sentiment scores saved to post.")

            # --- UPDATE USER SCORES ---
            db_user = db.query(User).filter(User.user_id == db_post.user_id).first()
            if db_user:
                update_user_scores(db, user=db_user, new_scores=returned_scores)
                print(f"Task: User {db_user.user_id}: Average scores updated.")
            else:
                print(f"Task: User not found for post {post_id}. Cannot update scores.")
            # --- END UPDATE ---

            if redis_publisher_client:
                try:
                    update_payload = {
                        "type": "post_sentiment_update",
                        "post_id": post_id,
                        "user_id": str(db_post.user_id),
                        "raw_text": raw_text,
                        "sentiment_scores": returned_scores,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    redis_publisher_client.publish(PUBSUB_CHANNEL, json.dumps(update_payload))
                    print(f"Task: Published sentiment update for post {post_id} to Redis channel '{PUBSUB_CHANNEL}'.")
                except Exception as pub_exc:
                    print(f"Task: Error publishing sentiment update for post {post_id} to Redis: {pub_exc}")
            else:
                print("Task: Redis publisher client not initialized. Cannot publish update.")
        else:
            print(f"Task: Post {post_id}: Invalid sentiment scores received from model: {sentiment_data}")

    except httpx.RequestError as exc:
        print(f"Task: Post {post_id}: An error occurred while requesting model service: {exc}")
    except httpx.HTTPStatusError as exc:
        print(f"Task: Post {post_id}: Model service returned an error status {exc.response.status_code}: {exc.response.text}")
    except Exception as exc:
        print(f"Task: Post {post_id}: An unexpected error occurred in task: {exc}")
    finally:
        if db:
            db.close()

#=====================
#ads/insights pipeline
#=====================

@celery_app.task(name="push_ads")
def push_ads_task():
    push_ads_to_queue()

@celery_app.task(name="push_insights")
def push_insights_task():
    push_insights_to_queue()

# Beat schedule (merged into existing config)
celery_app.conf.beat_schedule = getattr(celery_app.conf, "beat_schedule", {})
celery_app.conf.beat_schedule.update({
    "push_ads_every_minute": {
        "task": "push_ads",
        "schedule": 60.0,  # every 1 min (MVP)
    },
    "push_insights_every_two_minutes": {
        "task": "push_insights",
        "schedule": 120.0,  # every 2 min (MVP)
    },
})
