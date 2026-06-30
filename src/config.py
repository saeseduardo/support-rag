from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # ── Proveedor de IA ──────────────────────────────────────────────────────
    ai_provider: Literal["gemini", "openai"] = "gemini"

    # Gemini
    gemini_api_key: str = ""

    # OpenAI (opcional)
    openai_api_key: str = ""

    # ── Modelos ──────────────────────────────────────────────────────────────
    llm_model: str = "gemini-2.0-flash"
    embedding_model: str = "models/text-embedding-004"
    embedding_dimensions: int = 768

    # ── Base de datos ────────────────────────────────────────────────────────
    database_url: str = "postgresql://dev:dev@localhost:5432/supportrag"

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"

    # ── App ──────────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"

    # ── RAG config ───────────────────────────────────────────────────────────
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 10
    top_k_rerank: int = 3

    # ── estrategia de chunking ─────────────────────────────────────
    # Opciones: fixed | semantic | recursive
    chunk_strategy: str = "recursive"

    # ── Cohere  ────────────────────────────────────────────────────
    cohere_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
