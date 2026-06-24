import openai
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.models.schemas import HealthResponse
from src.models.db import get_db
from src.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Verifica el estado de todos los componentes del sistema.
    Usado por Railway/Fly.io para saber si la instancia puede recibir trafico.
    """
    # Check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        postgres_status = "ok"
    except Exception as e:
        postgres_status = f"error: {str(e)[:50]}"

    # Check OpenAI (llamada ligera — solo lista modelos)
    try:
        client = openai.OpenAI(api_key=settings.openai_api_key)
        client.models.list()
        openai_status = "ok"
    except Exception as e:
        openai_status = f"error: {str(e)[:50]}"

    overall = "ok"
    if "error" in postgres_status:
        overall = "down"
    elif "error" in openai_status:
        overall = "degraded"

    return HealthResponse(
        status=overall,
        postgres=postgres_status,
        openai=openai_status,
    )
