import uuid
from model.conversation import Conversation, Message, Role
from modular_agentic_ai.memory.conversation_store import ConversationStore


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
        self.store.save_meta(conversation_id, user_id)  # ← MongoDB
        return conversation

    # ── Read ──────────────────────────────────────────────
    def get(self, conversation_id: str) -> Conversation | None:
        """Reconstruct a full Conversation object from MongoDB."""
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
            summary=summary
        )

    def exists(self, conversation_id: str) -> bool:
        """Check if a conversation exists."""
        return self.store.get_meta(conversation_id) is not None

    def get_history(self, conversation_id: str) -> list[dict]:
        """Get raw history formatted for LLM."""
        return self.store.get_history(conversation_id)

    def get_summary(self, conversation_id: str) -> str | None:   # ← sync now
        """Get the current summary if it exists."""
        return self.store.get_summary(conversation_id)

    # ── Write ─────────────────────────────────────────────
    def append_message(
        self, conversation_id: str, role: Role, content: str
    ) -> Message:
        """Add a message and return the domain Message object."""
        message = Message(role=role, content=content)
        self.store.append_message(
            conversation_id,
            role=role.value,
            content=content
        )
        return message

    def save_summary(self, conversation_id: str, summary: str) -> None:  # ← sync now
        """Persist a summary after compression."""
        self.store.save_summary(conversation_id, summary)

    # ── Delete ────────────────────────────────────────────
    def delete(self, conversation_id: str) -> None:              # ← sync now
        """Delete full conversation from MongoDB."""
        self.store.delete_conversation(conversation_id)

    # ── List ──────────────────────────────────────────────
    def get_all_by_user(self, user_id: str) -> list[str]:        # ← sync now
        """Get all conversation IDs for a user."""
        return self.store.get_all_by_user(user_id)

    def register_to_user(
        self, user_id: str, conversation_id: str
    ) -> None:
        """
        No longer needed — MongoDB meta already stores user_id.
        get_all_by_user queries by user_id directly.
        Kept for compatibility.
        """
        pass