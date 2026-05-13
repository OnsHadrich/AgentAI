from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class Role(str, Enum):
    USER      = "user"
    ASSISTANT = "assistant"
    SYSTEM    = "system"

@dataclass
class Message:
    role: Role
    content: str
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )

@dataclass
class Conversation:
    conversation_id: str
    user_id: str
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )
    messages: list[Message] = field(default_factory=list)
    summary: str | None = None