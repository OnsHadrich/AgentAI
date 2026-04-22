from langchain_community.chat_message_histories import ChatMessageHistory
from datetime import datetime


class Session:
    def __init__(self, user_id: str, user_name: str, tier: str):
        self.user_id = user_id
        self.user_name = user_name
        self.tier = tier
        self.memory = ChatMessageHistory()   # ← replaces ConversationBufferMemory
        self.created_at = datetime.now()
        self.last_active = datetime.now()

    def touch(self):
        """Update last active timestamp on every message."""
        self.last_active = datetime.now()

    def summary(self):
        return (
            f"User     : {self.user_name} (ID: {self.user_id})\n"
            f"Tier     : {self.tier}\n"
            f"Started  : {self.created_at.strftime('%H:%M:%S')}\n"
            f"Last seen: {self.last_active.strftime('%H:%M:%S')}"
        )


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(self, user_id: str, user_name: str, tier: str) -> Session:
        """Create a new session for a user, replacing any existing one."""
        session = Session(user_id, user_name, tier)
        self._sessions[user_id] = session
        print(f"[Session] New session created for {user_name} ({user_id})")
        return session

    def get_session(self, user_id: str) -> Session | None:
        """Retrieve an existing session by user ID."""
        return self._sessions.get(user_id)

    def end_session(self, user_id: str):
        """Delete a user's session."""
        if user_id in self._sessions:
            name = self._sessions[user_id].user_name
            del self._sessions[user_id]
            print(f"[Session] Session ended for {name} ({user_id})")

    def list_sessions(self):
        """Show all active sessions."""
        if not self._sessions:
            print("No active sessions.")
            return
        print(f"\n{'='*40}")
        print(f"Active sessions: {len(self._sessions)}")
        print(f"{'='*40}")
        for uid, session in self._sessions.items():
            print(f"\n{session.summary()}")
        print(f"{'='*40}\n")