
from core.config import Configs
from model.user_model import User
from schema.channel_schema import Channel
from schema.channel_schema import Channel

configs = Configs()


class ChannelService:
    """
    Handles user identity across all channels.
    App users → DB lookup
    WhatsApp/Instagram/Messenger → guest user
    """

    def build_user(
        self,
        user_id     : str,
        channel     : Channel,
        sender_name : str = "Customer"
    ) -> User | None:
        """
        Build or fetch user based on channel.
        """
        if channel == Channel.APP:
            return None   # ← AgentService will fetch from DB

        return self._build_guest_user(
            user_id=user_id,
            channel=channel,
            name=sender_name
        )

    def _build_guest_user(
        self,
        user_id : str,
        channel : str,
        name    : str = "Customer"
    ) -> User:
        """
        Build a guest User for social channel users.
        They don't exist in DB — identified by platform ID.
        """
        clean_id = (
            user_id
            .replace("whatsapp:", "")
            .replace("+", "")
            .strip()
        )

        # assign tier based on channel
        tier_map = {
            "whatsapp" : "standard",
            "instagram": "standard",
            "messenger": "standard",
        }

        return User(
            user_id      = f"{channel}_{clean_id}",
            name         = name,
            email        = "None",  # ← no email available for social users
            tier         = tier_map.get(channel, "standard"),
            is_active    = True,
            is_superuser = False,
            password_hash= "",
            password     = ""
        )