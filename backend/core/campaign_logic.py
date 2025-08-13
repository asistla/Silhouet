# backend/core/campaign_logic.py
import random
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Any
import uuid
import redis.asyncio as redis

from models import User, Campaign
from crud import campaigns as crud_campaigns
from silhouet_config import PERSONALITY_KEYS

def get_users_by_criteria(db: Session, criteria: Dict[str, Any]) -> List[User]:
    """
    Finds users who match a given set of targeting criteria.
    
    Args:
        db: The database session.
        criteria: A dictionary of filters, e.g.,
                  {
                      "age_min": 25,
                      "age_max": 35,
                      "state": "California",
                      "country": "USA",
                      "avg_resentment_score_gt": 0.7,
                      "avg_courage_score_lt": 0.3
                  }

    Returns:
        A list of User objects matching the criteria.
    """
    query = db.query(User)
    filters = []

    # Demographic and geographic filters
    for key, value in criteria.items():
        if hasattr(User, key) and not key.endswith(('_gt', '_lt')):
            filters.append(getattr(User, key) == value)

    # Age range filter
    if 'age_min' in criteria:
        filters.append(User.age >= criteria['age_min'])
    if 'age_max' in criteria:
        filters.append(User.age <= criteria['age_max'])

    # Personality score filters (greater than / less than)
    for key, value in criteria.items():
        if key.endswith('_gt') and key.replace('_gt', '') in PERSONALITY_KEYS:
            score_attr = f"avg_{key.replace('_gt', '')}_score"
            if hasattr(User, score_attr):
                filters.append(getattr(User, score_attr) > value)
        
        if key.endswith('_lt') and key.replace('_lt', '') in PERSONALITY_KEYS:
            score_attr = f"avg_{key.replace('_lt', '')}_score"
            if hasattr(User, score_attr):
                filters.append(getattr(User, score_attr) < value)

    if not filters:
        return []

    return query.filter(and_(*filters)).all()

def generate_insight_text(cohort_size: int, criteria: Dict[str, Any]) -> str:
    """
    Generates a human-readable insight string from cohort data.
    """
    if cohort_size == 0:
        return "No users found for the specified criteria."

    # Simple implementation for now
    # Example criteria: {"state": "California", "avg_resentment_score_gt": 0.7}
    desc = []
    for key, value in criteria.items():
        if key.endswith('_gt'):
            trait = key.replace('_gt', '').replace('_', ' ')
            desc.append(f"a high '{trait}' score")
        elif key.endswith('_lt'):
            trait = key.replace('_lt', '').replace('_', ' ')
            desc.append(f"a low '{trait}' score")
        else:
            desc.append(f"in {value}")
    
    return f"There are {cohort_size} users {', '.join(desc)}."

async def process_ad_campaign(db: Session, redis_client: redis.Redis, campaign: Campaign):
    """
    Processes a single ad campaign: finds matching users and populates their ad queues.
    """
    if not campaign.targeting_criteria:
        return

    users = get_users_by_criteria(db, campaign.targeting_criteria)
    if not users:
        return

    ad_payload = json.dumps({
        "campaign_id": str(campaign.id),
        "content": campaign.content
    })
    
    # For now, we assume a frequency cap of 1 impression per user.
    # This can be made more complex later.
    async with redis_client.pipeline() as pipe:
        for user in users:
            pipe.rpush(f"user_ads:{user.user_id}", ad_payload)
        await pipe.execute()

    # Update the total impressions count for the campaign
    crud_campaigns.increment_campaign_impressions(db, campaign.id, count=len(users))

async def process_insight_campaign(db: Session, redis_client: redis.Redis):
    """
    Generates and stores a single, random insight.
    """
    # 1. Generate random criteria
    # For simplicity, let's create an insight for a random state
    all_states = db.query(User.state).distinct().all()
    if not all_states:
        return
    
    random_state = random.choice(all_states)[0]
    criteria = {"state": random_state}

    # 2. Find users and generate text
    users = get_users_by_criteria(db, criteria)
    insight_text = generate_insight_text(len(users), criteria)

    # 3. Store in Redis with a TTL (e.g., 10 minutes)
    redis_key = f"insight:state:{random_state}"
    await redis_client.set(redis_key, insight_text, ex=600)
