from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.container import Container
from api.routes import auth, chat, orders, products
from modular_agentic_ai.memory.conversation_store_old import ConversationStore


# ── Lifespan (startup + shutdown) ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    Use for: DB connections, Redis, loading models, etc.
    """
    # ── Startup ───────────────────────────────────────────
    print("Starting ShopAI Support API...")

    # verify Redis connection
    store = ConversationStore()
    try:
        store.client.ping()
        print("Redis connected ✓")
    except Exception as e:
        print(f"Redis connection failed: {e}")

    yield  # ← app runs here

    # ── Shutdown ──────────────────────────────────────────
    print("Shutting down ShopAI Support API...")
    await store.close()
    print("Redis connection closed ✓")


# ── App factory ───────────────────────────────────────────
def create_app() -> FastAPI:

    # ── DI Container ──────────────────────────────────────
    container = Container()
    container.wire(modules=[
        "api.routes.auth",
        "api.routes.chat",
        "api.routes.orders",
        "api.routes.products",
        "core.dependencies",
    ])

    # ── FastAPI app ────────────────────────────────────────
    app = FastAPI(
        title="ShopAI Customer Support API",
        description="Agentic AI customer support powered by LangChain + Groq + Redis",
        redirect_slashes=False,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",        # Swagger UI
        redoc_url="/redoc",      # ReDoc UI
    )

    app.state.container = container

    # ── CORS ──────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],     # restrict to frontend URL in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(orders.router, prefix="/api/v1")
    app.include_router(products.router, prefix="/api/v1")

    # ── Base endpoints ────────────────────────────────────
    @app.get("/", tags=["Health"])
    def root():
        return {
            "app": "ShopAI Customer Support API",
            "status": "running",
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"])
    async def health():
        """Check API and Redis health."""
        store = ConversationStore()
        try:
            store.client.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "disconnected"

        return {
            "api": "ok",
            "redis": redis_status,
        }

    return app


app = create_app()