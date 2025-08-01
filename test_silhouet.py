import asyncio
import httpx
import websockets
import json
import uuid
import os
from dotenv import load_dotenv
import time

#----------- TEST
from randomUser import createRandomUser
#-----------
# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "ws://localhost:8000")
# TEST_USER_PUBLIC_KEY will now be generated dynamically
# Timeout for waiting for WebSocket message
WEBSOCKET_RECEIVE_TIMEOUT = 30 # seconds

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

# MODIFIED: create_user now takes public_key as an argument
async def create_user(client: httpx.AsyncClient, public_key: str) -> uuid.UUID | None:
    """
    Creates a new test user with a generated public_key and returns their ID.
    Does NOT attempt to reuse existing users in this version.
    """
    print(f"\nAttempting to create user with public_key: {public_key}")
    try:
        response = await client.post(
            f"{BACKEND_URL}/register/",
            json=createRandomUser()
        )
        response.raise_for_status()
        user_data = response.json()
        print(json.dumps(user_data, indent = 2, sort_keys = True))
        user_id = uuid.UUID(user_data["user_id"])
#        print(f"✅ User created: ID={user_id}, Public Key={user_data['public_key']}")
        return user_id
    except httpx.HTTPStatusError as e:
        # If we get a 400 'Public key already registered' despite generating a unique key,
        # it might indicate an issue with the key generation or a race condition/very rapid test execution.
        print(f"❌ Failed to create user (Status: {e.response.status_code}): {e.response.text}")
        if e.response.status_code == 400 and "Public key already registered" in e.response.text:
            print("Hint: This might occur if a previous test run created this user rapidly, or if UUID generation is somehow repeating.")
    except httpx.RequestError as e:
        print(f"❌ Network error creating user: {e}")
    return None

async def create_post(client: httpx.AsyncClient, user_id: uuid.UUID, raw_text: str) -> uuid.UUID | None:
    """Creates a post for the given user_id and returns its ID."""
    print(f"\nAttempting to create post for user {user_id} with text: '{raw_text[:50]}...'")
    try:
        response = await client.post(
            f"{BACKEND_URL}/posts/",
            json={"user_id": str(user_id), "raw_text": raw_text}
        )
        response.raise_for_status()
        post_data = response.json()
        print(post_data)
        post_id = post_data.get('id')
        print(f"✅ Post created: ID={post_id}")
        return post_id
    except httpx.HTTPStatusError as e:
        print(f"❌ Failed to create post (Status: {e.response.status_code}): {e.response.text}")
    except httpx.RequestError as e:
        print(f"❌ Network error creating post: {e}")
    return None

# --- Main E2E Test Function ---

async def main():
    print("--- Starting Silhouet E2E Test ---")

    # 1. Service Checks
    backend_up = await check_service_status(BACKEND_URL, "Backend Service")
    if not backend_up:
        print("Test aborted due to backend not being reachable.")
        return

    # --- CRITICAL CHANGE: Establish WebSocket connection FIRST ---
    received_message = None
    # Use the created user's ID as the client_id for WebSocket connection
    # We'll create the user first, then use its ID for the WS.
    temp_user_id = None
    async with httpx.AsyncClient() as http_client:
        # Generate a truly unique public key for this test run
        current_test_public_key = f"test_user_key"
        temp_user_id = await create_user(http_client, current_test_public_key)
        if not temp_user_id:
            print("Test aborted due to user creation failure.")
            return

    # Now use temp_user_id as the client_id for WebSocket
    user_id_for_ws = str(temp_user_id)
    print(f"ℹ️ Using created user's ID ({user_id_for_ws}) as WebSocket client_id.")

    print(f"\nConnecting to WebSocket at {WEBSOCKET_URL}/ws/{user_id_for_ws}...")
    try:
        async with websockets.connect(f"{WEBSOCKET_URL}/ws/{user_id_for_ws}") as ws:
            print(f"✅ WebSocket connected as client: {user_id_for_ws}")

            # --- Now, within the active WebSocket connection, create the post ---
            async with httpx.AsyncClient() as http_client:
                test_raw_text = f"This is an E2E test message for real-time sentiment analysis! Generated at {time.time()}."
                # Use the original user_id (temp_user_id) for the post creation
                post_id = await create_post(http_client, temp_user_id, test_raw_text)
                if not post_id:
                    print("Test aborted due to post creation failure.")
                    # Ensure the WebSocket connection is gracefully closed or handled
                    return
            # The HTTP client context for post creation ends here.

            # Now, wait for the WebSocket message
            print(f"Waiting for sentiment update message for post {post_id} (timeout: {WEBSOCKET_RECEIVE_TIMEOUT}s)...")

            try:
                start_time = asyncio.get_event_loop().time()
                while asyncio.get_event_loop().time() - start_time < WEBSOCKET_RECEIVE_TIMEOUT:
                    remaining_timeout = WEBSOCKET_RECEIVE_TIMEOUT - (asyncio.get_event_loop().time() - start_time)
                    if remaining_timeout <= 0:
                        break

                    message_str = await asyncio.wait_for(ws.recv(), timeout=remaining_timeout)
                    print(f"Received message: {message_str}...")
                    message_data = json.loads(message_str)
                    if message_data.get("type") == "post_sentiment_update" and \
                       message_data.get("post_id") == str(post_id) and \
                       message_data.get("user_id") == str(temp_user_id): # Check against the user_id from creation
                        received_message = message_data
                        print(f"✅ Received expected sentiment update for post {post_id}:")
                        print(json.dumps(received_message, indent=2))
                        break
                    else:
                        print(f"ℹ️ Received unexpected message type or post ID. Still waiting for target post.")

                if received_message:
                    print("\n--- Test PASSED: End-to-End flow verified! 🎉 ---")
                else:
                    print(f"\n❌ Test FAILED: Did not receive expected sentiment update for post {post_id} within {WEBSOCKET_RECEIVE_TIMEOUT} seconds.")

            except asyncio.TimeoutError:
                print(f"❌ Test FAILED: Timeout waiting for WebSocket message after {WEBSOCKET_RECEIVE_TIMEOUT} seconds.")
            except json.JSONDecodeError as e:
                print(f"❌ Test FAILED: Received non-JSON message or malformed JSON on WebSocket: {message_str}. Error: {e}")
            except Exception as e:
                print(f"❌ An unexpected error occurred while receiving WebSocket message: {e}")

    except websockets.exceptions.ConnectionClosedOK:
        print("ℹ️ WebSocket connection closed normally.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ WebSocket connection closed with error: {e}")
    except Exception as e:
        print(f"❌ Could not connect to WebSocket at {WEBSOCKET_URL}/ws/{user_id_for_ws}: {e}")

    print("\n--- Silhouet E2E Test Finished ---")

if __name__ == "__main__":
    asyncio.run(main())
