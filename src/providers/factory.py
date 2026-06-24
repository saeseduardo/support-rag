from src.providers.llm.base import BaseLLMProvider
from src.providers.embeddings.base import BaseEmbeddingProvider
from src.config import settings


def get_llm() -> BaseLLMProvider:
    """Devuelve el proveedor LLM segun AI_PROVIDER en .env"""
    provider = settings.ai_provider.lower()

    if provider == "gemini":
        from src.providers.llm.gemini import GeminiProvider
        return GeminiProvider()

    if provider == "openai":
        from src.providers.llm.openai_llm import OpenAIProvider
        return OpenAIProvider()

    raise ValueError(
        f"Proveedor '{provider}' no soportado. "
        f"Opciones: gemini, openai"
    )


def get_embedder() -> BaseEmbeddingProvider:
    """Devuelve el proveedor de embeddings segun AI_PROVIDER en .env"""
    provider = settings.ai_provider.lower()

    if provider == "gemini":
        from src.providers.embeddings.gemini import GeminiEmbeddingProvider
        return GeminiEmbeddingProvider()

    if provider == "openai":
        from src.providers.embeddings.openai_embedding import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider()

    raise ValueError(
        f"Proveedor '{provider}' no soportado. "
        f"Opciones: gemini, openai"
    )