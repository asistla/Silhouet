# backend/celery_worker.py
import os
import httpx
import uuid
import json
import redis
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Post, User
from crud.users import update_user_scores
from workers.ads_worker import push_ads_for_campaign
from workers.insight_worker import push_insight
from .celery_app import celery_app  # Import the shared app

from dotenv import load_dotenv
load_dotenv()

REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://redis:6379/0")
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8001/process")

# Define the Redis Pub/Sub channel name (must match backend's listener)
PUBSUB_CHANNEL = "sentiment_updates"

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
        
        # SCORES processing
        returned_scores = sentiment_data.get("scores")
        if returned_scores and isinstance(returned_scores, dict):
            db_post.sentiment_scores_json = json.dumps(returned_scores)
            db.add(db_post)
            db.commit()
            db.refresh(db_post)
            print(f"Task: Post {post_id}: Sentiment scores saved to post.")

            db_user = db.query(User).filter(User.user_id == db_post.user_id).first()
            if db_user:
                update_user_scores(db, user=db_user, new_scores=returned_scores)
                print(f"Task: User {db_user.user_id}: Average scores updated.")
            else:
                print(f"Task: User not found for post {post_id}. Cannot update scores.")

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

        # CLAIMS processing
        returned_claims = sentiment_data.get("claims")
        if returned_claims and isinstance(returned_claims, list):
            # Asynchronously trigger the insight worker task
            push_insight.delay(claims=returned_claims)
            print(f"Task: Post {post_id}: Enqueued {len(returned_claims)} claims for insight processing.")
        else:
            print(f"Task: Post {post_id}: No claims received or claims format is invalid.")

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
#ads pipeline
#=====================

@celery_app.task(name="push_ads")
def push_ads_task():
    # This should be implemented in ads_worker.py, just calling it from here.
    # For now, assuming push_ads_for_campaign is the entry point.
    push_ads_for_campaign()
