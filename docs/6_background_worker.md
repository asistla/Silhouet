# 6. Background Worker

The background worker is a crucial component for ensuring the application remains responsive. It offloads time-consuming tasks from the main backend API, processing them asynchronously.

## Core Technology

*   **Framework**: Celery
*   **Message Broker**: Redis

## Role in the Architecture

When a user submits a post, the backend API's primary responsibility is to acknowledge the request and store the post as quickly as possible. The actual analysis of the post is a slow process that should not block the user's experience.

The worker's flow is as follows:

1.  **Listens for Tasks**: The Celery worker process continuously monitors a task queue in Redis.
2.  **Dequeues a Task**: When the backend publishes a `process_post_sentiment_task`, the worker picks it up.
3.  **Executes the Task**: The worker performs a series of actions for each task:
    a.  Calls the **Model Service** to get the personality scores for the post's text.
    b.  Connects to the **PostgreSQL database** to save these scores to the corresponding `posts` table entry.
    c.  Retrieves the user's current average scores and total post count from the `users` table.
    d.  Calculates the new running average for each personality trait.
    e.  Updates the `users` table with the new averages and increments the `total_posts_count`.
    f.  Publishes the new scores to the `sentiment_updates` channel in **Redis**. This is the final step that triggers the real-time update to the user.

## Key Task

### `process_post_sentiment_task`

*   **Trigger**: Called by the backend's `/posts/` endpoint after a new post is created.
*   **Arguments**: `post_id` (str), `raw_text` (str).
*   **Function**: Orchestrates the entire post-processing pipeline as described in the flow above.

By delegating this entire sequence to the worker, the main backend API can respond to the user in milliseconds, confirming their post has been received, while the actual work happens in the background.
