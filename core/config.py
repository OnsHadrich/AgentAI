import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

load_dotenv()

ENV: str = ""
BASE_DIR: Path = Path(__file__).resolve().parent.parent


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Configs(BaseSettings):
    # base
    ENV: str = os.getenv("ENV", "dev")
    API: str = "/api"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "agent-support"


    # date
    DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
    DATE_FORMAT: str = "%Y-%m-%d"

  
    # ── Auth ──────────────────────────────────────────────
    JWT_SECRET: str = os.getenv("JWT_SECRET", "fallback_secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = env_int("JWT_EXPIRE_MINUTES", 60)
    
    # ── Redis ─────────────────────────────────────────────
    # REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    # REDIS_PORT: int = env_int("REDIS_PORT", 6379)
    # REDIS_DB: int = env_int("REDIS_DB", 0)
    # REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD", None)
    # add these fields to your existing Configs class
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "shopai_support"
    
    # ── AI ────────────────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    LLM_MAX_TOKENS: int = 1024
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # ── Mock data (JSON files) ────────────────────────────
    DATA_DIR: Path = BASE_DIR / "data"
    USERS_FILE: Path = DATA_DIR / "users.json"
    ORDERS_FILE: Path = DATA_DIR / "orders.json"
    PRODUCTS_FILE: Path = DATA_DIR / "products.json"
    # add these fields to your existing Configs class
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "shopai-support"
    
    # ── WhatsApp API Configurations ───────────────────────
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v17.0"
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    

    @field_validator("JWT_EXPIRE_MINUTES", mode="before")
    @classmethod
    def parse_int_settings(cls, value, info):
        defaults = {
            "JWT_EXPIRE_MINUTES": 60,
        }
        if value is None or value == "":
            return defaults[info.field_name]
        try:
            return int(value)
        except (TypeError, ValueError):
            return defaults[info.field_name]

    class Config:
        case_sensitive = True


class TestConfigs(Configs):
    ENV: str = "test"


if ENV == "prod":
    pass
elif ENV == "stage":
    pass
elif ENV == "test":
    setting = TestConfigs()
