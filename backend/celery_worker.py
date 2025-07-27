# backend/celery_worker.py
import os
from celery import Celery
import httpx
from sqlalchemy.orm import Session
import uuid
import json
import redis # <<< NEW IMPORT for synchronous Redis client
from datetime import datetime
from database import SessionLocal
#from models import Post

from dotenv import load_dotenv
load_dotenv()

REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://redis:6379/0")
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8001/score")
# Removed BACKEND_INTERNAL_UPDATE_URL as it's no longer needed

# Define the Redis Pub/Sub channel name (must match backend's listener)
PUBSUB_CHANNEL = "sentiment_updates" # <<< NEW

# Initialize Celery app
celery_app = Celery(
    'sentiment_tasks',
    broker=REDIS_BROKER_URL,
    backend=REDIS_BROKER_URL # Still use Redis for Celery result backend
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Initialize synchronous Redis client for publishing
# It's important to use a separate client for Pub/Sub than the one Celery uses internally for its broker
try:
    # Decode responses=False because we're encoding the JSON ourselves.
    # The backend listener will decode the bytes.
    redis_publisher_client = redis.StrictRedis.from_url(REDIS_BROKER_URL, encoding="utf-8", decode_responses=False)
    redis_publisher_client.ping()
    print("Celery Worker: Redis publisher client initialized and connected.")
except Exception as e:
    print(f"Celery Worker: CRITICAL: Failed to connect Redis publisher client: {e}")
    redis_publisher_client = None # Set to None if connection fails

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

        # Make HTTP call to model service
        response = httpx.post(MODEL_SERVICE_URL, json={"text": raw_text})
        response.raise_for_status()
        sentiment_data = response.json()
        returned_scores = sentiment_data.get("scores")

        if returned_scores and isinstance(returned_scores, dict):
            # Update the Post in the database
            db_post.sentiment_scores_json = json.dumps(returned_scores)
            db.add(db_post)
            db.commit()
            db.refresh(db_post)
            print(f"Task: Post {post_id}: Sentiment scores updated successfully.")

            # --- NEW: Publish update to Redis Pub/Sub ---
            if redis_publisher_client:
                print("Publisher client exists")
                try:
                    # Construct the message payload
                    # Ensure all data is JSON serializable
                    update_payload = {
                        "type": "post_sentiment_update", # Define a type for the message
                        "post_id": post_id,
                        "user_id": str(db_post.user_id), # Send user_id as string for WebSocket targeting
                        "raw_text": raw_text,
                        "sentiment_scores": returned_scores,
                        "timestamp": datetime.utcnow().isoformat() + "Z" # Current time for client
                    }
                    # Publish the JSON-encoded string to the channel
                    print(json.dumps(update_payload, indent = 2, sort_keys = True))
                    redis_publisher_client.publish(PUBSUB_CHANNEL, json.dumps(update_payload))
                    print(f"Task: Published sentiment update for post {post_id} to Redis channel '{PUBSUB_CHANNEL}'.")
                except Exception as pub_exc:
                    print(f"Task: Error publishing sentiment update for post {post_id} to Redis: {pub_exc}")
            else:
                print("Task: Redis publisher client not initialized. Cannot publish update.")
            # --- END NEW ---

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

# No main block needed, Celery worker command handles execution.
