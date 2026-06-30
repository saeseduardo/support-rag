import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app

client = TestClient(app)


def test_health_endpoint():
    """El health check debe responder aunque los servicios externos fallen."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded", "down")


@patch("src.api.query.rerank")
@patch("src.api.query.search")
@patch("src.api.query.get_llm")
def test_query_endpoint_structure(mock_get_llm, mock_search, mock_rerank):
    """Verifica que el endpoint devuelve el schema correcto."""
    from src.models.schemas import SourceChunk
    from src.providers.llm.base import LLMResponse

    source_chunk = SourceChunk(
        content="Contenido de prueba",
        source_file="test.pdf",
        chunk_index=0,
        score=0.9,
        metadata={},
    )
    mock_search.return_value = ([source_chunk], [0.1] * 1536)
    mock_rerank.return_value = [source_chunk]

    mock_llm = MagicMock()
    mock_llm.complete.return_value = LLMResponse(
        content="Respuesta de prueba",
        input_tokens=100,
        output_tokens=50,
        model="test-model",
    )
    mock_llm.calculate_cost.return_value = 0.001
    mock_get_llm.return_value = mock_llm

    response = client.post("/query", json={"query": "Como uso el sistema?"})

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "latency" in data
    assert "cost_usd" in data
    assert data["cost_usd"] > 0


def test_query_validates_empty_string():
    """No debe aceptar queries vacias."""
    response = client.post("/query", json={"query": "ab"})  # menos de 3 chars
    assert response.status_code == 422
