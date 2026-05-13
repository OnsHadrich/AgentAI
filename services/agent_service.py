from repositories.conversation_repository import ConversationRepository
from repositories.user_repository import UserRepository
from modular_agentic_ai.agent.support_agent import run_agent, memory_manager
from sessions.session_manager import Session


class AgentService:
    def __init__(self):
        self.conv_repo = ConversationRepository()
        self.user_repo = UserRepository()

    def start_conversation(self, user_id: str) -> str:
        """Creates a new conversation, returns conversation_id."""
        conv = self.conv_repo.create(user_id)

        memory_manager.init_conversation(
            conversation_id=conv.conversation_id,
            user_id=user_id
        )

        return conv.conversation_id

    async def reply(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str
    ) -> str:
        """Process user message through the full agent pipeline."""

        # ── Step 1: get user ──────────────────────────────
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError(f"User '{user_id}' not found.")

        # ── Step 2: build session ─────────────────────────
        session = Session(user=user)
        session.conversation_id = conversation_id

        # ── Step 3: run agent (handles memory + tools + LLM)
        reply = await run_agent(session, user_message)

        return reply