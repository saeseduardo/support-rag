import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.models.schemas import QueryRequest, QueryResponse, LatencyBreakdown
from src.models.db import get_db
from src.retrieval.searcher import search
from src.retrieval.reranker import rerank
from src.providers.factory import get_llm

router = APIRouter()

SYSTEM_PROMPT = (
    "Eres un asistente de soporte tecnico. Responde la pregunta del usuario "
    "UNICAMENTE basandote en el contexto proporcionado. "
    "Si la respuesta no esta en el contexto, di exactamente: "
    "'No encontre informacion sobre esto en la documentacion disponible.'"
)

@router.post("/query", response_model=QueryResponse)
def query_docs(req: QueryRequest, db: Session = Depends(get_db)):
    llm = get_llm()
    t0 = time.perf_counter()

    chunks, _ = search(db=db, query=req.query,
                       source_filter=req.source_filter)
    t1 = time.perf_counter()

    top_chunks = rerank(query=req.query, chunks=chunks)
    t2 = time.perf_counter()

    context = "\n\n---\n\n".join(
        f"[{c.source_file}]\n{c.content}" for c in top_chunks
    )
    prompt = f"CONTEXTO:\n{context}\n\nPREGUNTA: {req.query}"

    llm_response = llm.complete(prompt=prompt, system=SYSTEM_PROMPT)
    t3 = time.perf_counter()

    cost = llm.calculate_cost(llm_response)

    return QueryResponse(
        answer=llm_response.content,
        sources=top_chunks,
        latency=LatencyBreakdown(
            embed_ms=round((t1 - t0) * 1000),
            search_ms=round((t2 - t1) * 1000),
            llm_ms=round((t3 - t2) * 1000),
            total_ms=round((t3 - t0) * 1000),
        ),
        tokens_used=llm_response.total_tokens,
        cost_usd=round(cost, 6),
        provider=llm_response.model,
    )
