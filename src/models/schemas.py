from pydantic import BaseModel, Field
from typing import Optional


class SourceChunk(BaseModel):
    content: str
    source_file: str
    chunk_index: int
    score: float = Field(description="Similitud coseno 0-1")
    metadata: dict = {}


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    max_chunks: int = Field(default=5, ge=1, le=20)
    source_filter: Optional[list[str]] = None  # filtrar por archivo


class LatencyBreakdown(BaseModel):
    embed_ms: int
    search_ms: int
    llm_ms: int
    total_ms: int


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    latency: LatencyBreakdown
    tokens_used: int
    cost_usd: float
    provider: str


class IngestRequest(BaseModel):
    docs_path: str = Field(default="./docs")
    force_reingest: bool = False  # re-procesa aunque no haya cambios


class IngestResponse(BaseModel):
    processed: int
    skipped: int
    failed: int
    total_chunks: int
    duration_seconds: float


class HealthResponse(BaseModel):
    status: str                    # ok | degraded | down
    postgres: str
    openai: str
    version: str = "1.0.0"
