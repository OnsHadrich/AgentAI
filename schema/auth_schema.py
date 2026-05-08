from pydantic import BaseModel, EmailStr
from datetime import datetime


# ── Inbound ───────────────────────────────────────────────
class SignIn(BaseModel):
    email: EmailStr
    password: str

class SignUp(BaseModel):
    name: str
    email: EmailStr
    password: str
    tier: str


# ── JWT payload (what gets encoded in the token) ──────────
class Payload(BaseModel):
    id: str
    email: EmailStr
    name: str
    tier: str
    is_superuser: bool


# ── Outbound ──────────────────────────────────────────────
class SignInResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expiration: datetime
    user_id: str
    user_name: str
    tier: str

class SignOutResponse(BaseModel):
    message: str


# ── Session info (for /me and /sessions) ──────────────────
class SessionInfo(BaseModel):
    user_id: str
    user_name: str
    tier: str
    created_at: str
    last_active: str