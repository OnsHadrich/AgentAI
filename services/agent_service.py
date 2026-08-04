from repositories.conversation_repository import ConversationRepository
from repositories.user_repository import UserRepository
from modular_agentic_ai.agent.support_agent import run_agent, memory_manager
from schema.channel_schema import Channel
from sessions.session_manager import Session
from services.channel_service import ChannelService




class AgentService:
    def __init__(
        self,
        user_repository: UserRepository | None = None,
        conversation_repository: ConversationRepository | None = None,
        channel_service: ChannelService| None = None
      
    ):
        self.user_repository = user_repository or UserRepository()
        self.conv_repo = conversation_repository or ConversationRepository()
        self.channel_service = channel_service or ChannelService()

    async def start_conversation(self, user_id: str,conversation_id: str | None = None) -> str:
        """Creates a new conversation, returns conversation_id."""
        if conversation_id:
                meta = self.conv_repo.get(conversation_id)
                if meta:
                    return conversation_id
        conv = self.conv_repo.create(user_id)

        await memory_manager.init_conversation(
            conversation_id=conv.conversation_id,
            user_id=user_id
        )

        return conv.conversation_id

    async def reply(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        channel: str = Channel.APP,
        sender_name: str = "Customer",    
    ) -> str:
        """
        Process user message through the full agent pipeline.
        Supports both app (JWT users) and WhatsApp (phone number users).
        Channel is used to determine how to handle the user and conversation.
        """

        # ── Step 1: get or build user ─────────────────────────
        if channel == Channel.WHATSAPP:
            # WhatsApp users are not in DB — build a guest user
            user = self.user_repository._build_whatsapp_user(user_id)
            print(f"[AgentService] WhatsApp user: {user_id}")
        elif channel == Channel.INSTAGRAM:
                # Instagram users are not in DB — build a guest user
                user = self.user_repository._build_instagram_user(user_id)
                print(f"[AgentService] Instagram user: {user_id}")
        elif channel == Channel.MESSENGER:
                # Messenger users are not in DB — build a guest user
                user = self.user_repository._build_messenger_user(user_id)
                print(f"[AgentService] Messenger user: {user_id}")
        else:
            # App users must exist in DB
            user = self.user_repository.find_by_id(user_id)
            if not user:
                raise ValueError(f"User '{user_id}' not found.")
            print(f"[AgentService] App user: {user.name}")

        # ── Step 2: load existing summary ────────────────────
        existing_summary = self.conv_repo.get_summary(conversation_id)
        if existing_summary:
            print(f"[AgentService] Summary found for {conversation_id}")

        # ── Step 3: build session ─────────────────────────────
        session = Session(user=user)
        session.conversation_id = conversation_id

        # ── Step 4: run agent ─────────────────────────────────
        reply = await run_agent(session, user_message)

        return reply


   