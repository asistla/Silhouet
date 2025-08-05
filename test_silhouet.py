import asyncio
import httpx
import websockets
import json
import uuid
import os
from dotenv import load_dotenv
import time

#----------- TEST
from randomUser import createRandomUser, createRandomPost
#-----------
# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "ws://localhost:8000")
# Timeout for waiting for WebSocket message
WEBSOCKET_RECEIVE_TIMEOUT = 30 # seconds
# How many users?
USER_COUNT = 10
# User create period?
USER_CREATE_PERIOD = 1 # seconds apart
# How many posts per user?
POSTS_PER_USER = 10
# Post create period?
POST_CREATE_PERIOD = 0.1 # seconds apart

# --- Helper Functions ---

async def check_service_status(url: str, service_name: str):
    """Checks if a service is reachable."""
    print(f"Checking status of {service_name} at {url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url + "/docs", timeout=5) # Assuming /docs is always available
            response.raise_for_status()
            print(f"✅ {service_name} is UP. Status: {response.status_code}")
            return True
    except httpx.HTTPStatusError as e:
        print(f"❌ {service_name} returned error status {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        print(f"❌ Could not connect to {service_name} at {url}: {e}")
    return False

async def create_user(client: httpx.AsyncClient) -> tuple[uuid.UUID | None, str | None]:
    """
    Creates a new test user with a generated public_key and returns their ID and public key.
    """
    user_payload = createRandomUser()
    public_key = user_payload['public_key']
    print(f"\nAttempting to create user with public_key: {public_key}")
    try:
        response = await client.post(
            f"{BACKEND_URL}/users/",
            json=user_payload
        )
        response.raise_for_status()
        user_data = response.json()
        user_id = uuid.UUID(user_data["user_id"])
        created_public_key = user_data['public_key']
        print(f"✅ User created: ID={user_id}, Public Key={created_public_key}")
        return user_id, created_public_key
    except httpx.HTTPStatusError as e:
        print(f"❌ Failed to create user (Status: {e.response.status_code}): {e.response.text}")
    except httpx.RequestError as e:
        print(f"❌ Network error creating user: {e}")
    return None, None

async def create_post(client: httpx.AsyncClient, user_id: uuid.UUID, raw_text: str) -> uuid.UUID | None:
    """Creates a post for the given user_id and returns its ID."""
    print(f"\nAttempting to create post for user {user_id}...")
    try:
        response = await client.post(
            f"{BACKEND_URL}/posts/",
            json={"user_id": str(user_id), "raw_text": raw_text}
        )
        response.raise_for_status()
        post_data = response.json()
        post_id = uuid.UUID(post_data.get('id'))
        print(f"✅ Post created: ID={post_id}")
        return post_id
    except httpx.HTTPStatusError as e:
        print(f"❌ Failed to create post (Status: {e.response.status_code}): {e.response.text}")
    except httpx.RequestError as e:
        print(f"❌ Network error creating post: {e}")
    return None

async def run_e2e_test_for_user(http_client: httpx.AsyncClient):
    """
    Runs the full E2E test for a single user: create user, connect WebSocket,
    create posts, and verify WebSocket messages for each post.
    """
    user_id, public_key = await create_user(http_client)
    if not user_id:
        print("Test for this user aborted due to user creation failure.")
        return

    user_id_for_ws = str(user_id)
    print(f"ℹ️ Using created user's ID ({user_id_for_ws}) as WebSocket client_id.")

    print(f"\nConnecting to WebSocket at {WEBSOCKET_URL}/ws/{user_id_for_ws}...")
    try:
        async with websockets.connect(f"{WEBSOCKET_URL}/ws/{user_id_for_ws}") as ws:
            print(f"✅ WebSocket connected for client: {user_id_for_ws}")

#            try:
#                with open('example.txt', 'r') as f:
#                    test_raw_text_template = f.read()
#            except FileNotFoundError:
#                print("⚠️ 'example.txt' not found. Using default post content.")
#                test_raw_text_template = "This is a default post content."

            for i in range(POSTS_PER_USER):
                print(f"\n--- Starting Post {i+1}/{POSTS_PER_USER} for User {user_id_for_ws} ---")
                post_text = createRandomPost()
#                post_text = f"Post {i+1}/{POSTS_PER_USER} by {public_key}: {test_raw_text_template}"
                post_id = await create_post(http_client, user_id, post_text)

                if not post_id:
                    print(f"Skipping post {i+1} due to creation failure.")
                    await asyncio.sleep(POST_CREATE_PERIOD)
                    continue

                print(f"Waiting for sentiment update for post {post_id} (timeout: {WEBSOCKET_RECEIVE_TIMEOUT}s)...")
                try:
                    message_str = await asyncio.wait_for(ws.recv(), timeout=WEBSOCKET_RECEIVE_TIMEOUT)
                    message_data = json.loads(message_str)

                    # Basic validation of the received message
                    if message_data.get("user_id") == str(user_id):
                        print(f"✅ Received expected sentiment update for user {user_id}:")
                        # print(json.dumps(message_data, indent=2))
                    else:
                        print(f"❌ FAILED: Received message for wrong user. Expected {user_id}, got {message_data.get('user_id')}")

                except asyncio.TimeoutError:
                    print(f"❌ FAILED: Timeout waiting for WebSocket message for post {post_id}.")
                except json.JSONDecodeError:
                    print(f"❌ FAILED: Could not decode JSON from WebSocket message: {message_str}")
                except Exception as e:
                    print(f"❌ An unexpected error occurred while receiving WebSocket message: {e}")
                await asyncio.sleep(POST_CREATE_PERIOD)

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ WebSocket connection closed with error: {e}")
    except Exception as e:
        print(f"❌ Could not connect to WebSocket: {e}")


# --- Main E2E Test Function ---

async def main():
    print("--- Starting Silhouet E2E Test ---")

    backend_up = await check_service_status(BACKEND_URL, "Backend Service")
    if not backend_up:
        print("Test aborted due to backend not being reachable.")
        return

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        for i in range(USER_COUNT):
            print(f"\n\n--- Running Test for User {i+1}/{USER_COUNT} ---")
            await run_e2e_test_for_user(http_client)
            if i < USER_COUNT - 1:
                print(f"--- Waiting for {USER_CREATE_PERIOD}s before next user ---")
                await asyncio.sleep(USER_CREATE_PERIOD)

    print("\n--- Silhouet E2E Test Finished ---")

if __name__ == "__main__":
    asyncio.run(main())
