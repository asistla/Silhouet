# backend/auth.py
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from jose import JWTError, jwt
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Local imports are now needed here
from database import get_db
from crud import users
from models import User

load_dotenv()

KEYS_FILE = '/keys/rotating_keys.json'
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_keys() -> List[str]:
    """Reads the list of valid keys from the keys file."""
    try:
        with open(KEYS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
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
    
    keys = get_keys()
    if not keys:
        raise RuntimeError("No secret keys available for signing.")
    signing_key = keys[0]
    
    encoded_jwt = jwt.encode(to_encode, signing_key, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    valid_keys = get_keys()
    if not valid_keys:
        raise credentials_exception

    last_exception = None
    for key in valid_keys:
        try:
            payload = jwt.decode(token, key, algorithms=[ALGORITHM])
            public_key: str = payload.get("sub")
            if public_key is None:
                continue 
            return TokenData(sub=public_key)
        except JWTError as e:
            last_exception = e
            continue
    
    raise credentials_exception

# --- User and Role Dependencies ---

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Dependency to get the current user from a token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token, credentials_exception)
    user = users.get_user_by_public_key(db, public_key=token_data.sub)
    if user is None:
        raise credentials_exception
    return user

class RoleChecker:
    """
    Dependency factory to check for user roles.
    Usage: `Depends(RoleChecker(['admin', 'advertiser']))`
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {', '.join(self.allowed_roles)}."
            )
        return current_user
