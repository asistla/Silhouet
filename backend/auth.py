# backend/auth.py
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from jose import JWTError, jwt
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# The path to the file where keys are stored, consistent with keymanager.py and docker-compose.yml
KEYS_FILE = '/keys/rotating_keys.json'
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def get_keys() -> List[str]:
    """Reads the list of valid keys from the keys file."""
    try:
        with open(KEYS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is empty/corrupt, we cannot proceed.
        # The entrypoint script should prevent this, but this is a safeguard.
        raise RuntimeError("Could not load secret keys. The key file is missing or invalid.")

class TokenData(BaseModel):
    sub: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Always sign with the newest key (the first one in the list)
    keys = get_keys()
    if not keys:
        raise RuntimeError("No secret keys available for signing.")
    signing_key = keys[0]
    
    encoded_jwt = jwt.encode(to_encode, signing_key, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    # Get all valid keys for verification
    valid_keys = get_keys()
    if not valid_keys:
        raise credentials_exception

    last_exception = None
    for key in valid_keys:
        try:
            payload = jwt.decode(token, key, algorithms=[ALGORITHM])
            public_key: str = payload.get("sub")
            if public_key is None:
                # This case should ideally not be hit if the token was signed correctly
                continue 
            return TokenData(sub=public_key)
        except JWTError as e:
            # Store the exception but continue to try other keys
            last_exception = e
            continue
    
    # If the loop completes without returning, it means no key worked.
    # We raise the original credentials_exception for consistency,
    # but you could also raise the last_exception for more specific debugging.
    raise credentials_exception
