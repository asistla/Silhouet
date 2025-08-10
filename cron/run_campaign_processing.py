# cron/run_campaign_processing.py
import asyncio
import os
from dotenv import load_dotenv
import sys

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
import redis.asyncio as redis

from backend.database import SessionLocal, get_db
from backend.crud import campaigns as crud_campaigns
from backend.core.campaign_logic import process_ad_campaign, process_insight_campaign

# Load environment variables from the project root .env file
load_dotenv(os.path.join(project_root, '.env'))

async def main():
    """
    Main function to run the campaign and insight processing jobs.
    This script is intended to be run by a scheduler (e.g., cron).
    """
    print("Starting campaign processing run...")
    db: Session = SessionLocal()
    redis_client: redis.Redis = None
    
    try:
        # --- Connect to Redis ---
        redis_url = os.getenv("REDIS_BROKER_URL")
        if not redis_url:
            raise ValueError("REDIS_BROKER_URL environment variable not set.")
        
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        print("Successfully connected to Redis.")

        # --- Process Active Ad Campaigns ---
        print("Fetching and processing active ad campaigns...")
        active_ad_campaigns = crud_campaigns.get_active_campaigns(db, campaign_type='ad')
        
        if not active_ad_campaigns:
            print("No active ad campaigns to process.")
        else:
            for campaign in active_ad_campaigns:
                print(f"Processing ad campaign: {campaign.name} ({campaign.id})")
                await process_ad_campaign(db, redis_client, campaign)
            print(f"Finished processing {len(active_ad_campaigns)} ad campaign(s).")

        # --- Process a System Insight ---
        print("Generating and processing a new system insight...")
        await process_insight_campaign(db, redis_client)
        print("Finished processing system insight.")

    except Exception as e:
        print(f"An error occurred during the campaign processing run: {e}")
    finally:
        # --- Clean up connections ---
        if redis_client:
            await redis_client.close()
            print("Redis connection closed.")
        if db:
            db.close()
            print("Database session closed.")
    
    print("Campaign processing run finished.")

if __name__ == "__main__":
    asyncio.run(main())
