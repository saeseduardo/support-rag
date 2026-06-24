from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content     TEXT NOT NULL,
                embedding   vector(1536),
                metadata    JSONB DEFAULT '{}',
                source_file TEXT,
                chunk_index INT,
                checksum    TEXT,
                created_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS documents_embedding_idx
            ON documents USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ingestion_log (
                source_file  TEXT PRIMARY KEY,
                checksum     TEXT NOT NULL,
                chunks_count INT,
                ingested_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.commit()