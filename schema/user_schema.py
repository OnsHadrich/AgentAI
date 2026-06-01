from pydantic import BaseModel, EmailStr

# What the CLIENT SENDS
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# What the SERVER RETURNS
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    user_name: str
    tier: str
    message: str
    # ← no password_hash, no internal fields
    
class SessionInfo(BaseModel):
    user_id: str
    user_name: str
    tier: str
    created_at: str
    last_active: str

class LogoutRequest(BaseModel):
    email: EmailStr
    
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    tier: str
    
class RegisterResponse(BaseModel):
    user_id: str
    user_name: str
    email: EmailStr
    tier: str
    message: str