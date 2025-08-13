import os
import json
import redis

REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://redis:6379/0")
redis_client = redis.StrictRedis.from_url(REDIS_BROKER_URL, decode_responses=True)

def queue_key_for_user(user_id):
    """Return the Redis list key for this user's message queue."""
    return f"user_queue:{user_id}"

def push_message_for_user(user_id, message):
    """Push a JSON message to a specific user's queue."""
    key = queue_key_for_user(user_id)
    redis_client.rpush(key, json.dumps(message))

def pop_message_for_user(user_id):
    """Pop the oldest message from a specific user's queue."""
    key = queue_key_for_user(user_id)
    raw = redis_client.lpop(key)
    if raw:
        return json.loads(raw)
    return None

def push_broadcast(message, user_ids):
    """Push the same message to all specified user queues."""
    for uid in user_ids:
        push_message_for_user(uid, message)
