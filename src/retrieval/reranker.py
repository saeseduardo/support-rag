"""
reranker.py — Sprint 2
Cohere Rerank: reordena los chunks por relevancia real respecto a la query.
"""
import cohere
from src.models.schemas import SourceChunk
from src.config import settings

_cohere: cohere.Client | None = None


def _get_client() -> cohere.Client:
    """Lazy init del cliente Cohere — solo si COHERE_API_KEY esta configurado."""
    global _cohere
    if _cohere is None:
        if not settings.cohere_api_key:
            raise RuntimeError(
                "COHERE_API_KEY no configurado. "
                "Obtén una key gratuita en dashboard.cohere.com "
                "y agrégala al .env"
            )
        _cohere = cohere.Client(api_key=settings.cohere_api_key)
    return _cohere


def rerank(
    query: str,
    chunks: list[SourceChunk],
    top_n: int | None = None,
) -> list[SourceChunk]:
    """
    Reordena los chunks por relevancia real usando Cohere Rerank v3.

    El vector search devuelve chunks similares por geometría del embedding.
    El reranker lee la query Y el chunk juntos y decide si el chunk
    realmente responde la pregunta — mucho más preciso.

    Args:
        query:  Pregunta original del usuario.
        chunks: Lista de chunks del vector search (top-10).
        top_n:  Cuántos devolver tras reranking (default: top_k_rerank del config).

    Returns:
        Lista de SourceChunk reordenados, limitados a top_n.
    """
    top_n = top_n or settings.top_k_rerank

    if not chunks:
        return []

    # Si Cohere no está configurado, fallback al orden del vector search
    if not settings.cohere_api_key:
        return chunks[:top_n]

    client = _get_client()
    docs   = [c.content for c in chunks]

    results = client.rerank(
        query=query,
        documents=docs,
        top_n=top_n,
        model="rerank-english-v3.0",
        return_documents=False,   # solo necesitamos los índices
    )

    # Reconstruye la lista en el nuevo orden, actualizando el score
    reranked = []
    for r in results.results:
        chunk = chunks[r.index].model_copy()
        # Reemplaza el score de cosine similarity por el score de Cohere (0-1)
        chunk.score = round(r.relevance_score, 4)
        reranked.append(chunk)

    return reranked
