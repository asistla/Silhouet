#!/bin/sh
# backend/entrypoint.sh

# This script runs every time the backend container starts.

# Define the path to the keys file
KEYS_FILE="/keys/rotating_keys.json"

# Check if the keys file already exists in the volume.
# If it doesn't, this is the first run (or the volume was cleared),
# so we need to initialize the keys.
if [ ! -f "$KEYS_FILE" ]; then
  echo "Keys file not found at $KEYS_FILE. Initializing keys..."
  python /app/keymanager.py init
else
  echo "Keys file found at $KEYS_FILE. Skipping initialization."
fi

# Execute the main container command (CMD)
# This starts the uvicorn server.
exec "$@"
