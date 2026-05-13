import json
from redis.asyncio import Redis
from core.config import Configs
from typing import cast
configs = Configs()


class ConversationStore:
    def __init__(self):
        self.client: Redis = Redis(
            host=configs.REDIS_HOST,
            port=configs.REDIS_PORT,
            db=configs.REDIS_DB,
            password=configs.REDIS_PASSWORD,
            decode_responses=True,
        )
        self.MAX_MESSAGES = 20
        self.TTL = 60 * 60 * 24 * 7

    # Keys
    def _history_key(self, conversation_id: str) -> str:
        return f"conversation:{conversation_id}:history"

    def _summary_key(self, conversation_id: str) -> str:
        return f"conversation:{conversation_id}:summary"

    def _meta_key(self, conversation_id: str) -> str:
        return f"conversation:{conversation_id}:meta"

    # Messages
    def append_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        key = self._history_key(conversation_id)
        message = json.dumps({"role": role, "content": content})

        self.client.rpush(key, message)
        self.client.expire(key, self.TTL)
        self.client.ltrim(key, -self.MAX_MESSAGES, -1)

    def get_history(self, conversation_id: str) -> list[dict]:
        key = self._history_key(conversation_id)
        messages = self.client.lrange(key, 0, -1)

        if not messages:
            return []

        return [json.loads(message) for message in cast(list[str], messages)]

    def get_message_count(self, conversation_id: str) -> int:
        key = self._history_key(conversation_id)
        return cast(int, self.client.llen(key))

    # Summary
    async def save_summary(self, conversation_id: str, summary: str) -> None:
        """Store a compressed summary of old messages."""
        key = self._summary_key(conversation_id)
        await self.client.set(key, summary, ex=self.TTL)

    async def get_summary(self, conversation_id: str) -> str | None:
        """Retrieve the summary if it exists."""
        return await self.client.get(self._summary_key(conversation_id))

    # Meta
    def save_meta(self, conversation_id: str, user_id: str) -> None:
        """Store conversation metadata."""
        key = self._meta_key(conversation_id)
        self.client.hset(
            key,
            mapping={
                "user_id": user_id,
                "conversation_id": conversation_id,
            },
        )
        self.client.expire(key, self.TTL)

    def get_meta(self, conversation_id: str) -> dict | None:
        key = self._meta_key(conversation_id)
        meta = self.client.hgetall(key)
        return cast(dict | None, meta or None)

    # Cleanup
    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete all data for a conversation."""
        await self.client.delete(
            self._history_key(conversation_id),
            self._summary_key(conversation_id),
            self._meta_key(conversation_id),
        )

    async def close(self) -> None:
        await self.client.aclose()
        
    def reset_history(self, conversation_id: str, messages: list[dict]) -> None:
        """Replace history with a new set of messages."""
        key = self._history_key(conversation_id)
        self.client.delete(key)

        for msg in messages:
            self.append_message(conversation_id, msg["role"], msg["content"])
            