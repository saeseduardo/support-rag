from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ai_provider: str = "gemini"

    gemini_api_key: str = ""
    openai_api_key: str = ""

    llm_model: str = "gemini-2.0-flash"
    embedding_model: str = "models/text-embedding-004"
    embedding_dimensions: int = 768

    database_url: str = "postgresql://dev:dev@localhost:5432/supportrag"
    redis_url: str = "redis://localhost:6379"

    chunk_size: int = 512
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
