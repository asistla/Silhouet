# 4. Frontend Application

The frontend is a Single-Page Application (SPA) built with React and TypeScript. It is responsible for the entire user experience, from identity creation to data visualization.

## Core Technologies

*   **Framework**: React
*   **Language**: TypeScript
*   **Styling**: React-Bootstrap, custom CSS (`App.css`)
*   **Charting**: Chart.js
*   **Cryptography**: `tweetnacl` for key generation and signing, `crypto-js` for encrypting the private key.

## Component Structure

### `App.tsx`

This is the root component that manages the application's state and view logic.

*   **State Management**: It holds the primary state for the application, including:
    *   `user`: The currently logged-in user object (`{user_id, public_key}`).
    *   `view`: Controls which page is displayed (`'login'`, `'register'`, or `'dashboard'`).
    *   `userScores` & `cohortScores`: Stores the data for the personality charts.
    *   `filters`: Manages the state of the demographic filter inputs.
*   **Routing**: It acts as a simple router, conditionally rendering the `LoginPage`, `RegistrationPage`, or the main dashboard based on the `view` state.
*   **API Logic**: Contains all the `fetch` calls to the backend API for logging in, registering, submitting posts, and fetching scores.

### `LoginPage.tsx`

*   **Purpose**: Handles the user login process.
*   **Key Logic**:
    1.  Takes the user's public key and passphrase.
    2.  Retrieves the corresponding encrypted private key from the browser's `localStorage`.
    3.  Calls the `decryptPrivateKey` utility to decrypt the key with the provided passphrase.
    4.  Orchestrates the challenge-response flow: fetches a challenge from the backend, signs it using the decrypted key, and sends the signature back to log in.

### `RegistrationPage.tsx`

*   **Purpose**: Manages the creation of a new user identity.
*   **Key Logic**:
    1.  Collects demographic data and a user-created passphrase.
    2.  Uses `generateKeyPair` to create a new `nacl` public/private key pair.
    3.  Uses `encryptPrivateKey` to encrypt the new private key with the passphrase.
    4.  **Stores the encrypted private key in `localStorage`**. This is a critical step; the key is tied to the browser.
    5.  Sends the public key and demographic data to the backend to create the user record.

### `crypto.ts`

*   **Purpose**: A utility file that abstracts all client-side cryptographic operations.
*   **Functions**:
    *   `generateKeyPair()`: Creates a new key pair.
    *   `encryptPrivateKey()`: Encrypts a private key with a passphrase using AES.
    *   `decryptPrivateKey()`: Decrypts the private key.
    *   `signMessage()`: Signs a message (the challenge) with the private key.

## Real-time Updates

*   **Current Implementation**: After a user submits a post, the `App.tsx` component uses a `setTimeout` to wait for a fixed period (2 seconds) before re-fetching the user's scores. This is a simple polling mechanism.
*   **Future Improvement**: The plan is to replace this polling with a true real-time solution. The frontend will be updated to establish a WebSocket connection with the backend's `/ws/{client_id}` endpoint. A listener will be implemented to receive score updates pushed from the server, allowing the chart to update instantly after processing is complete without needing a manual refresh or delay.
