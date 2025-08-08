# backend/keymanager.py
import secrets
import json
import os
from typing import List

# The path to the file where keys are stored.
# It's placed within a mounted volume for persistence.
KEYS_FILE = '/keys/rotating_keys.json'
NUM_KEYS = 3  # The total number of keys to maintain in the rotation.

def generate_key() -> str:
    """Generates a new URL-safe secret key."""
    return secrets.token_urlsafe(32)

def read_keys() -> List[str]:
    """Reads the list of keys from the keys file."""
    if not os.path.exists(KEYS_FILE):
        return []
    with open(KEYS_FILE, 'r') as f:
        return json.load(f)

def write_keys(keys: List[str]):
    """Writes the list of keys to the keys file."""
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

def initialize_keys():
    """
    Generates the initial set of secret keys.
    This should be run once during the initial setup of the application.
    """
    if os.path.exists(KEYS_FILE):
        print(f"Key file already exists at {KEYS_FILE}. Initialization skipped.")
        return

    print(f"Initializing {NUM_KEYS} new secret keys...")
    keys = [generate_key() for _ in range(NUM_KEYS)]
    write_keys(keys)
    print(f"Successfully created {KEYS_FILE} with {NUM_KEYS} keys.")

def rotate_keys():
    """
    Rotates the secret keys.
    - The oldest key is removed.
    - A new key is generated and becomes the primary signing key.
    """
    keys = read_keys()
    if not keys:
        print("No keys found. Please initialize them first.")
        return

    print("Rotating keys...")
    # Remove the oldest key (at the end of the list)
    keys.pop()
    # Generate a new key and add it to the front of the list
    new_key = generate_key()
    keys.insert(0, new_key)
    
    write_keys(keys)
    print("Keys rotated successfully. The new primary key is ready.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Silhouet Key Management")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-parser for the 'init' command
    parser_init = subparsers.add_parser("init", help="Initialize the secret keys for the first time.")
    
    # Sub-parser for the 'rotate' command
    parser_rotate = subparsers.add_parser("rotate", help="Rotate the secret keys, retiring the oldest one.")

    args = parser.parse_args()

    if args.command == "init":
        initialize_keys()
    elif args.command == "rotate":
        rotate_keys()