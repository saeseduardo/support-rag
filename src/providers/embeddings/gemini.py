import time
import google.generativeai as genai
from src.providers.embeddings.base import BaseEmbeddingProvider
from src.config import settings

# Gemini embedding dimensions segun modelo
GEMINI_EMBEDDING_DIMS = {
    "models/text-embedding-004":  768,
    "models/embedding-001":      768,
    "models/gemini-embedding-001": 3072,
}


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Proveedor de embeddings con Google Gemini.
    Modelo: text-embedding-004
    Dimensiones: 768 (diferente a OpenAI 1536 — la DB debe coincidir)
    """

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self._model = settings.embedding_model  # "models/text-embedding-004"

    def embed(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            # Gemini embedding API no soporta batch nativo — loop con backoff
            for attempt in range(3):
                try:
                    result = genai.embed_content(
                        model=self._model,
                        content=text,
                        task_type="retrieval_document",
                        output_dimensionality=settings.embedding_dimensions,
                    )
                    results.append(result["embedding"])
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    time.sleep(2 ** attempt)
        return results

    def dimensions(self) -> int:
        return settings.embedding_dimensions

    def cost_per_million_tokens(self) -> float:
        return 0.0  # text-embedding-004 es GRATIS hasta 1500 req/min
