# 1. Architecture Overview

The Silhouet platform is designed as a microservices-based architecture, containerized with Docker and orchestrated using Docker Compose. This design ensures scalability, separation of concerns, and maintainability.

Each service runs in its own container and communicates with others over a container network.

## Service Diagram

```
+-----------------+      +-----------------+      +--------------------+
|   Frontend      |----->|   Backend       |<---->|   PostgreSQL DB    |
| (React, Nginx)  |      | (FastAPI)       |      | (User/Post Data)   |
+-----------------+      +-------+---------+      +--------------------+
                             ^   |
                             |   |
                             |   v
+-----------------+      +---+---+---------+      +--------------------+
|   Model Service |<---->|   Celery Worker |----->|   Redis            |
| (SentenceTrans) |      | (Background     |      | (Broker, Cache)    |
+-----------------+      +-----------------+      +--------------------+
```

## Core Services

### 1. Frontend (`frontend/`)

*   **Technology**: React, TypeScript, Bootstrap.
*   **Server**: Nginx (for serving the static build).
*   **Role**: The user-facing single-page application (SPA). It is responsible for:
    *   Rendering the user interface for registration, login, journaling, and viewing scores.
    *   **Client-Side Cryptography**: Generating public/private key pairs (`nacl`), encrypting the private key with a user's passphrase, and storing it in the browser's local storage.
    *   Signing authentication challenges to prove identity without exposing the private key.
    *   Communicating with the backend via its REST API.

### 2. Backend (`backend/`)

*   **Technology**: FastAPI (Python).
*   **Role**: The central API gateway that orchestrates application logic. Its responsibilities include:
    *   Managing user registration and storing user metadata.
    *   Handling the challenge-response authentication flow.
    *   Receiving new journal entries (posts) from the frontend.
    *   Delegating heavy processing (like sentiment analysis) to the Celery worker to ensure fast API response times.
    *   Providing API endpoints for querying aggregated cohort scores.
    *   Managing WebSocket connections for real-time updates to the client.

### 3. Database (`db` in `docker-compose.yml`)

*   **Technology**: PostgreSQL.
*   **Role**: The primary data store for the application. It holds:
    *   The `users` table containing anonymized demographic data, public keys, and running average personality scores.
    *   The `posts` table containing the encrypted text of user entries and their corresponding scores once processed.

### 4. Redis (`redis` in `docker-compose.yml`)

*   **Technology**: Redis.
*   **Role**: Serves two critical functions:
    *   **Celery Broker**: Acts as the message broker for Celery, holding the queue of tasks to be processed by the worker.
    *   **Cache & Pub/Sub**: Caches temporary data like authentication challenges and serves as the Pub/Sub channel (`sentiment_updates`) for pushing real-time score updates from the worker back to the backend and then to the client.

### 5. Celery Worker (`worker/`)

*   **Technology**: Celery (Python).
*   **Role**: Executes long-running or resource-intensive tasks asynchronously in the background. Its main task is:
    *   `process_post_sentiment_task`: Picks up a new post from the Redis queue, calls the Model Service to get scores, updates the database with the scores, recalculates the user's running average scores, and publishes the result to the Redis Pub/Sub channel.

### 6. Model Service (`model/`)

*   **Technology**: FastAPI, Sentence-Transformers (Python).
*   **Role**: A dedicated microservice for running the machine learning model.
    *   It exposes a single `/score` endpoint that accepts text.
    *   It uses a pre-trained `all-mpnet-base-v2` model to generate a vector embedding for the input text.
    *   It calculates personality scores by comparing the text's embedding against pre-computed embeddings for positive and negative phrases associated with each personality trait.
    *   This service is stateless and can be scaled independently if scoring becomes a bottleneck.

### 7. Cron (`cron/`)

*   **Technology**: Cron (Linux utility).
*   **Role**: Designed for scheduled tasks. While the current implementation is minimal, it is intended to run periodic jobs like:
    *   Data aggregation for cohort analysis (e.g., pre-calculating daily averages by zipcode).
    *   Database cleanup or maintenance tasks.
