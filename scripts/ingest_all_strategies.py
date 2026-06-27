"""
ingest_all_strategies.py — Sprint 2
Indexa los mismos documentos con las 3 estrategias de chunking.
Guarda la estrategia en metadata para poder filtrar en el search.

Uso:
    python scripts/ingest_all_strategies.py
    python scripts/ingest_all_strategies.py --docs ./docs --force
"""
import time
import argparse
from src.models.db import SessionLocal, init_db
from src.ingestion.loader import load_all_docs
from src.ingestion.chunker import chunk_document, ChunkStrategy
from src.ingestion.embedder import embed_all_chunks
from src.ingestion.store import (
    compute_checksum,
    save_chunks,
    update_ingestion_log,
)


def ingest_with_strategy(
    docs: list[dict],
    strategy: ChunkStrategy,
    db,
    force: bool = False,
):
    print(f"\n  Estrategia: {strategy.value.upper()}")
    processed = skipped = failed = total_chunks = 0

    for doc in docs:
        checksum = compute_checksum(doc["content"] + strategy.value)
        log_key  = f"{doc['name']}::{strategy.value}"

        try:
            print(f"    PROC  {doc['name']} ...", end=" ")
            chunks = chunk_document(doc["content"], doc["name"], strategy=strategy)

            # Marca la estrategia en el source_file para poder filtrar
            # Ej: "manual.pdf::recursive"
            for c in chunks:
                c["source_file"] = f"{doc['name']}::{strategy.value}"
                c["checksum"]    = checksum

            chunks = embed_all_chunks(chunks)
            saved  = save_chunks(db, chunks)
            update_ingestion_log(db, log_key, checksum, saved)

            total_chunks += saved
            processed    += 1
            print(f"{len(chunks)} chunks → {saved} guardados")

        except Exception as e:
            print(f"\n    ERROR {doc['name']}: {e}")
            failed += 1

    return processed, skipped, failed, total_chunks


def main(docs_path: str = "./docs", force: bool = False):
    print("\nIngesta multi-estrategia — SupportRAG Sprint 2")
    init_db()
    db    = SessionLocal()
    start = time.time()

    docs = load_all_docs(docs_path)
    print(f"Documentos encontrados: {len(docs)}")

    totals = {"processed": 0, "skipped": 0, "failed": 0, "chunks": 0}

    for strategy in ChunkStrategy:
        p, s, f, c = ingest_with_strategy(docs, strategy, db, force)
        totals["processed"] += p
        totals["skipped"]   += s
        totals["failed"]    += f
        totals["chunks"]    += c

    db.close()
    elapsed = time.time() - start

    print(f"\nIngesta completada en {elapsed:.1f}s")
    print(f"  Estrategias: {len(ChunkStrategy)}")
    print(f"  Docs por estrategia: {len(docs)}")
    print(f"  Chunks totales en DB: {totals['chunks']}")
    print(f"\nAhora corre: python scripts/compare_chunking.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs",  default="./docs")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    main(args.docs, args.force)
