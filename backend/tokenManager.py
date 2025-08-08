import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
from dataclasses import dataclass
from fastapi import HTTPException, status
import json
import os

@dataclass
class JWTKey:
    key_id: str
    secret: str
    created_at: datetime
    is_active: bool = True

class JWTKeyManager:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.key_prefix = "jwt_keys"
        self.current_key_id = None
        
    async def initialize_keys(self):
        """Initialize with first key if none exist"""
        keys = await self.get_all_keys()
        if not keys:
            await self.rotate_key()
        else:
            # Find the most recent active key
            active_keys = {k: v for k, v in keys.items() if v.is_active}
            if active_keys:
                self.current_key_id = max(active_keys.keys(), 
                                        key=lambda k: active_keys[k].created_at)
            else:
                await self.rotate_key()
    
    async def get_all_keys(self) -> Dict[str, JWTKey]:
        """Retrieve all keys from Redis"""
        keys = {}
        key_pattern = f"{self.key_prefix}:*"
        
        async for key in self.redis_client.scan_iter(match=key_pattern):
            key_data = await self.redis_client.get(key)
            if key_data:
                data = json.loads(key_data)
                key_id = key.decode().split(':')[1]
                keys[key_id] = JWTKey(
                    key_id=key_id,
                    secret=data['secret'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    is_active=data['is_active']
                )
        return keys
    
    async def get_key(self, key_id: str) -> Optional[JWTKey]:
        """Get a specific key by ID"""
        key_data = await self.redis_client.get(f"{self.key_prefix}:{key_id}")
        if not key_data:
            return None
            
        data = json.loads(key_data)
        return JWTKey(
            key_id=key_id,
            secret=data['secret'],
            created_at=datetime.fromisoformat(data['created_at']),
            is_active=data['is_active']
        )
    
    async def store_key(self, jwt_key: JWTKey):
        """Store a key in Redis"""
        key_data = {
            'secret': jwt_key.secret,
            'created_at': jwt_key.created_at.isoformat(),
            'is_active': jwt_key.is_active
        }
        await self.redis_client.set(
            f"{self.key_prefix}:{jwt_key.key_id}", 
            json.dumps(key_data),
            # Keep keys for 60 days after creation (longer than any token could live)
            ex=60 * 24 * 60 * 60  
        )
    
    async def rotate_key(self) -> str:
        """Create a new signing key and mark it as current"""
        # Generate new key
        new_key_id = f"key_{int(datetime.now(timezone.utc).timestamp())}"
        new_secret = secrets.token_urlsafe(32)
        
        new_key = JWTKey(
            key_id=new_key_id,
            secret=new_secret,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        # Store the new key
        await self.store_key(new_key)
        self.current_key_id = new_key_id
        
        # Clean up old keys (deactivate keys older than 30 days)
        await self.cleanup_old_keys()
        
        print(f"Created new JWT signing key: {new_key_id}")
        return new_key_id
    
    async def cleanup_old_keys(self):
        """Deactivate keys older than 30 days but keep them for verification"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        keys = await self.get_all_keys()
        
        for key_id, jwt_key in keys.items():
            if jwt_key.created_at < cutoff_date and jwt_key.is_active:
                jwt_key.is_active = False
                await self.store_key(jwt_key)
                print(f"Deactivated old key: {key_id}")
    
    async def get_current_key(self) -> JWTKey:
        """Get the current signing key"""
        if not self.current_key_id:
            await self.initialize_keys()
            
        current_key = await self.get_key(self.current_key_id)
        if not current_key or not current_key.is_active:
            # Current key is invalid, rotate
            await self.rotate_key()
            current_key = await self.get_key(self.current_key_id)
            
        return current_key

# Global key manager instance
key_manager = None

def get_key_manager(redis_client) -> JWTKeyManager:
    global key_manager
    if key_manager is None:
        key_manager = JWTKeyManager(redis_client)
    return key_manager

async def create_access_token(data: dict, redis_client, expires_delta: Optional[timedelta] = None):
    """Create a JWT token with the current signing key"""
    manager = get_key_manager(redis_client)
    current_key = await manager.get_current_key()
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "your-app-name"  # Add your app identifier
    })
    
    # Include key ID in header
    headers = {"kid": current_key.key_id}
    
    encoded_jwt = jwt.encode(
        to_encode, 
        current_key.secret, 
        algorithm="HS256",
        headers=headers
    )
    return encoded_jwt

async def verify_token(token: str, redis_client, credentials_exception):
    """Verify a JWT token using the appropriate key"""
    try:
        # Get key ID from token header
        unverified_header = jwt.get_unverified_header(token)
        key_id = unverified_header.get("kid")
        
        manager = get_key_manager(redis_client)
        
        if key_id:
            # Try to verify with the specified key
            jwt_key = await manager.get_key(key_id)
            if jwt_key:
                try:
                    payload = jwt.decode(
                        token, 
                        jwt_key.secret, 
                        algorithms=["HS256"]
                    )
                    public_key: str = payload.get("sub")
                    if public_key is None:
                        raise credentials_exception
                    return TokenData(sub=public_key)
                except jwt.ExpiredSignatureError:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired"
                    )
                except jwt.JWTError:
                    pass  # Try other keys
        
        # Fallback: try all active keys (for tokens without kid header)
        all_keys = await manager.get_all_keys()
        for jwt_key in all_keys.values():
            if not jwt_key.is_active:
                continue
                
            try:
                payload = jwt.decode(
                    token, 
                    jwt_key.secret, 
                    algorithms=["HS256"]
                )
                public_key: str = payload.get("sub")
                if public_key is None:
                    raise credentials_exception
                return TokenData(sub=public_key)
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            except jwt.JWTError:
                continue
                
        raise credentials_exception
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise credentials_exception

# Background task for key rotation (optional - can also be done via cron)
async def periodic_key_rotation(redis_client):
    """Background task to rotate keys periodically"""
    manager = get_key_manager(redis_client)
    
    while True:
        try:
            # Check if current key is older than 7 days
            current_key = await manager.get_current_key()
            age = datetime.now(timezone.utc) - current_key.created_at
            
            if age > timedelta(days=7):  # Rotate weekly
                await manager.rotate_key()
                print("Automatic key rotation completed")
            
            # Sleep for 24 hours
            await asyncio.sleep(24 * 60 * 60)
            
        except Exception as e:
            print(f"Error in periodic key rotation: {e}")
            await asyncio.sleep(60 * 60)  # Wait 1 hour before retrying
