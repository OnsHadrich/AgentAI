from enum import Enum
from pydantic import BaseModel


class Channel(str, Enum):
    APP       = "app"        # Mobile/Web
    WHATSAPP  = "whatsapp"
    INSTAGRAM = "instagram"
    MESSENGER = "messenger"


class ChannelMessage(BaseModel):
    user_id         : str
    conversation_id : str
    message         : str
    channel         : Channel
    sender_name     : str = "Customer"
    sender_avatar   : str | None = None