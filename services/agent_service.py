from repositories.conversation_repository import ConversationRepository
from repositories.user_repository import UserRepository
from model.conversation import Role
from agent. import chat
from modular_agentic_ai.prompt.prompt_builder import build_system_prompt

class AgentService:
    def __init__(self):
        self.conv_repo = ConversationRepository()
        self.user_repo = UserRepository()

    def start_conversation(self, user_id: str) -> str:
        """Creates a new conversation, returns conversation_id."""
        conv = self.conv_repo.create(user_id)
        return conv.conversation_id

    def reply(self, user_id: str, conversation_id: str, user_message: str) -> str:
        """Process user message and return AI response."""
        # 1. get user context
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        # 2. save user message
        self.conv_repo.append_message(conversation_id, Role.USER, user_message)

        # 3. build prompt + history
        system_prompt = build_system_prompt(user)
        history = self.conv_repo.get_history(conversation_id)

        # 4. call LLM
        ai_response = chat(system_prompt, history, user_message)

        # 5. save AI response
        self.conv_repo.append_message(conversation_id, Role.ASSISTANT, ai_response)

        return ai_response