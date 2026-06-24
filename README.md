# SupportRAG

Sistema RAG para automatizar respuestas de soporte técnico sobre documentación privada. Construido con arquitectura multi-proveedor: cambia entre Google Gemini y OpenAI editando una sola variable de entorno.

---

## El problema que resuelve

Los agentes de soporte buscan manualmente en miles de páginas de documentación para responder cada ticket. SupportRAG indexa esa documentación y responde preguntas en lenguaje natural en menos de 2 segundos, citando las fuentes exactas de cada respuesta.

---

## Arquitectura

El diseño central es un **patrón Provider/Factory** que desacopla la lógica de negocio de los proveedores de IA. `query.py` y `embedder.py` nunca importan Gemini ni OpenAI directamente — solo conocen las clases abstractas `BaseLLMProvider` y `BaseEmbeddingProvider`. La `factory.py` resuelve el proveedor correcto en runtime según la variable `AI_PROVIDER` del entorno.

```
POST /query
    │
    ├── embed_query()         providers/factory → GeminiEmbeddingProvider
    │                         text-embedding-004 · 768 dims · GRATIS
    │
    ├── vector_search()       pgvector · cosine similarity · top-10
    │
    ├── rerank()              Cohere Rerank · top-3  (Sprint 2)
    │
    └── generate_answer()     providers/factory → GeminiProvider
                              gemini-2.0-flash · 1M context · $0.10/1M tokens
```

```
src/providers/
    factory.py              ← único punto de cambio de proveedor
    llm/
        base.py             ← BaseLLMProvider (ABC)
        gemini.py           ← GeminiProvider
        openai.py           ← OpenAIProvider
    embeddings/
        base.py             ← BaseEmbeddingProvider (ABC)
        gemini.py           ← GeminiEmbeddingProvider (gratuito)
        openai.py           ← OpenAIEmbeddingProvider
```

Agregar un proveedor nuevo (Anthropic, Mistral) requiere crear un archivo en `providers/llm/` y un `if` en `factory.py`. Ningún otro archivo cambia.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| API | FastAPI · Uvicorn |
| LLM | Google Gemini 2.0 Flash / OpenAI GPT-4o-mini |
| Embeddings | Gemini text-embedding-004 (768 dims, gratis) / OpenAI text-embedding-3-small |
| Vector DB | PostgreSQL + pgvector |
| Chunking | LangChain RecursiveCharacterTextSplitter |
| Reranking | Cohere Rerank v3 (Sprint 2) |
| Evals | RAGAS + Langfuse (Sprint 3) |
| Caché | Redis |
| Infraestructura | Docker · Docker Compose |

---

## Inicio rápido

**1. Clona y configura el entorno**

```bash
git clone https://github.com/tu-usuario/support-rag.git
cd support-rag
cp .env.example .env
```

Edita `.env` y agrega tu API key. Por defecto usa Gemini (gratuito para desarrollo):

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=AIza...        # obtén en ai.google.dev — tier gratuito suficiente
```

Para usar OpenAI en su lugar:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

**2. Levanta la base de datos**

```bash
docker-compose up -d
```

**3. Instala dependencias y corre la app**

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

**4. Indexa tus documentos**

Copia tus PDFs o archivos `.md` a la carpeta `/docs`, luego:

```bash
python scripts/ingest.py
```

El pipeline detecta automáticamente archivos nuevos o modificados (checksum MD5) y solo re-procesa los que cambiaron.

**5. Prueba el sistema**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Cómo reseteo mi password?"}'
```

Respuesta:

```json
{
  "answer": "Para resetear tu password, ve a Configuración → Seguridad...",
  "sources": [
    { "source_file": "guia-usuario.pdf", "score": 0.91, "content": "..." }
  ],
  "tokens_used": 847,
  "cost_usd": 0.000093,
  "provider": "gemini-2.0-flash",
  "latency": { "embed_ms": 45, "search_ms": 18, "llm_ms": 890, "total_ms": 953 }
}
```

---

## Cambiar de proveedor

Editar una línea en `.env` y reiniciar:

