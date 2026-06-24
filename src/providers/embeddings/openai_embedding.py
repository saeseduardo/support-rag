import time
import openai as _openai
from src.providers.embeddings.base import BaseEmbeddingProvider
from src.config import settings


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    Proveedor de embeddings con OpenAI.
    Modelo: text-embedding-3-small
    Dimensiones: 1536
    """

    def __init__(self):
        self._client = _openai.OpenAI(api_key=settings.openai_api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        delay = 2
        for attempt in range(3):
            try:
                resp = self._client.embeddings.create(
                    input=texts,
                    model=settings.embedding_model,
                )
                return [r.embedding for r in resp.data]
            except _openai.RateLimitError:
                if attempt == 2:
                    raise
                time.sleep(delay)
                delay *= 2

    def dimensions(self) -> int:
        return 1536

    def cost_per_million_tokens(self) -> float:
        return 0.02  # $0.02 / 1M tokens
