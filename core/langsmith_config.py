import os
from dotenv import load_dotenv
from core.config import Configs

configs = Configs()


def setup_langsmith() -> None:
    """
    Configure LangSmith tracing.
    Call once at startup in main.py.
    """
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = configs.LANGCHAIN_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = configs.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = configs.LANGCHAIN_PROJECT

    print(f"LangSmith tracing enabled ✓")
    print(f"Project: {configs.LANGCHAIN_PROJECT}")
    print(f"Dashboard: https://smith.langchain.com/projects/{configs.LANGCHAIN_PROJECT}")