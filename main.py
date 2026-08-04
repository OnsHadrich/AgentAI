from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routes.channels import instagram, messenger, whatsapp
from core.langsmith_config import setup_langsmith      # ← add
from core.container import Container
from api.routes import auth, chat, orders, products
from database.mongodb import MongoDB
from modular_agentic_ai.memory.conversation_store import ConversationStore


# ── Lifespan (startup + shutdown) ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    """
    # ── Startup ───────────────────────────────────────────
    setup_langsmith()  # ← configure LangSmith tracing on startup
    print("Starting ShopAI Support API...")

    try:
        MongoDB.connect()
        store = ConversationStore()
        store.create_indexes()
        print("MongoDB connected ✓")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")

    yield  # ← app runs here

    # ── Shutdown ──────────────────────────────────────────
    print("Shutting down ShopAI Support API...")
    MongoDB.close()
    print("MongoDB connection closed ✓")


# ── App factory ───────────────────────────────────────────
def create_app() -> FastAPI:

    # ── DI Container ──────────────────────────────────────
    container = Container()
    container.wire(modules=[
        "api.routes.auth",
        "api.routes.chat",
        "api.routes.orders",
        "api.routes.products",
        "api.routes.channels.whatsapp",
        "api.routes.channels.messenger",
        "api.routes.channels.instagram",
        "core.dependencies",
    ])

    # ── FastAPI app ────────────────────────────────────────
    app = FastAPI(
        title="ShopAI Customer Support API",
        description="Agentic AI customer support powered by LangChain + Groq + MongoDB",
        redirect_slashes=False,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.state.container = container

    # ── CORS ──────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────
    app.include_router(auth.router,     prefix="/api/v1")
    app.include_router(chat.router,     prefix="/api/v1")
    app.include_router(orders.router,   prefix="/api/v1")
    app.include_router(products.router, prefix="/api/v1")
    app.include_router(whatsapp.router, prefix="/api/v1")
    app.include_router(messenger.router, prefix="/api/v1")
    app.include_router(instagram.router, prefix="/api/v1")
    # ── Base endpoints ────────────────────────────────────
    @app.get("/", tags=["Health"])
    def root():
        return {
            "app": "ShopAI Customer Support API",
            "status": "running",
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"])
    def health():
        """Check API and MongoDB health."""
        try:
            MongoDB.get_client().admin.command("ping")
            mongo_status = "connected"
        except Exception:
            mongo_status = "disconnected"

        return {
            "api": "ok",
            "mongodb": mongo_status,
        }

    return app


app = create_app()
