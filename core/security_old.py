from datetime import datetime, timedelta, timezone
from typing import Any, Tuple
from fastapi import HTTPException
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import Configs
from core.exceptions import AuthError
from redis.asyncio import Redis
import bcrypt

configs = Configs()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_ALGORITHM = configs.JWT_ALGORITHM


# ── Redis ──────────────────────────────────────────────────
# redis_client: Redis = Redis(
#     host=configs.REDIS_HOST,
#     port=configs.REDIS_PORT,
#     db=configs.REDIS_DB,
#     password=configs.REDIS_PASSWORD,
#     decode_responses=True
# )

# ── Bearer scheme ──────────────────────────────────────────
class JWTBearer(HTTPBearer): 
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials | None = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise AuthError(detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise AuthError(detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise AuthError(detail="Invalid authorization code.")

    def verify_jwt(self, token: str) -> bool:
        try:
            jwt.decode(token, configs.JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return True
        except JWTError:
            return False

# ── Token creation ─────────────────────────────────────────
def create_access_token(subject: dict[str, Any], expires_delta: timedelta | None = None) -> Tuple[str, datetime]:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=configs.JWT_EXPIRE_MINUTES)
    )
    payload = {"exp": expire, **subject}
    token = jwt.encode(payload, configs.JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expire


# ── Token validation ───────────────────────────────────────
async def decode_token(token: str) -> dict:
    # if await redis_client.exists(f"blacklist:{token}"):
        # raise HTTPException(status_code=401, detail="Token has been revoked.")
    try:
        return jwt.decode(token, configs.JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")


# # ── Token blacklist ────────────────────────────────────────
# async def blacklist_token(token: str):
#     try:
#         payload = jwt.decode(token, configs.JWT_SECRET, algorithms=[JWT_ALGORITHM])
#         exp = payload.get("exp")
#         if exp:
#             ttl = int(exp - datetime.now(timezone.utc).timestamp())
#             if ttl > 0:
#                 # await redis_client.setex(f"blacklist:{token}", ttl, "1")
#     # except JWTError:
#     #     pass


# ── Password hashing ───────────────────────────────────────


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())