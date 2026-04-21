from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools.order_tool import get_order_status,delete_order,create_order,confirm_delivery,cancel_order
from tools.product_tool import check_product_availability, get_product_details, get_product_price, list_available_products, list_products, search_products
from prompt.system_prompt import build_system_prompt
from sessions.session_manager import Session
import os
Model_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")
API_KEY = os.getenv("API_KEY")

def create_agent(session: Session) -> AgentExecutor:
    """Create an agent executor bound to a specific user session."""
    llm = ChatOpenAI(model=Model_NAME, temperature=0)

    tools = [get_order_status, delete_order, create_order, confirm_delivery, cancel_order,
             check_product_availability, get_product_details, get_product_price, list_available_products, list_products, search_products]

    system_prompt = build_system_prompt(session.user_name, session.tier)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad")
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=session.memory,   # ← each session has its own memory
        verbose=False
    )