import uuid
from model.conversation import Conversation, Message, Role
from modular_agentic_ai.memory.conversation_store import ConversationStore
from typing import cast, Coroutine, Any

class ConversationRepository:
    def __init__(self, store: ConversationStore | None = None):
        self.store = store or ConversationStore()

    # ── Create ────────────────────────────────────────────
    def create(self, user_id: str) -> Conversation:
        """Start a new conversation."""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        # persist meta to Redis
        self.store.save_meta(conversation_id, user_id)
        return conversation

    # ── Read ──────────────────────────────────────────────
    def get(self, conversation_id: str) -> Conversation | None:
        """Reconstruct a full Conversation object from Redis."""
        meta = self.store.get_meta(conversation_id)
        if not meta:
            return None

        messages = [
            Message(
                role=Role(m["role"]),
                content=m["content"],
                created_at=m.get("created_at", "")
            )
            for m in self.store.get_history(conversation_id)
        ]

        summary = self.store.get_summary(conversation_id)

        return Conversation(
            conversation_id=meta["conversation_id"],
            user_id=meta["user_id"],
            created_at=meta.get("created_at", ""),
            messages=messages,
            summary= cast(str, summary)
        )

    def exists(self, conversation_id: str) -> bool:
        """Check if a conversation exists."""
        return self.store.get_meta(conversation_id) is not None

    def get_history(self, conversation_id: str) -> list[dict]:
        """Get raw history formatted for LLM — used by agent service."""
        return self.store.get_history(conversation_id)

    async def get_summary(self, conversation_id: str) -> str | None:
        """Get the current summary if it exists."""
        return await self.store.get_summary(conversation_id)

    # ── Write ─────────────────────────────────────────────
    def append_message(self, conversation_id: str, role: Role, content: str) -> Message:
        """Add a message and return the domain Message object."""
        message = Message(role=role, content=content)
        self.store.append_message(
            conversation_id,
            role=role.value,
            content=content
        )
        return message

    async def save_summary(self, conversation_id: str, summary: str):
        """Persist a summary after compression."""
        await self.store.save_summary(conversation_id, summary)

    # ── Delete ────────────────────────────────────────────
    async def delete(self, conversation_id: str):
        """Delete full conversation from Redis."""
        await self.store.delete_conversation(conversation_id)

    # ── List ──────────────────────────────────────────────


    async def get_all_by_user(self, user_id: str) -> list[str]:
        key = f"user:{user_id}:conversations"
        result = await cast(Coroutine[Any, Any, list[str]], self.store.client.lrange(key, 0, -1))
        return result or []

    def register_to_user(self, user_id: str, conversation_id: str):
        """Index conversation under the user for lookup."""
        key = f"user:{user_id}:conversations"
        self.store.client.rpush(key, conversation_id)
        self.store.client.expire(key, self.store.TTL)