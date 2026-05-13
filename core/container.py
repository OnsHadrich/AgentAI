from dependency_injector import containers, providers

from services.user_service import UserService

from .config import Configs

# repositories
from repositories.user_repository import UserRepository
from repositories.order_repository import OrderRepository
from repositories.product_repository import ProductRepository
from repositories.conversation_repository import ConversationRepository

# services
from services.auth_service import AuthService
from services.agent_service import AgentService

# agent
from modular_agentic_ai.agent.llm_client import LLMClient
from modular_agentic_ai.prompt.prompt_builder import build_system_prompt

# tools
from modular_agentic_ai.tools.order_tool import  OrderTool 
from modular_agentic_ai.tools.product_tool import ProductTool

# sessions
from sessions.session_manager import SessionManager


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        modules=[
            "api.routes.auth",
            "api.routes.chat",
        ]
    )

    # ── Config ────────────────────────────────────────────
    config = providers.Object(Configs())

    # ── Repositories (Singleton — JSON loaded once) ───────
    user_repository = providers.Singleton(
        UserRepository,
        filepath=Configs().USERS_FILE
    )
    order_repository = providers.Singleton(
        OrderRepository,
        filepath=Configs().ORDERS_FILE
    )
    product_repository = providers.Singleton(
        ProductRepository,
        filepath=Configs().PRODUCTS_FILE
    )
    conversation_repository = providers.Singleton(
        ConversationRepository        # in-memory, lives for app lifetime
    )

    # ── Sessions (Singleton — shared state) ───────────────
    session_manager = providers.Singleton(SessionManager)

    # ── Agent layer (Singleton — one LLM client) ──────────
    llm_client = providers.Singleton(
        LLMClient,
        api_key=Configs().GROQ_API_KEY,
        model=Configs().LLM_MODEL,
        max_tokens=Configs().LLM_MAX_TOKENS
    )
    prompt_builder = providers.Singleton(build_system_prompt)

    # ── Tools (Factory — fresh per request) ───────────────
    order_tool = providers.Factory(
        OrderTool,
        repo=order_repository
    )
    product_tool = providers.Factory(
        ProductTool,
        repo=product_repository
    )

    # ── Services (Factory — fresh per request) ────────────
    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository,
        session_manager=session_manager
    )
    user_service = providers.Factory(
        UserService,
        user_repository=user_repository
    )
    agent_service = providers.Factory(
        AgentService,
        user_repository=user_repository,
        conversation_repository=conversation_repository,
        llm_client=llm_client,
        prompt_builder=prompt_builder,
        order_tool=order_tool,
        product_tool=product_tool,
    )