```bash
# De Gemini a OpenAI
AI_PROVIDER=openai

# De OpenAI a Gemini
AI_PROVIDER=gemini
```

Ningún archivo de código cambia. El campo `provider` en la respuesta confirma cuál está activo.

> **Nota sobre dimensiones:** Gemini produce vectores de 768 dimensiones; OpenAI de 1536. Si cambias de proveedor en un proyecto ya con datos, actualiza `EMBEDDING_DIMENSIONS` en `.env` y re-indexa con `python scripts/ingest.py --force` para regenerar todos los embeddings.

---

## Decisiones técnicas

**pgvector sobre Pinecone o Chroma**
PostgreSQL ya está en la infraestructura de cualquier backend. Agregar la extensión pgvector añade búsqueda vectorial sin introducir otra base de datos que operar. El rendimiento es equivalente hasta ~1M de chunks. La columna `metadata JSONB` permite filtrar por fuente, fecha o sección sin tablas adicionales.

**Gemini como proveedor default**
`text-embedding-004` es gratuito hasta 1500 requests/minuto — la ingesta completa cuesta $0 durante desarrollo. `gemini-2.0-flash` tiene 1M de tokens de contexto vs 128K de `gpt-4o-mini`, lo que permite pasar más chunks sin truncar. El precio es un 33% menor que GPT-4o-mini para el mismo caso de uso.

**Chunking 512 tokens / 50 de overlap**
Balance entre contexto suficiente para responder y precisión del retrieval. Chunks más grandes contienen más información irrelevante; chunks más pequeños pierden el contexto de la idea. El overlap de 50 tokens evita cortar ideas a la mitad entre dos chunks consecutivos.

**Factory con imports lazy**
Los imports de `GeminiProvider` y `OpenAIProvider` dentro de los `if` evitan que Python intente importar `google-generativeai` cuando `AI_PROVIDER=openai`, y viceversa. El proyecto funciona con solo una de las dos librerías instalada.

## Estructura del proyecto

```
support-rag/
├── src/
│   ├── api/
│   │   ├── query.py          # POST /query
│   │   └── health.py         # GET /health
│   ├── ingestion/
│   │   ├── loader.py         # Lee y limpia PDFs y Markdown
│   │   ├── chunker.py        # RecursiveCharacterTextSplitter
│   │   ├── embedder.py       # Genera embeddings via factory
│   │   └── store.py          # Guarda en pgvector, ingesta incremental
│   ├── retrieval/
│   │   ├── searcher.py       # Cosine similarity con pgvector
│   │   └── reranker.py       # Cohere Rerank (Sprint 2)
│   ├── providers/
│   │   ├── factory.py        # Único punto de cambio de proveedor
│   │   ├── llm/
│   │   │   ├── base.py       # BaseLLMProvider (ABC)
│   │   │   ├── gemini.py     # GeminiProvider
│   │   │   └── openai.py     # OpenAIProvider
│   │   └── embeddings/
│   │       ├── base.py       # BaseEmbeddingProvider (ABC)
│   │       ├── gemini.py     # GeminiEmbeddingProvider
│   │       └── openai.py     # OpenAIEmbeddingProvider
│   ├── models/
│   │   ├── schemas.py        # Pydantic: QueryRequest, QueryResponse
│   │   └── db.py             # init_db, tablas, get_db
│   ├── config.py             # Settings desde .env con Pydantic
│   └── main.py               # FastAPI app + routers
├── scripts/
│   ├── ingest.py             # Pipeline de ingesta completo
│   └── manual_test.py        # Prueba con preguntas reales
├── tests/
│   ├── test_ingestion.py
│   └── test_query.py
├── docs/                     # Coloca aquí tus PDFs y .md
├── data/                     # test_results.json, eval datasets
├── docker-compose.yml        # PostgreSQL 16 + pgvector + Redis
├── Dockerfile                # Multi-stage, imagen < 200MB
├── requirements.txt
└── .env.example
```

---

## Tests

```bash
pytest tests/ -v
```

Los tests de `test_query.py` mockean el vector search y el LLM — no requieren API keys ni base de datos para correr.

---