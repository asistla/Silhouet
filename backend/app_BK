# backend/app.py
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import time
import os
from dotenv import load_dotenv
from typing import List, Dict # <<< ADD Dict
import json
import asyncio # <<< NEW IMPORT for async operations
import uuid
from database import SessionLocal, engine, Base
from crud import users, posts
from schemas import UserCreate, UserResponse, PostCreate, PostResponse
from pydantic import BaseModel
import redis.asyncio as redis # <<< NEW IMPORT for async Redis client

# Load environment variables
load_dotenv()

app = FastAPI()

# --- ConnectionManager for WebSockets ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Store connections by client_id. If client_id is user_id, it enables targeted messages.
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
            except RuntimeError as e: # Handle potential connection issues during send
                print(f"Failed to send to client {client_id} due to connection error: {e}. Disconnecting.")
                self.disconnect(websocket, client_id) # Attempt to disconnect faulty connection
        else:
            print(f"Client {client_id} not found in active connections. Message not sent.")

    async def broadcast(self, message: str):
        for connection in list(self.active_connections): # Iterate over a copy to allow modification during iteration
            try:
                await connection.send_text(message)
            except RuntimeError as e:
                print(f"Error broadcasting to a connection: {e}. Attempting to disconnect.")
                self.disconnect(connection, "unknown_client") # Placeholder client_id if not tracked for broadcast

manager = ConnectionManager()

# --- Redis Client for Pub/Sub ---
redis_client: redis.Redis = None # Type hint for global redis client instance
PUBSUB_CHANNEL = "sentiment_updates" # Define the Redis Pub/Sub channel name

async def listen_for_redis_updates():
    """
    Listens for messages on the Redis Pub/Sub channel and pushes them to WebSockets.
    """
    print(f"Starting Redis Pub/Sub listener on channel: {PUBSUB_CHANNEL}")
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(PUBSUB_CHANNEL)

    # Listen indefinitely for messages
    while True:
        try:
            message = await pubsub.get_message(ignore_subscribe_messages=True) #, timeout=5.0)
            if message:
                print("PUBSUB CLIENT: Received message: %s"%(str(message)))
                data = message.get('data')
                print(data)
                if data:
                    try:
                        decoded_message = json.loads(data)
                        print(f"Received Redis Pub/Sub message: {decoded_message}")

                        # Assuming the message contains 'user_id' and the update payload
                        user_id = decoded_message.get("user_id")
                        if user_id:
                            # Send message to specific user
                            await manager.send_message_to_client(user_id, json.dumps(decoded_message))
                        else:
                            # If no user_id or general update, broadcast to all
                            await manager.broadcast(json.dumps(decoded_message))

                    except json.JSONDecodeError:
                        print(f"Could not decode JSON from Redis message: {data.decode('utf-8')}")
                    except Exception as e:
                        print(f"Error processing Redis Pub/Sub message: {e}")
            await asyncio.sleep(0.01) # Small sleep to prevent busy-waiting
        except asyncio.CancelledError:
            print("Redis Pub/Sub listener cancelled.")
            break
        except Exception as e:
            print(f"Unhandled error in Redis Pub/Sub listener: {e}")
            await asyncio.sleep(5) # Wait before retrying on unexpected errors


# --- Database Initialization Logic & Redis Client Setup ---
@app.on_event("startup")
async def on_startup(): # Make startup an async function
    print("Application startup event triggered.")
    
    # Database initialization
    max_retries = 10
    retry_delay = 5 # seconds
    for i in range(max_retries):
        try:
            print(f"Attempting to create database tables... (Attempt {i+1}/{max_retries})")
            db = SessionLocal()
            Base.metadata.create_all(bind=engine)
            db.close()
            print("Database tables ensured.")
            break # Exit loop if successful
        except Exception as e:
            print(f"Database connection or table creation failed: {e}")
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    else: # This else block executes if the loop finishes without a 'break'
        print("CRITICAL: Failed to connect to database and create tables after multiple retries. Application may not function correctly.")
        # Consider sys.exit(1) here in production


    # Initialize Redis client for Pub/Sub
    global redis_client
    redis_url = os.getenv("REDIS_BROKER_URL")
    print(f"Connecting to Redis for Pub/Sub at: {redis_url}")
    try:
        redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await redis_client.ping() # Test connection
        print("Redis Pub/Sub client initialized and connected.")
    except Exception as e:
        print(f"CRITICAL: Failed to connect to Redis for Pub/Sub: {e}")
        # Application will still run, but real-time updates won't work


    # Start the Redis Pub/Sub listener in the background
    asyncio.create_task(listen_for_redis_updates())
    print("Redis Pub/Sub listener task created.")


@app.on_event("shutdown")
async def on_shutdown(): # Make shutdown an async function
    print("Application shutdown event triggered.")
    if redis_client:
        await redis_client.close() # Close Redis connection gracefully
        print("Redis Pub/Sub client closed.")


# Dependency to get DB session (existing)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- User Endpoints (existing) ---
@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = users.get_user_by_public_key(db, public_key=user.public_key)
    if db_user:
        return db_user
    return users.create_user(db=db, user=user)

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    db_user = users.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

# --- Post Endpoints (existing) ---
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
    user_posts = posts.get_posts_by_user(db, user_id=user_id, skip=skip, limit=limit)
    return user_posts

# --- WebSocket Endpoint (from previous step, with minor connection manager adjustments) ---
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        # Keep connection alive, potentially listen for client messages
        while True:
            # You might want to listen for client messages if you want interactive WebSockets
            # For now, just a placeholder to keep the connection open for server-sent messages.
            await websocket.receive_text() # This blocks until a message is received
            # print(f"Message from {client_id}: {data}") # Uncomment if you want to see client messages
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        print(f"Client {client_id} disconnected from WebSocket.")
    except Exception as e:
        print(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(websocket, client_id)
