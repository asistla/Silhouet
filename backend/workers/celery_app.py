# backend/workers/celery_app.py
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://redis:6379/0")

# Initialize the shared Celery app
celery_app = Celery(
    'silhouet_tasks',
    broker=REDIS_BROKER_URL,
    backend=REDIS_BROKER_URL,
    include=[
        'backend_code.workers.celery_worker',
        'backend_code.workers.insight_worker'
    ]
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Define the beat schedule for periodic tasks
#celery_app.conf.beat_schedule = {
#    "push_ads_every_minute": {
#        "task": "push_ads",
#        "schedule": 60.0,  # every 1 min (MVP)
#    },
#}

if __name__ == '__main__':
    celery_app.start()
