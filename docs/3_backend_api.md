# 3. Backend API Reference

The backend is a FastAPI application that serves as the primary interface for the frontend and orchestrates the core application logic.

**Base URL**: `/api` (as configured in the frontend proxy)

## Authentication Endpoints

### `POST /auth/challenge`

*   **Description**: Initiates the login process by generating a unique, temporary challenge for a user to sign.
*   **Request Body**: `ChallengeRequest`
    ```json
    {
      "public_key": "string"
    }
    ```
*   **Response (200 OK)**: `ChallengeResponse`
    ```json
    {
      "challenge": "string"
    }
    ```
*   **Details**: The generated challenge is stored in Redis with a 5-minute expiry. This endpoint is the first step in the secure challenge-response authentication flow.

### `POST /users/login`

*   **Description**: Authenticates a user by verifying a signed challenge.
*   **Request Body**: `UserLogin`
    ```json
    {
      "public_key": "string",
      "signature": "string"
    }
    ```
*   **Response (200 OK)**: `UserResponse`
    ```json
    {
      "user_id": "uuid",
      "public_key": "string",
      "created_at": "datetime"
    }
    ```
*   **Response (401 Unauthorized)**: If the signature is invalid or the challenge has expired.
*   **Details**: This is the second step of authentication. The backend retrieves the original challenge from Redis, verifies the provided signature against the user's public key, and, if successful, deletes the challenge to prevent reuse.

## User Endpoints

### `POST /users/`

*   **Description**: Creates a new user account.
*   **Request Body**: `UserCreate` (includes `public_key` and all optional demographic fields).
*   **Response (201 Created)**: `UserCreateResponse`
    ```json
    {
      "user_id": "uuid",
      "public_key": "string",
      "created_at": "datetime"
    }
    ```
*   **Response (400 Bad Request)**: If the public key is already registered.

### `GET /users/{user_id}`

*   **Description**: Retrieves basic information for a single user.
*   **Path Parameter**: `user_id` (UUID).
*   **Response (200 OK)**: `UserResponse`.
*   **Response (404 Not Found)**: If the user does not exist.

## Post Endpoints

### `POST /posts/`

*   **Description**: Creates a new journal post and queues it for sentiment analysis.
*   **Request Body**: `PostCreate`
    ```json
    {
      "user_id": "uuid",
      "raw_text": "string",
      "category": "string"
    }
    ```
*   **Response (201 Created)**: `PostResponse` (contains the new post's ID and data, but scores will be null initially).
*   **Security Note**: Currently, this endpoint relies on the `user_id` provided in the body. The intended design is to protect this endpoint and derive the `user_id` from the authenticated user's session. This is a planned future improvement.

### `GET /users/{user_id}/posts`

*   **Description**: Retrieves a list of all posts made by a specific user.
*   **Path Parameter**: `user_id` (UUID).
*   **Query Parameters**: `skip` (int, default 0), `limit` (int, default 100).
*   **Response (200 OK)**: `List[PostResponse]`.

## Score Endpoints

### `GET /scores/{public_key}`

*   **Description**: Retrieves the most recent, up-to-date running average personality scores for a specific user, identified by their public key.
*   **Path Parameter**: `public_key` (string).
*   **Response (200 OK)**: A JSON object where keys are `avg_<personality_key>_score` and values are the corresponding scores (float).
*   **Response (404 Not Found)**: If the user does not exist.

### `POST /scores/filtered`

*   **Description**: Calculates and returns the average personality scores for a cohort of users matching a set of demographic filters.
*   **Request Body**: `FilteredScoresRequest` (all fields are optional).
*   **Response (200 OK)**: A JSON object of average scores for the matching cohort.
*   **Response (404 Not Found)**: If no users match the specified criteria.

## WebSocket Endpoint

### `WS /ws/{client_id}`

*   **Description**: Establishes a WebSocket connection for real-time communication.
*   **Path Parameter**: `client_id` (string, typically the user's public key or a unique session ID).
*   **Functionality**: Once a connection is established, the backend can push messages to the client. This is used to send real-time score updates after a post has been processed by the background worker. The backend listens on a Redis Pub/Sub channel for these updates and forwards them to the appropriate client via this WebSocket.
