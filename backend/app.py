from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlalchemy_func
from datetime import datetime, timezone
import time
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import json
import asyncio
import uuid
from database import SessionLocal, engine, Base
from crud import users, posts
from schemas import UserCreate, UserResponse, PostCreate, PostResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
from silhouet_config import PERSONALITY_KEYS, AGGREGATION_FREQUENCIES, PERSONALITY_LABEL_MAP
from models import User, AggregatedGeoScore
from database import get_db_session, create_db_tables
from schemas import UserCreate, PostCreate

load_dotenv()
app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connections_by_id: Dict[str, WebSocket] = {}
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connections_by_id[client_id] = websocket
        print(f"WebSocket connected: {websocket.client} (ID: {client_id})")
    def disconnect(self, websocket: WebSocket, client_id: str):
        self.active_connections.remove(websocket)
        if client_id in self.connections_by_id and self.connections_by_id[client_id] == websocket:
            del self.connections_by_id[client_id]
        print(f"WebSocket disconnected: {websocket.client} (ID: {client_id})")
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    async def send_message_to_client(self, client_id: str, message: str):
        websocket = self.connections_by_id.get(client_id)
        if websocket:
            try:
                await websocket.send_text(message)
                print(f"Sent message to client {client_id} via WebSocket.")
            except RuntimeError as e:
                print(f"Failed to send to client {client_id} due to connection error: {e}. Disconnecting.")
                self.disconnect(websocket, client_id)
        else:
            print(f"Client {client_id} not found in active connections. Message not sent.")
    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except RuntimeError as e:
                print(f"Error broadcasting to a connection: {e}. Attempting to disconnect.")
                self.disconnect(connection, "unknown_client")

manager = ConnectionManager()
redis_client: redis.Redis = None
PUBSUB_CHANNEL = "sentiment_updates"

async def listen_for_redis_updates():
    print(f"Starting Redis Pub/Sub listener on channel: {PUBSUB_CHANNEL}")
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(PUBSUB_CHANNEL)
    while True:
        try:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message and message.get('data'):
                try:
                    decoded_message = json.loads(message['data'])
                    user_id = decoded_message.get("user_id")
                    if user_id:
                        await manager.send_message_to_client(user_id, json.dumps(decoded_message))
                    else:
                        await manager.broadcast(json.dumps(decoded_message))
                except (json.JSONDecodeError, Exception) as e:
                    print(f"Error processing Redis message: {e}")
            await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            print("Redis Pub/Sub listener cancelled.")
            break
        except Exception as e:
            print(f"Unhandled error in Redis Pub/Sub listener: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def on_startup():
    print("Application startup...")
    max_retries = 10
    retry_delay = 5
    for i in range(max_retries):
        try:
            db = SessionLocal()
            Base.metadata.create_all(bind=engine)
            db.close()
            print("Database tables ensured.")
            break
        except Exception as e:
            print(f"DB connection failed: {e}, retrying in {retry_delay}s...")
            time.sleep(retry_delay)
    else:
        print("CRITICAL: DB connection failed after multiple retries.")
    
    global redis_client
    redis_url = os.getenv("REDIS_BROKER_URL")
    try:
        redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await redis_client.ping()
        print("Redis client connected.")
        asyncio.create_task(listen_for_redis_updates())
        print("Redis listener task created.")
    except Exception as e:
        print(f"CRITICAL: Redis connection failed: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    print("Application shutdown.")
    if redis_client:
        await redis_client.close()
        print("Redis client closed.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FilteredScoresRequest(BaseModel):
    age_min: Optional[int] = Field(None, description="Minimum age")
    age_max: Optional[int] = Field(None, description="Maximum age")
    sex: Optional[str] = None
    gender: Optional[str] = None
    religion: Optional[str] = None
    ethnicity: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    nationality: Optional[str] = None

@app.post("/scores/filtered", status_code=status.HTTP_200_OK)
def get_filtered_scores(filters: FilteredScoresRequest, db: Session = Depends(get_db)):
    try:
        query = db.query(User)

        if filters.age_min is not None:
            query = query.filter(User.age >= filters.age_min)
        if filters.age_max is not None:
            query = query.filter(User.age <= filters.age_max)

        for field in ['sex', 'gender', 'religion', 'ethnicity', 'pincode', 'city', 'district', 'state', 'country', 'nationality']:
            if getattr(filters, field) is not None:
                query = query.filter(getattr(User, field) == getattr(filters, field))

        if query.count() == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users match the specified criteria.")

        avg_scores = {f"avg_{key}_score": sqlalchemy_func.avg(getattr(User, f"avg_{key}_score")) for key in PERSONALITY_KEYS}
        result = query.with_entities(*avg_scores.values()).one()

        return {key: round(value, 4) if value is not None else 0.5 for key, value in zip(avg_scores.keys(), result)}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def handle_user_login(user: UserCreate, db: Session = Depends(get_db)):
    """
    This endpoint handles both user login and registration.
    It retrieves the user by public_key or creates a new one if not found.
    """
    db_user = users.get_or_create_user(db=db, user=user)
    if not db_user:
        raise HTTPException(status_code=400, detail="Could not retrieve or create user.")
    return db_user

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    db_user = users.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@app.post("/posts/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_new_post(post: PostCreate, db: Session = Depends(get_db)):
    db_user = users.get_user_by_id(db, user_id=post.user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return posts.create_post(db=db, post=post)

@app.get("/users/{user_id}/posts", response_model=list[PostResponse])
def read_user_posts(user_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_user = users.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return posts.get_posts_by_user(db, user_id=user_id, skip=skip, limit=limit)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        print(f"Client {client_id} disconnected.")
    except Exception as e:
        print(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(websocket, client_id)
