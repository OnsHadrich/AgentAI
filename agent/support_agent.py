import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from tools.order_tool import get_order_status, delete_order, create_order, confirm_delivery, cancel_order
from tools.product_tool import check_product_availability, get_product_details, get_product_price, list_available_products, list_products, search_products
from prompt.system_prompt import build_system_prompt
from sessions.session_manager import Session

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
GROQ_API_KEY = SecretStr(str("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"))

# One memory store for all sessions (LangGraph handles thread_id)
memory = MemorySaver()

def create_agent(session: Session):
    """Create an agent for LangChain 1.2.15"""
    
    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=0,
        api_key=GROQ_API_KEY,
    )

    tools = [
        get_order_status, delete_order, create_order, confirm_delivery, cancel_order,
        check_product_availability, get_product_details, get_product_price,
        list_available_products, list_products, search_products
    ]

    system_prompt = build_system_prompt(session.user_name, session.tier)

    # ✅ v1.2.15 way - no AgentExecutor needed
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,  # system prompt
        checkpointer=memory,   # keeps chat history
    )
    
    return agent