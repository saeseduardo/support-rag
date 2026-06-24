from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.schemas import SourceChunk
from src.providers.factory import get_embedder


def search(db: Session, query: str, max_chunks: int = 5, source_filter: list[str] | None = None):
    embedder = get_embedder()
    query_embedding = embedder.embed([query])[0]

    sql = """
        SELECT content, source_file, chunk_index, metadata,
               1 - (embedding <=> CAST(:embedding AS vector)) AS score
        FROM documents
        WHERE (:source_filter IS NULL OR source_file = ANY(:source_filter))
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """
    rows = db.execute(
        text(sql),
        {
            "embedding": query_embedding,
            "source_filter": source_filter,
            "limit": max_chunks,
        },
    ).fetchall()

    chunks = [
        SourceChunk(
            content=row.content,
            source_file=row.source_file,
            chunk_index=row.chunk_index,
            score=row.score,
            metadata=row.metadata or {},
        )
        for row in rows
    ]
    return chunks, query_embedding
