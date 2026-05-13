from langchain_community.chat_message_histories import ChatMessageHistory
from datetime import datetime
import uuid

from model.user_model import User


class Session:
    def __init__(self,user :User):
        self.user = user
        self.user_id = user.user_id
        self.user_name = user.name
        self.tier = user.tier
        self.memory = ChatMessageHistory()
        self.conversation_id = str(uuid.uuid4())   # ← unique ID per session for Redis
        self.created_at = datetime.now()
        self.last_active = datetime.now()

    def touch(self):
        self.last_active = datetime.now()

    def summary(self):
        return (
            f"User            : {self.user_name} (ID: {self.user_id})\n"
            f"Tier            : {self.tier}\n"
            f"Conversation ID : {self.conversation_id}\n"
            f"Started         : {self.created_at.strftime('%H:%M:%S')}\n"
            f"Last seen       : {self.last_active.strftime('%H:%M:%S')}"
        )


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(self, user: User) -> Session:
        session = Session(user)
        self._sessions[user.user_id] = session
        print(f"[Session] New session for {user.name} | conv_id: {session.conversation_id}")
        return session

    def get_session(self, user_id: str) -> Session | None:
        return self._sessions.get(user_id)

    def end_session(self, user_id: str):
        if user_id in self._sessions:
            name = self._sessions[user_id].user_name
            del self._sessions[user_id]
            print(f"[Session] Ended for {name} ({user_id})")

    def list_sessions(self):
        if not self._sessions:
            print("No active sessions.")
            return
        for uid, session in self._sessions.items():
            print(f"\n{session.summary()}")
        
