import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import JWTError, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis

from core.config import Configs

load_dotenv()

configs = Configs()
JWT_SECRET = configs.JWT_SECRET
JWT_ALGORITHM = configs.JWT_ALGORITHM
JWT_EXPIRE_MINUTES = configs.JWT_EXPIRE_MINUTES

# ── Redis connection ───────────────────────────────────────
redis_client: Redis = Redis(
    host=configs.REDIS_HOST,
    port=configs.REDIS_PORT,
    db=configs.REDIS_DB,
    username=os.getenv("REDIS_USERNAME", None),
    password=configs.REDIS_PASSWORD,
    decode_responses=True  # returns str instead of bytes
)

bearer_scheme = HTTPBearer()

# ── JWT Utility Functions ───────────────────────────────────────
def create_token(user_id: str, user_name: str, tier: str) -> str:
    """Generate a JWT token for a logged-in user."""
    payload = {
        "sub": user_id,
        "name": user_name,
        "tier": tier,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    # Check blacklist in Redis
    if redis_client.exists(f"blacklist:{token}"):
        raise HTTPException(status_code=401, detail="Token has been revoked. Please login again.")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")


def blacklist_token(token: str):
    """Invalidate a token on logout — auto-expires with the token itself."""
    try:
        # Decode without blacklist check to get expiry
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        exp = payload.get("exp")
        if exp is not None:
            ttl = int(exp - datetime.utcnow().timestamp())
            if ttl > 0:
                redis_client.setex(f"blacklist:{token}", ttl, "1")
    except JWTError:
        pass


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> dict:
    """FastAPI dependency — extracts and validates token from Authorization header."""
    token = credentials.credentials
    payload = decode_token(token)
    return {
        "user_id": payload.get("sub"),
        "user_name": payload.get("name"),
        "tier": payload.get("tier"),
        "token": token
    }
