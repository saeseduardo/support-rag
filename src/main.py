from fastapi import FastAPI

from src.api.health import router as health_router
from src.api.query import router as query_router
from src.models.db import init_db

app = FastAPI(title="Support RAG", version="1.0.0")

app.include_router(health_router)
app.include_router(query_router)


@app.on_event("startup")
def on_startup():
    init_db()
