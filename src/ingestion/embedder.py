from src.providers.factory import get_embedder

_embedder = get_embedder()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Genera embeddings usando el proveedor configurado en .env"""
    return _embedder.embed(texts)


def embed_all_chunks(chunks: list[dict], batch_size: int = 50) -> list[dict]:
    """
    Embeddea todos los chunks en batches.
    batch_size=50 por defecto (Gemini tiene rate limit mas estricto que OpenAI)
    """
    total = len(chunks)
    processed = 0

    for i in range(0, total, batch_size):
        batch = chunks[i: i + batch_size]
        texts = [c["content"] for c in batch]

        try:
            embeddings = embed_batch(texts)
            for chunk, emb in zip(batch, embeddings):
                chunk["embedding"] = emb
            processed += len(batch)
        except Exception as e:
            print(f"Error en batch {i}: {e}")
            continue

        print(f"Embeddings: {processed}/{total}")

    return [c for c in chunks if "embedding" in c]
