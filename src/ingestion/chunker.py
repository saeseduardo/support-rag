"""
Tres estrategias de chunking comparables.
La estrategia activa se configura con CHUNK_STRATEGY en .env.
"""
from enum import Enum
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
)
from src.config import settings


class ChunkStrategy(str, Enum):
    FIXED      = "fixed"       # 512 tokens, overlap 50 — Sprint 1
    SEMANTIC   = "semantic"    # agrupa por oraciones similares
    RECURSIVE  = "recursive"   # respeta estructura del documento (mejor para Markdown/PDF)


# ── Splitters pre-inicializados ───────────────────────────────────────────────

_fixed_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    length_function=len,
)

_recursive_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    # Respeta estructura: headers > parrafos > oraciones > palabras
    separators=[
        "\n# ", "\n## ", "\n### ",   # headers Markdown
        "\n\n",                       # parrafos
        "\n",                         # saltos de linea
        ". ", "! ", "? ",            # oraciones
        " ", "",                      # palabras / chars
    ],
    length_function=len,
)


def chunk_document(
    content: str,
    source_file: str,
    strategy: ChunkStrategy = None,
) -> list[dict]:
    """
    Divide el contenido en chunks usando la estrategia configurada.

    Args:
        content:     Texto limpio del documento.
        source_file: Nombre del archivo fuente (para metadata).
        strategy:    Estrategia de chunking. Si es None, usa CHUNK_STRATEGY del .env.

    Returns:
        Lista de dicts con content, source_file, chunk_index, metadata, strategy.
    """
    strategy = strategy or ChunkStrategy(settings.chunk_strategy)

    if strategy == ChunkStrategy.FIXED:
        raw_chunks = _fixed_splitter.split_text(content)

    elif strategy == ChunkStrategy.RECURSIVE:
        raw_chunks = _recursive_splitter.split_text(content)

    elif strategy == ChunkStrategy.SEMANTIC:
        # Semantic: corta en oraciones y agrupa hasta llenar el chunk_size
        # Usa el splitter recursivo con separadores de oracion solamente
        sentence_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=[". ", "! ", "? ", "\n\n", "\n", " ", ""],
            length_function=len,
        )
        raw_chunks = sentence_splitter.split_text(content)

    else:
        raise ValueError(f"Estrategia desconocida: {strategy}")

    chunks = []
    for i, chunk_text in enumerate(raw_chunks):
        chunk_text = chunk_text.strip()
        if len(chunk_text) < 20:
            continue
        chunks.append({
            "content":     chunk_text,
            "source_file": source_file,
            "chunk_index": i,
            "strategy":    strategy.value,
            "metadata": {
                "char_count":  len(chunk_text),
                "word_count":  len(chunk_text.split()),
                "strategy":    strategy.value,
            },
        })

    return chunks
