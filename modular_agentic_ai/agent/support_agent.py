import asyncio
from typing import Any, cast
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory

from modular_agentic_ai.tools.order_tool import OrderTool
from modular_agentic_ai.tools.product_tool import ProductTool
from modular_agentic_ai.registery_tool.order_registery import create_order_tools
from modular_agentic_ai.registery_tool.product_registery_tool import create_product_tools
from modular_agentic_ai.prompt.prompt_builder import build_system_prompt
from sessions.session_manager import Session
from modular_agentic_ai.memory.memory_manager import MemoryManager
from modular_agentic_ai.agent.llm_client import LLMClient

memory_manager = MemoryManager()
llm_client = LLMClient()


def _build_chat_history(conversation_id: str) -> ChatMessageHistory:
    """Load history from MongoDB and return as LangChain ChatMessageHistory."""
    chat_history = ChatMessageHistory()
    messages = memory_manager.build_langchain_messages(conversation_id)

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


async def create_support_agent(session: Session):
    """Create an agent bound to a specific user session with MongoDB memory."""

    await memory_manager.init_conversation(
        conversation_id=session.conversation_id,
        user_id=session.user_id
    )

    tools = _build_tools()
    memory_context = memory_manager.get_context(session.conversation_id)

    system_prompt = build_system_prompt(
        user=session.user,
        memory_context=memory_context
    )
    
    return create_agent(
        model=llm_client.raw,
        tools=tools,
        system_prompt=system_prompt,
    )


def _extract_reply(response) -> str:
    if isinstance(response, dict):
        output = response.get("output")
        if output:
            return str(output)

        messages = response.get("messages")
        if isinstance(messages, list):
            for message in reversed(messages):
                if isinstance(message, AIMessage) and message.content:
                    content = message.content
                    return content if isinstance(content, str) else str(content)

    content = getattr(response, "content", None)
    if content:
        return content if isinstance(content, str) else str(content)

    return str(response)


async def run_agent(session: Session, user_input: str) -> str:
    """Run the agent, persist messages, trigger summarization."""
    agent = await create_support_agent(session)
    chat_history = _build_chat_history(session.conversation_id)

    memory_manager.add_user_message(
        session.conversation_id, user_input
    )

    response = agent.invoke(
        cast(
            Any,
            {"messages": 
                [*chat_history.messages, 
                 HumanMessage(content=user_input)
                 ]}

        )
        
    )

    reply = _extract_reply(response)
    # ── save assistant reply to MongoDB ───────────────────

    memory_manager.add_assistant_message(
        session.conversation_id, reply
    )
    # ── summarize ─────────────────────────────────────────
    if memory_manager.should_summarize(session.conversation_id):
        await memory_manager.summarize(session.conversation_id)      # ← compress at threshold
    else:
        memory_manager.save_summary(session.conversation_id) 
  
    return reply
