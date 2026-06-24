import hashlib
import json
from sqlalchemy.orm import Session
from sqlalchemy import text


def compute_checksum(content: str) -> str:
    """MD5 del contenido — para ingesta incremental."""
    return hashlib.md5(content.encode()).hexdigest()


def file_needs_ingestion(db: Session, source_file: str, checksum: str) -> bool:
    """
    Devuelve True si el archivo no ha sido ingestado antes
    o si su contenido cambio (checksum distinto).
    """
    result = db.execute(
        text("SELECT checksum FROM ingestion_log WHERE source_file = :f"),
        {"f": source_file},
    ).fetchone()

    if result is None:
        return True  # archivo nuevo
    return result.checksum != checksum  # archivo modificado


def save_chunks(db: Session, chunks: list[dict]) -> int:
    """
    Guarda los chunks con sus embeddings en pgvector.
    Devuelve la cantidad de chunks guardados.
    """
    if not chunks:
        return 0

    # Borra chunks anteriores del mismo archivo (re-ingesta)
    source_file = chunks[0]["source_file"]
    db.execute(
        text("DELETE FROM documents WHERE source_file = :f"),
        {"f": source_file},
    )

    # Inserta los nuevos chunks
    for chunk in chunks:
        db.execute(
            text("""
                INSERT INTO documents
                    (content, embedding, metadata, source_file, chunk_index, checksum)
                VALUES
                    (:content, :embedding, :metadata, :source_file, :chunk_index, :checksum)
            """),
            {
                "content": chunk["content"],
                "embedding": str(chunk["embedding"]),
                "metadata": json.dumps(chunk.get("metadata", {})),
                "source_file": chunk["source_file"],
                "chunk_index": chunk["chunk_index"],
                "checksum": chunk.get("checksum", ""),
            },
        )

    db.commit()
    return len(chunks)


def update_ingestion_log(
    db: Session, source_file: str, checksum: str, chunks_count: int
):
    """Registra o actualiza el log de ingesta de un archivo."""
    db.execute(
        text("""
            INSERT INTO ingestion_log (source_file, checksum, chunks_count)
            VALUES (:f, :c, :n)
            ON CONFLICT (source_file)
            DO UPDATE SET checksum = :c, chunks_count = :n, ingested_at = NOW()
        """),
        {"f": source_file, "c": checksum, "n": chunks_count},
    )
    db.commit()
