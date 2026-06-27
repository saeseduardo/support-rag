"""
searcher.py — Sprint 2
Vector search con soporte de filtros por metadata (source, section, date).
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.ingestion.embedder import embed_batch
from src.models.schemas import SourceChunk
from src.config import settings


def search(
    db: Session,
    query: str,
    top_k: int | None = None,
    source_filter: list[str] | None = None,
    section_filter: str | None = None,
    strategy_filter: str | None = None,
) -> tuple[list[SourceChunk], list[float]]:
    """
    Busca los chunks más similares a la query usando cosine similarity.

    Sprint 2: agrega filtros por metadata — source, section y strategy.
    Permite buscar solo en documentos específicos o chunks de una estrategia
    concreta durante la comparativa.

    Args:
        db:              Sesión de base de datos.
        query:           Pregunta del usuario.
        top_k:           Cuántos chunks recuperar (default: top_k_retrieval).
        source_filter:   Lista de nombres de archivo a incluir.
        section_filter:  Texto del header de sección (metadata->>'section').
        strategy_filter: Estrategia de chunking ('fixed', 'semantic', 'recursive').

    Returns:
        (chunks ordenados por score, embedding de la query)
    """
    top_k = top_k or settings.top_k_retrieval

    # 1. Embedding de la query
    query_embedding = embed_batch([query])[0]

    # 2. Construye cláusulas WHERE dinámicas
    conditions = []
    params: dict = {"embedding": str(query_embedding), "limit": top_k}

    if source_filter:
        conditions.append("source_file = ANY(:sources)")
        params["sources"] = source_filter

    if section_filter:
        conditions.append("metadata->>'section' ILIKE :section")
        params["section"] = f"%{section_filter}%"

    if strategy_filter:
        conditions.append("metadata->>'strategy' = :strategy")
        params["strategy"] = strategy_filter

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # 3. Vector search con pgvector
    rows = db.execute(
        text(f"""
            SELECT
                content,
                source_file,
                chunk_index,
                metadata,
                1 - (embedding <=> :embedding::vector) AS score
            FROM documents
            {where_clause}
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """),
        params,
    ).fetchall()

    chunks = [
        SourceChunk(
            content=row.content,
            source_file=row.source_file,
            chunk_index=row.chunk_index,
            metadata=row.metadata or {},
            score=round(float(row.score), 4),
        )
        for row in rows
    ]

    return chunks, query_embedding
