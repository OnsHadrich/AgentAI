from agent.llm_client import LLMClient
from memory.conversation_store import ConversationStore


class MemoryManager:
    def __init__(
        self,
        store: ConversationStore | None = None,
        llm: LLMClient | None = None
    ):
        self.store = store or ConversationStore()
        self.llm = llm or LLMClient()
        self.SUMMARY_THRESHOLD = 15

    # ── Write ─────────────────────────────────────────────

    def add_user_message(self, conversation_id: str, content: str) -> None:
        self.store.append_message(conversation_id, "user", content)

    def add_assistant_message(self, conversation_id: str, content: str) -> None:
        self.store.append_message(conversation_id, "assistant", content)

    # ── Read ──────────────────────────────────────────────

    def get_history(self, conversation_id: str) -> list[dict]:
        return self.store.get_history(conversation_id)

    def get_context(self, conversation_id: str) -> str:
        """Plain string context for injecting into system prompt."""
        summary = self.store.get_summary(conversation_id)
        history = self.store.get_history(conversation_id)

        parts = []

        if summary:
            parts.append(f"[Previous Summary]\n{summary}")

        if history:
            parts.append("[Recent Messages]")
            for msg in history:
                label = "User" if msg["role"] == "user" else "Agent"
                parts.append(f"{label}: {msg['content']}")

        return "\n".join(parts) if parts else ""

    def build_langchain_messages(self, conversation_id: str) -> list[dict]:
        """Return history in LangChain format for ChatMessageHistory."""
        return self.store.get_history(conversation_id)

    def build_context(self, conversation_id: str) -> list[dict]:
        """Full message list: summary block + recent messages."""
        messages = []

        summary = self.store.get_summary(conversation_id)
        if summary:
            messages.append({
                "role": "user",
                "content": f"[Conversation summary so far]: {summary}"
            })
            messages.append({
                "role": "assistant",
                "content": "Understood, I have context from our previous discussion."
            })

        messages += self.store.get_history(conversation_id)
        return messages

    # ── Summarization ─────────────────────────────────────

    def should_summarize(self, conversation_id: str) -> bool:
        count =  self.store.get_message_count(conversation_id)
        return count >= self.SUMMARY_THRESHOLD

    async def summarize(self, conversation_id: str) -> None:
        """Compress old history into a summary, keep only last 4 messages."""
        history =  self.store.get_history(conversation_id)
        existing = await self.store.get_summary(conversation_id)

        to_summarize = history[:-4]
        to_keep = history[-4:]

        if not to_summarize:
            return

        prompt = f"""
        Summarize this customer support conversation concisely.
        Keep: key issues raised, decisions made, orders mentioned, promises made.

        Previous summary: {existing or 'None'}

        New messages:
        {self._format(to_summarize)}
        """
        new_summary = self.llm.invoke(prompt)   # LLMClient.invoke() is sync, returns str

        await self.store.save_summary(conversation_id, new_summary)
        self.store.reset_history(
            conversation_id=conversation_id,
            messages=to_keep
        )

    async def maybe_summarize(self, conversation_id: str) -> None:
        """Trigger summarization only when threshold is reached."""
        if self.should_summarize(conversation_id):
            await self.summarize(conversation_id)

    # ── Meta ──────────────────────────────────────────────

    def init_conversation(self, conversation_id: str, user_id: str) -> None:
        existing = self.store.get_meta(conversation_id)
        if not existing:
            self.store.save_meta(conversation_id, user_id)

    def get_conversation_meta(self, conversation_id: str) -> dict | None:
        return  self.store.get_meta(conversation_id)

    async def delete_conversation(self, conversation_id: str) -> None:
        await self.store.delete_conversation(conversation_id)

    # ── Helpers ───────────────────────────────────────────

    def _format(self, history: list[dict]) -> str:
        return "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in history
        ])