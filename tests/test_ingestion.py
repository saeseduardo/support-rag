import pytest
from src.ingestion.loader import clean_text
from src.ingestion.chunker import chunk_document


def test_clean_text_removes_short_lines():
    raw = "123\nEsta es una linea valida con contenido suficiente\n45\n"
    result = clean_text(raw)
    assert "123" not in result
    assert "45" not in result
    assert "valida" in result


def test_clean_text_normalizes_spaces():
    raw = "texto   con    muchos    espacios"
    result = clean_text(raw)
    assert "  " not in result


def test_chunk_document_returns_chunks():
    content = "Esta es una oracion. " * 100  # texto suficientemente largo
    chunks = chunk_document(content, "test.txt")
    assert len(chunks) > 1
    for chunk in chunks:
        assert "content" in chunk
        assert "source_file" in chunk
        assert chunk["source_file"] == "test.txt"
        assert "chunk_index" in chunk


def test_chunk_document_respects_size():
    content = "palabra " * 1000
    chunks = chunk_document(content, "test.txt")
    for chunk in chunks:
        # Ningún chunk debe ser trivialmente corto
        assert len(chunk["content"]) >= 20
