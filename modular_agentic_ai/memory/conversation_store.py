from datetime import datetime
from pymongo import ASCENDING
from pymongo.collection import Collection
from database.mongodb import MongoDB


class ConversationStore:
    MAX_MESSAGES = 20

    def _messages(self) -> Collection:
        return MongoDB.get_db()["conversation_messages"]

    def _summaries(self) -> Collection:
        return MongoDB.get_db()["conversation_summaries"]

    def _meta(self) -> Collection:
        return MongoDB.get_db()["conversation_meta"]

    def create_indexes(self):
        """Call once on startup to create indexes."""
        self._messages().create_index([("conversation_id", ASCENDING)])
        self._summaries().create_index([("conversation_id", ASCENDING)], unique=True)
        self._meta().create_index([("conversation_id", ASCENDING)], unique=True)
        self._meta().create_index([("user_id", ASCENDING)])
        print("MongoDB indexes created ✓")

    # ── Messages ──────────────────────────────────────────

    def append_message(
        self, conversation_id: str, role: str, content: str
    ) -> None:
        """Add a message and trim to MAX_MESSAGES."""
        self._messages().insert_one({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow()
        })
        self._trim(conversation_id)

    def _trim(self, conversation_id: str) -> None:
        """Keep only the last MAX_MESSAGES messages."""
        messages = list(
            self._messages()
            .find({"conversation_id": conversation_id})
            .sort("created_at", ASCENDING)
        )

        if len(messages) > self.MAX_MESSAGES:
            to_delete = messages[:len(messages) - self.MAX_MESSAGES]
            ids = [m["_id"] for m in to_delete]
            self._messages().delete_many({"_id": {"$in": ids}})

    def get_history(self, conversation_id: str) -> list[dict]:
        """Get all messages for a conversation."""
        messages = self._messages().find(
            {"conversation_id": conversation_id},
            {"_id": 0, "role": 1, "content": 1}   # ← exclude _id
        ).sort("created_at", ASCENDING)

        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def get_message_count(self, conversation_id: str) -> int:
        return self._messages().count_documents(
            {"conversation_id": conversation_id}
        )

    def reset_history(
        self, conversation_id: str, messages: list[dict]
    ) -> None:
        """Replace entire history with a new list."""
        self._messages().delete_many({"conversation_id": conversation_id})

        if messages:
            self._messages().insert_many([
                {
                    "conversation_id": conversation_id,
                    "role": msg["role"],
                    "content": msg["content"],
                    "created_at": datetime.utcnow()
                }
                for msg in messages
            ])

    # ── Summary ───────────────────────────────────────────

    def save_summary(self, conversation_id: str, summary: str) -> None:
        """Store or update the summary."""
        self._summaries().update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "summary": summary,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True   # ← insert if not exists, update if exists
        )

    def get_summary(self, conversation_id: str) -> str | None:
        """Retrieve the summary if it exists."""
        doc = self._summaries().find_one(
            {"conversation_id": conversation_id},
            {"_id": 0, "summary": 1}
        )
        return doc["summary"] if doc else None

    # ── Meta ──────────────────────────────────────────────

    def save_meta(self, conversation_id: str, user_id: str) -> None:
        """Store conversation metadata."""
        self._meta().update_one(
            {"conversation_id": conversation_id},
            {
                "$setOnInsert": {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True   
        )

    def get_meta(self, conversation_id: str) -> dict | None:
        """Retrieve conversation metadata."""
        doc = self._meta().find_one(
            {"conversation_id": conversation_id},
            {"_id": 0}
        )
        return doc if doc else None

    def get_all_by_user(self, user_id: str) -> list[str]:
        """Get all conversation IDs for a user."""
        docs = self._meta().find(
            {"user_id": user_id},
            {"_id": 0, "conversation_id": 1}
        )
        return [d["conversation_id"] for d in docs]

    # ── Cleanup ───────────────────────────────────────────

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete all data for a conversation."""
        self._messages().delete_many({"conversation_id": conversation_id})
        self._summaries().delete_many({"conversation_id": conversation_id})
        self._meta().delete_many({"conversation_id": conversation_id})