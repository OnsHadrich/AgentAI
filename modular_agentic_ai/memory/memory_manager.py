from modular_agentic_ai.agent.llm_client import LLMClient
from modular_agentic_ai.memory.conversation_store import ConversationStore


class MemoryManager:
    def __init__(
        self,
        store: ConversationStore | None = None,
        llm: LLMClient | None = None
    ):
        self.store = store or ConversationStore()
        self.llm = llm or LLMClient()
        self.SUMMARY_THRESHOLD = 5  # number of messages before summarization

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
        history = self.store.get_history(conversation_id)

        parts = []

        if history:
            parts.append("[Recent Messages]")
            for msg in history:
                label = "User" if msg["role"] == "user" else "Agent"
                parts.append(f"{label}: {msg['content']}")

        return "\n".join(parts) if parts else ""
    def get_summary(self, conversation_id: str) -> str | None:
        """Get the current summary for this conversation"""
        return self.store.get_summary(conversation_id)
    
    # ── Build ──────────────────────────────────────────────

    def build_langchain_messages(self, conversation_id: str) -> list[dict]:
        """Return history in LangChain format for ChatMessageHistory."""
        return self.store.get_history(conversation_id)

    def build_context(self, conversation_id: str) -> list[dict]:
        """Full message list: summary (if exists) + recent history."""
        messages = []
        summary = self.get_summary(conversation_id)
        
        if summary:
            messages.append({"role": "user", "content": f"Summary of conversation so far: {summary}"})
            messages.append({
                "role": "assistant",
                "content": "Understood, I have context from our previous discussion."
            })
        messages += self.store.get_history(conversation_id)


        return messages

    # ── Summarization ─────────────────────────────────────

    def should_summarize(self, conversation_id: str) -> bool:
        count = self.store.get_message_count(conversation_id)
        return count >= self.SUMMARY_THRESHOLD

    def save_summary(self, conversation_id: str) -> None:
            """Save summary after every reply — always runs."""
            history = self.store.get_history(conversation_id)

            if not history:
                return

            existing = self.store.get_summary(conversation_id)

            if existing:
                prompt = f"""
    You are summarizing an ongoing customer support conversation.

    Previous summary:
    {existing}

    New messages to incorporate:
    {self._format(history)}

    Update the summary concisely (max 200 words).
    Focus on: what was asked, what was resolved, open issues, orders mentioned.
    Do not repeat what is already in the previous summary unless updated.
    """
            else:
                prompt = f"""
    You are summarizing a customer support conversation.

    Messages:
    {self._format(history)}

    Write a concise summary (max 200 words).
    Focus on: what was asked, what was resolved, open issues, orders mentioned.
    """

            try:
                new_summary = self.llm.invoke(prompt)
                self.store.save_summary(conversation_id, new_summary)
                print(f"[MemoryManager] summary saved ✓")
                print(f"[MemoryManager] preview: {new_summary[:100]}...")
            except Exception as e:
                print(f"[MemoryManager] save_summary_now ERROR: {e}")

    async def summarize(self, conversation_id: str) -> None:
        """Compress old history into a summary, keep only last 4 messages."""
        history = self.store.get_history(conversation_id)
        existing = self.store.get_summary(conversation_id)

        to_summarize = history[:-4]
        to_keep = history[-4:]

        if not to_summarize:
            return
        if existing:
            prompt = f"""
        You are summarizing an ongoing customer support conversation.

        Previous summary:
        {existing}

        New messages to add:
        {self._format(to_summarize)}

        Update the summary concisely (max 200 words).
        Focus on: what was asked, what was resolved, open issues, orders mentioned.
        """
        else:
            prompt = f"""
            Summarize this customer support conversation concisely.
            Keep: key issues raised, decisions made, orders mentioned, promises made.

            Previous summary: {existing or 'None'}

            New messages:
            {self._format(to_summarize)}
            Focus on: what was asked, what was resolved, open issues, orders mentioned.
            """
        new_summary = self.llm.invoke(prompt)

        self.store.save_summary(conversation_id, new_summary)
        self.store.reset_history(
            conversation_id=conversation_id,
            messages=to_keep
        )
        print(f"[MemoryManager] summary saved ✓ ({len(to_summarize)} messages compressed)")


    async def maybe_summarize(self, conversation_id: str) -> None:
        """Trigger summarization only when threshold is reached."""
        if self.should_summarize(conversation_id):
            await self.summarize(conversation_id)
        else:
            self.save_summary(conversation_id)

    # ── Meta ──────────────────────────────────────────────

    async def init_conversation(self, conversation_id: str, user_id: str) -> None:
        existing = self.store.get_meta(conversation_id)
        if not existing:
            self.store.save_meta(conversation_id, user_id)

    async def delete_conversation(self, conversation_id: str) -> None:
        self.store.delete_conversation(conversation_id)

    # ── Helpers ───────────────────────────────────────────

    def _format(self, history: list[dict]) -> str:
        return "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in history
        ])