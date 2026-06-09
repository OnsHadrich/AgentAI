from typing import cast
from langsmith import traceable
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import SecretStr

from core.config import Configs
configs = Configs()

class LLMClient:
    """
    A reusable wrapper around ChatGroq.
    Inject this wherever you need LLM calls
    (MemoryManager, SupportAgent, etc.)
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0,
        max_tokens: int | None = None,
    ):
        self.model = model or configs.LLM_MODEL
        self.api_key = api_key or configs.GROQ_API_KEY
        self.temperature = temperature
        self.max_tokens = max_tokens or configs.LLM_MAX_TOKENS

        if not self.api_key:
            raise ValueError("GROQ_API_KEY is missing. Check your .env file.")

        self.llm = ChatGroq(
            model=self.model,
            temperature=self.temperature,
            api_key=cast(SecretStr, self.api_key),
            max_tokens=self.max_tokens,
        )
    @traceable(run_type="llm", name="LLMClient.invoke")      
    def invoke(self, prompt: str) -> str:
        """
        Simple single prompt call.
        Returns the response as a plain string.
        """
        response = self.llm.invoke(prompt)
        return self._extract_content(response)

    def _extract_content(self, response) -> str:
        content = response.content
        return content if isinstance(content, str) else str(content)
    @traceable(run_type="llm", name="LLMClient.chat")       
    def chat(self, system: str, messages: list[dict]) -> str:
        """
        Multi-turn chat call with a system prompt.

        messages format:
        [
            {"role": "user",      "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user",      "content": "Where is my order?"}
        ]
        """
        langchain_messages: list[BaseMessage] = [SystemMessage(content=system)]

        for msg in messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))

        response = self.llm.invoke(langchain_messages)
        return self._extract_content(response)

    def bind_tools(self, tools: list):
        """
        Return the underlying LLM with tools bound.
        Used by the agent to enable tool calling.
        """
        return self.llm.bind_tools(tools)

    @property
    def raw(self) -> ChatGroq:
        """
        Access the raw ChatGroq instance directly
        when you need to pass it to LangChain components.
        """
        return self.llm