
# backend/app.py
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlalchemy_func
from datetime import datetime, timezone, timedelta
import time
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import json
import asyncio
import uuid
import secrets

# Local imports
from database import SessionLocal, engine, Base, get_db
from crud import users, posts
from schemas import (
    UserCreate, UserResponse, PostCreate, PostResponse, 
    UserLogin, UserCreateResponse, ChallengeRequest, ChallengeResponse, Token,
    AdResponse, InsightResponse
)
from api import campaigns as campaigns_router
from api import admin as admin_router
from pydantic import BaseModel, Field
import redis.asyncio as redis
from silhouet_config import PERSONALITY_KEYS
from models import User
from auth import get_current_user, create_access_token, verify_token

load_dotenv()
app = FastAPI()

# --- Routers ---
app.include_router(campaigns_router.router)
app.include_router(admin_router.router)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"WebSocket disconnected: {client_id}")

    async def send_message_to_client(self, client_id: str, message: str):
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_text(message)
            except RuntimeError as e:
                print(f"Failed to send to client {client_id}: {e}. Disconnecting.")
                self.disconnect(client_id)

manager = ConnectionManager()
redis_client: redis.Redis = None
PUBSUB_CHANNEL = "sentiment_updates"

# --- Redis Pub/Sub Listener ---
async def listen_for_redis_updates():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(PUBSUB_CHANNEL)
    while True:
        try:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message and message.get('data'):
                decoded_message = json.loads(message['data'])
                user_id = decoded_message.get("user_id")
                if user_id:
                    await manager.send_message_to_client(user_id, json.dumps(decoded_message))
            await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error in Redis listener: {e}")
            await asyncio.sleep(5)

# --- Application Lifecycle Events ---
@app.on_event("startup")
async def on_startup():
    # Database connection
    for i in range(10):
        try:
            db = SessionLocal()
            Base.metadata.create_all(bind=engine)
            db.close()
            print("Database tables ensured.")
            break
        except Exception as e:
            print(f"DB connection failed: {e}, retrying...")
            time.sleep(5)
    
    # Redis connection
    global redis_client
    try:
        redis_client = redis.from_url(os.getenv("REDIS_BROKER_URL"), decode_responses=True)
        await redis_client.ping()
        print("Redis client connected.")
        asyncio.create_task(listen_for_redis_updates())
    except Exception as e:
        print(f"CRITICAL: Redis connection failed: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    if redis_client:
        await redis_client.close()
        print("Redis client closed.")

# --- API Endpoints ---

# Authentication
@app.post("/auth/challenge", response_model=ChallengeResponse)
async def get_challenge(request: ChallengeRequest, db: Session = Depends(get_db)):
    if not users.get_user_by_public_key(db, public_key=request.public_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    challenge = secrets.token_hex(32)
    await redis_client.set(f"challenge:{request.public_key}", challenge, ex=300)
    return ChallengeResponse(challenge=challenge)

@app.post("/users/login", response_model=Token)
async def login_for_access_token(user_login: UserLogin, db: Session = Depends(get_db)):
    # Note: authenticate_user_challenge is not in the provided crud/users.py, assuming it exists
    # and works as intended. If not, this part would need implementation.
    db_user = await users.authenticate_user_challenge(
        db, redis_client, user_login.public_key, user_login.signature
    )
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature or challenge",
        )
    access_token = create_access_token(data={"sub": db_user.public_key})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_id": str(db_user.user_id), 
        "public_key": db_user.public_key,
        "role": db_user.role  # Include role in response
    }

# Users
@app.post("/users/", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    if users.get_user_by_public_key(db, public_key=user.public_key):
        raise HTTPException(status_code=400, detail="Public key already registered.")
    # Refactored to use the more generic create_user function
    created_user = users.create_user(db=db, user_data=user, role='user')
    db.commit()
    db.refresh(created_user)
    if not created_user:
        raise HTTPException(status_code=500, detail="Could not create user.")
    return created_user

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Posts
@app.post("/posts/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_new_post(post: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Assuming posts.create_post exists and works as intended.
    return posts.create_post(db=db, post_text=post.raw_text, user_id=current_user.user_id)

@app.get("/users/me/posts", response_model=list[PostResponse])
def read_my_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Assuming posts.get_posts_by_user exists and works as intended.
    return posts.get_posts_by_user(db, user_id=current_user.user_id, skip=skip, limit=limit)

# Scores
@app.get("/scores/me", status_code=status.HTTP_200_OK)
def get_my_scores(current_user: User = Depends(get_current_user)):
    scores = {f"avg_{key}_score": getattr(current_user, f"avg_{key}_score", 0.5) for key in PERSONALITY_KEYS}
    return scores

class FilteredScoresRequest(BaseModel):
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    # ... other filters
    
@app.post("/scores/filtered", status_code=status.HTTP_200_OK)
def get_filtered_scores(filters: FilteredScoresRequest, db: Session = Depends(get_db)):
    query = db.query(User)
    # Apply filters...
    if query.count() == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users match criteria.")
    avg_scores = {f"avg_{key}_score": sqlalchemy_func.avg(getattr(User, f"avg_{key}_score")) for key in PERSONALITY_KEYS}
    result = query.with_entities(*avg_scores.values()).one()
    return {key: round(value, 4) if value is not None else 0.5 for key, value in zip(avg_scores.keys(), result)}

# --- Serving Endpoints ---
@app.get("/serve/ad", response_model=Optional[AdResponse])
async def serve_ad(current_user: User = Depends(get_current_user)):
    ad_json = await redis_client.lpop(f"user_ads:{current_user.user_id}")
    if not ad_json:
        return None
    ad_data = json.loads(ad_json)
    return AdResponse(**ad_data)

@app.get("/serve/insight", response_model=Optional[InsightResponse])
async def serve_insight(current_user: User = Depends(get_current_user)):
    geo_keys_to_check = [
        f"insight:pincode:{current_user.pincode}",
        f"insight:city:{current_user.city}",
        f"insight:state:{current_user.state}",
        f"insight:country:{current_user.country}",
        "insight:global:all"
    ]
    insight_text_list = await redis_client.mget(geo_keys_to_check)
    first_valid_insight = next((item for item in insight_text_list if item is not None), None)
    
    if not first_valid_insight:
        return None
    return InsightResponse(content=first_valid_insight)

# WebSocket
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)
