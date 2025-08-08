# 2. Data Flow

This document details the sequence of operations and data movement for the core user-facing features of the Silhouet application.

## 2.1 User Registration Flow

This flow describes how a new, anonymous identity is created. The primary design goal is to establish a user account without the server ever handling a password or private key.

```mermaid
sequenceDiagram
    participant User
    participant Frontend (React)
    participant Backend (FastAPI)
    participant Database (Postgres)

    User->>Frontend (React): Fills out registration form (demographics, passphrase)
    User->>Frontend (React): Clicks "Create Identity"
    
    activate Frontend (React)
    Frontend (React)->>Frontend (React): 1. Generate public/private key pair (NaCl)
    Frontend (React)->>Frontend (React): 2. Encrypt private key with passphrase
    Frontend (React)->>Frontend (React): 3. Store encrypted private key in browser's localStorage
    
    Frontend (React)->>Backend (FastAPI): 4. POST /users/ (sends public key + demographics)
    deactivate Frontend (React)
    
    activate Backend (FastAPI)
    Backend (FastAPI)->>Database (Postgres): 5. INSERT into `users` table (public_key, demographics, initial scores)
    
    activate Database (Postgres)
    Database (Postgres)-->>Backend (FastAPI): 6. Return new user record
    deactivate Database (Postgres)
    
    Backend (FastAPI)-->>Frontend (React): 7. Return {user_id, public_key, created_at}
    deactivate Backend (FastAPI)
    
    activate Frontend (React)
    Frontend (React)->>User: Displays success message with public key
    deactivate Frontend (React)
```

**Key Takeaways:**
*   The user's private key **never leaves the browser**.
*   The server only ever sees the public key, which acts as the user's identifier.
*   The user's ability to log in is tied to their passphrase and the specific browser/device where the encrypted key is stored.

## 2.2 User Login/Authentication Flow

This flow uses a challenge-response mechanism to verify the user's identity. This proves the user possesses the private key corresponding to their public key without ever transmitting the key itself.

```mermaid
sequenceDiagram
    participant User
    participant Frontend (React)
    participant Backend (FastAPI)
    participant Redis

    User->>Frontend (React): Enters public key and passphrase
    User->>Frontend (React): Clicks "Login"
    
    activate Frontend (React)
    Frontend (React)->>Frontend (React): 1. Decrypt private key from localStorage using passphrase
    Frontend (React)->>Backend (FastAPI): 2. POST /auth/challenge (sends public_key)
    deactivate Frontend (React)
    
    activate Backend (FastAPI)
    Backend (FastAPI)->>Backend (FastAPI): 3. Generate a secure, random challenge string
    Backend (FastAPI)->>Redis: 4. Store challenge with a 5-min expiry (key: `challenge:<public_key>`)
    
    activate Redis
    Redis-->>Backend (FastAPI): 5. Confirmation
    deactivate Redis
    
    Backend (FastAPI)-->>Frontend (React): 6. Return {challenge}
    deactivate Backend (FastAPI)
    
    activate Frontend (React)
    Frontend (React)->>Frontend (React): 7. Sign the challenge string with the decrypted private key
    Frontend (React)->>Backend (FastAPI): 8. POST /users/login (sends public_key, signature)
    deactivate Frontend (React)
    
    activate Backend (FastAPI)
    Backend (FastAPI)->>Redis: 9. Retrieve challenge for the public_key
    
    activate Redis
    Redis-->>Backend (FastAPI): 10. Return challenge
    deactivate Redis
    
    Backend (FastAPI)->>Backend (FastAPI): 11. Verify the signature against the public key and challenge
    alt Signature is valid
        Backend (FastAPI)->>Redis: 12. Delete the used challenge from Redis
        Backend (FastAPI)-->>Frontend (React): 13. Return user data to establish a session
    else Signature is invalid
        Backend (FastAPI)-->>Frontend (React): 13. Return 401 Unauthorized
    end
    deactivate Backend (FastAPI)
```

## 2.3 Post Submission and Scoring Flow

This flow is asynchronous to ensure the user gets a fast response, while the computationally intensive scoring happens in the background.

```mermaid
sequenceDiagram
    participant User
    participant Frontend (React)
    participant Backend (FastAPI)
    participant Celery Worker
    participant Model Service
    participant Database (Postgres)
    participant Redis

    User->>Frontend (React): Writes journal entry and clicks "Submit"
    
    activate Frontend (React)
    Frontend (React)->>Backend (FastAPI): 1. POST /posts/ (sends user_id, raw_text)
    deactivate Frontend (React)
    
    activate Backend (FastAPI)
    Backend (FastAPI)->>Database (Postgres): 2. INSERT into `posts` table (raw_text, user_id)
    Database (Postgres)-->>Backend (FastAPI): 3. Return new post_id
    
    Backend (FastAPI)->>Redis: 4. Enqueue `process_post_sentiment_task(post_id, raw_text)`
    Backend (FastAPI)-->>Frontend (React): 5. Return 201 Created (immediately)
    deactivate Backend (FastAPI)
    
    activate Celery Worker
    Celery Worker->>Redis: 6. Dequeue task
    Celery Worker->>Model Service: 7. POST /score (sends raw_text)
    
    activate Model Service
    Model Service->>Model Service: 8. Calculate ~53 personality scores
    Model Service-->>Celery Worker: 9. Return {scores}
    deactivate Model Service
    
    Celery Worker->>Database (Postgres): 10. UPDATE `posts` SET scores = {scores} WHERE id = post_id
    Celery Worker->>Database (Postgres): 11. GET user's current avg_scores and post_count
    Database (Postgres)-->>Celery Worker: 12. Return user data
    
    Celery Worker->>Celery Worker: 13. Recalculate user's running average scores
    Celery Worker->>Database (Postgres): 14. UPDATE `users` SET new avg_scores and increment post_count
    
    Celery Worker->>Redis: 15. PUBLISH score update to "sentiment_updates" channel
    deactivate Celery Worker
    
    Note over Backend (FastAPI), User: The backend's WebSocket listener receives the Redis message and pushes the update to the connected client.
```

### Implementation Notes & Future Improvements

*   **Post Authentication**: Currently, the `POST /posts/` endpoint identifies the user via the `user_id` in the request body. **Future Improvement**: This endpoint should be protected to ensure only the currently logged-in user can post on their own behalf. This involves checking for an active, authenticated session on the backend before accepting the post.
*   **Real-time Frontend Updates**: The frontend currently polls for score updates using a `setTimeout` after submitting a post. **Future Improvement**: The frontend will be updated to use a WebSocket listener to receive score updates pushed from the backend in real-time, providing a more responsive user experience. This work is planned for a later stage.
