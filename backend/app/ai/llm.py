"""
LLM client factory.
Groq is the primary provider.
"""

from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings


def get_chat_model(
    model_name: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> BaseChatModel:
    """
    Returns a LangChain chat model.
    Primary provider: Groq
    """
    model = model_name or settings.DEFAULT_CHAT_MODEL

    if settings.DEFAULT_LLM_PROVIDER == "groq":
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment variables")

        return ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Future: add OpenAI or other providers here
    raise ValueError(f"Unsupported LLM provider: {settings.DEFAULT_LLM_PROVIDER}")


def get_classification_model() -> BaseChatModel:
    """Slightly lower temperature for structured classification."""
    return get_chat_model(temperature=0.1, max_tokens=1024)


def get_response_model() -> BaseChatModel:
    """Model used for customer-facing response generation."""
    return get_chat_model(temperature=0.3, max_tokens=2048)
