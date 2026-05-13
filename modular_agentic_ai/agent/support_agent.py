import asyncio
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from tools.order_tool import OrderTool
from tools.product_tool import ProductTool
from modular_agentic_ai.registery_tool.order_registery import create_order_tools
from modular_agentic_ai.registery_tool.product_registery_tool import create_product_tools
from prompt.prompt_builder import build_system_prompt
from sessions.session_manager import Session
from memory.memory_manager import MemoryManager
from agent.llm_client import LLMClient
from core.config import Configs

configs = Configs()
memory_manager = MemoryManager()
llm_client = LLMClient()


async def _build_chat_history(conversation_id: str) -> ChatMessageHistory:
    """Load history from Redis and return as LangChain ChatMessageHistory."""
    chat_history = ChatMessageHistory()
    messages = memory_manager.build_langchain_messages(conversation_id)  # ← await

    for msg in messages:
        if msg["role"] == "user":
            chat_history.add_message(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            chat_history.add_message(AIMessage(content=msg["content"]))

    return chat_history


def _build_tools() -> list:
    order_tool = OrderTool()
    product_tool = ProductTool()
    return [
        *create_order_tools(order_tool),
        *create_product_tools(product_tool),
    ]


async def create_agent(session: Session) -> RunnableWithMessageHistory:
    """Create an agent bound to a specific user session with Redis memory."""

    memory_manager.init_conversation(          # ← await
        conversation_id=session.conversation_id,
        user_id=session.user_id
    )

    tools = _build_tools()
    memory_context = memory_manager.get_context(session.conversation_id)  # ← await

    system_prompt = build_system_prompt(
        user=session.user,
        memory_context=memory_context
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad")
    ])

    llm_with_tools = llm_client.bind_tools(tools)   # ← use LLMClient

    # pre-load history for this session
    chat_history = await _build_chat_history(session.conversation_id)

    chain = RunnableWithMessageHistory(
        llm_with_tools,
        lambda session_id: chat_history,            # ← pre-loaded, no async lambda needed
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    return chain


async def run_agent(session: Session, user_input: str) -> str:
    """Run the agent, persist messages, trigger summarization."""
    agent = await create_agent(session)             # ← await

    memory_manager.add_user_message(          # ← await
        session.conversation_id, user_input
    )

    response = agent.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session.conversation_id}}
    )

    reply = response.content

    memory_manager.add_assistant_message(     
        session.conversation_id, reply
    )

    asyncio.create_task(                            # fire and forget
        memory_manager.maybe_summarize(session.conversation_id)
    )

    return reply