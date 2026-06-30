"""
test_sprint2.py — Tests del Sprint 2
Cubre las 3 estrategias de chunking, el reranker y los filtros de metadata.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.ingestion.chunker import chunk_document, ChunkStrategy


# ── Chunking ─────────────────────────────────────────────────────────────────

SAMPLE_TEXT = """
# Sección 1: Introducción

Este es el primer párrafo de la documentación. Contiene información importante sobre el producto.

## Subsección 1.1

Aquí hay más contenido. Las oraciones son cortas. Hay varias de ellas.
Cada una aporta algo distinto al contexto general del documento.

# Sección 2: Configuración

Para configurar el sistema, sigue estos pasos detallados que se explican a continuación.
El proceso requiere acceso de administrador y unos 10 minutos de tu tiempo.
""" * 5  # repite para tener suficiente texto


def test_fixed_strategy_produces_chunks():
    chunks = chunk_document(SAMPLE_TEXT, "test.md", ChunkStrategy.FIXED)
    assert len(chunks) > 1
    for c in chunks:
        assert c["strategy"] == "fixed"
        assert len(c["content"]) >= 20
        assert "source_file" in c
        assert "chunk_index" in c


def test_recursive_strategy_produces_chunks():
    chunks = chunk_document(SAMPLE_TEXT, "test.md", ChunkStrategy.RECURSIVE)
    assert len(chunks) > 1
    for c in chunks:
        assert c["strategy"] == "recursive"


def test_semantic_strategy_produces_chunks():
    chunks = chunk_document(SAMPLE_TEXT, "test.md", ChunkStrategy.SEMANTIC)
    assert len(chunks) > 1
    for c in chunks:
        assert c["strategy"] == "semantic"


def test_all_strategies_have_metadata():
    for strategy in ChunkStrategy:
        chunks = chunk_document(SAMPLE_TEXT, "test.pdf", strategy)
        for c in chunks:
            assert "char_count" in c["metadata"]
            assert "word_count" in c["metadata"]
            assert "strategy"   in c["metadata"]


def test_chunk_respects_min_length():
    """No debe producir chunks trivialmente cortos."""
    chunks = chunk_document(SAMPLE_TEXT, "test.md", ChunkStrategy.FIXED)
    for c in chunks:
        assert len(c["content"]) >= 20, f"Chunk muy corto: '{c['content']}'"


def test_recursive_respects_headers():
    """El chunking recursivo no debería cortar a mitad de un header."""
    chunks = chunk_document(SAMPLE_TEXT, "test.md", ChunkStrategy.RECURSIVE)
    for c in chunks:
        # Ningún chunk debe empezar a mitad de un header markdown
        content = c["content"]
        assert not content.startswith("##") or content.count("\n") > 0


# ── Reranker ─────────────────────────────────────────────────────────────────

from src.models.schemas import SourceChunk


def make_chunks(n: int) -> list[SourceChunk]:
    return [
        SourceChunk(
            content=f"Contenido del chunk {i}",
            source_file="test.pdf",
            chunk_index=i,
            score=round(0.9 - i * 0.05, 2),
            metadata={},
        )
        for i in range(n)
    ]


def test_reranker_fallback_without_api_key():
    """Sin COHERE_API_KEY, el reranker devuelve los primeros top_n chunks."""
    from unittest.mock import patch
    with patch("src.retrieval.reranker.settings") as mock_settings:
        mock_settings.cohere_api_key = ""
        mock_settings.top_k_rerank   = 3
        from src.retrieval.reranker import rerank
        chunks  = make_chunks(10)
        result  = rerank("query de prueba", chunks, top_n=3)
        assert len(result) == 3
        assert result[0].chunk_index == 0  # mismo orden


def test_reranker_empty_input():
    """Con lista vacía debe devolver lista vacía."""
    from src.retrieval.reranker import rerank
    result = rerank("query", [], top_n=3)
    assert result == []
