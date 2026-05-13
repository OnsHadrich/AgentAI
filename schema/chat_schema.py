from pydantic import BaseModel
from typing import Literal




class ChatRequest(BaseModel):
    message: str               


class ChatResponse(BaseModel):
    user_id: str
    user_name: str
    response: str


class SessionInfo(BaseModel):
    user_id: str
    user_name: str
    tier: str
    created_at: str
    last_active: str


