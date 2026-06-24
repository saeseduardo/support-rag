"""
Pipeline completo de ingesta — corre este script para indexar tus documentos.

Uso:
    python scripts/ingest.py
    python scripts/ingest.py --docs ./mis-docs --force
"""
import time
import argparse
from src.models.db import SessionLocal, init_db
from src.ingestion.loader import load_all_docs
from src.ingestion.chunker import chunk_document
from src.ingestion.embedder import embed_all_chunks
from src.ingestion.store import (
    compute_checksum,
    file_needs_ingestion,
    save_chunks,
    update_ingestion_log,
)


def run_ingestion(docs_path: str = "./docs", force: bool = False):
    print(f"\nIniciando ingesta desde: {docs_path}")
    init_db()
    db = SessionLocal()
    start = time.time()

    docs = load_all_docs(docs_path)
    print(f"Documentos encontrados: {len(docs)}")

    processed = skipped = failed = total_chunks = 0

    for doc in docs:
        checksum = compute_checksum(doc["content"])

        if not force and not file_needs_ingestion(db, doc["name"], checksum):
            print(f"  SKIP  {doc['name']} (sin cambios)")
            skipped += 1
            continue

        try:
            print(f"  PROC  {doc['name']}...")

            chunks = chunk_document(doc["content"], doc["name"])
            print(f"         {len(chunks)} chunks creados")

            chunks = embed_all_chunks(chunks)
            print(f"         {len(chunks)} chunks embeddeados")

            # Agrega checksum a cada chunk para trazabilidad
            for c in chunks:
                c["checksum"] = checksum

            saved = save_chunks(db, chunks)
            update_ingestion_log(db, doc["name"], checksum, saved)

            total_chunks += saved
            processed += 1
            print(f"         {saved} chunks guardados en pgvector")

        except Exception as e:
            print(f"  ERROR {doc['name']}: {e}")
            failed += 1

    duration = time.time() - start
    print(f"\nIngesta completada en {duration:.1f}s")
    print(f"  Procesados: {processed}")
    print(f"  Saltados:   {skipped}")
    print(f"  Fallidos:   {failed}")
    print(f"  Chunks totales en DB: {total_chunks}")
    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", default="./docs", help="Ruta a la carpeta de documentos")
    parser.add_argument("--force", action="store_true", help="Re-ingestar aunque no haya cambios")
    args = parser.parse_args()
    run_ingestion(args.docs, args.force)
