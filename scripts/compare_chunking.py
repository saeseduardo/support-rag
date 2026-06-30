"""
compare_chunking.py — Sprint 2
Compara las 3 estrategias de chunking sobre las mismas preguntas.
Mide faithfulness proxy, latencia y costo por estrategia.

Uso:
    # Asegúrate de tener la app corriendo:
    uvicorn src.main:app --reload

    # Luego en otra terminal:
    python scripts/compare_chunking.py
"""
import json
import time
import httpx
from datetime import datetime
from pathlib import Path

REQUEST_DELAY_S = 15  # evita el rate limit de Gemini free tier

BASE_URL = "http://localhost:8000"

# Las mismas preguntas del manual_test.py — importante usar las mismas
# para que la comparativa sea justa
QUESTIONS = [
    "Como reseteo mi password?",
    "Cuales son los limites del plan gratuito?",
    "Como exporto mis datos en CSV?",
    "Donde veo el historial de facturacion?",
    "Como agrego un nuevo usuario al equipo?",
    "Que pasa si supero el limite de la API?",
]

STRATEGIES = ["fixed", "semantic", "recursive"]


def run_strategy(strategy: str) -> dict:
    """
    Corre las 10 preguntas contra el índice de una estrategia concreta.
    Devuelve métricas agregadas.
    """
    print(f"\n{'='*50}")
    print(f"  Estrategia: {strategy.upper()}")
    print(f"{'='*50}")

    latencies   = []
    costs       = []
    avg_scores  = []
    results     = []

    for i, q in enumerate(QUESTIONS, 1):
        try:
            r = httpx.post(
                f"{BASE_URL}/query",
                json={
                    "query": q,
                    # Sprint 2: filtra por estrategia de chunking
                    # Requiere que hayas indexado con cada estrategia por separado
                    # Ver scripts/ingest_all_strategies.py
                },
                timeout=30.0,
            )
            if r.status_code != 200:
                raise ValueError(f"HTTP {r.status_code}: {r.text[:200]}")
            d = r.json()

            lat   = d.get("latency", {}).get("total_ms", 0)
            cost  = d.get("cost_usd", 0)
            srcs  = d.get("sources", [])
            score = sum(s.get("score", 0) for s in srcs) / len(srcs) if srcs else 0

            latencies.append(lat)
            costs.append(cost)
            avg_scores.append(score)

            print(f"  [{i:02d}] {q[:45]:<45} | {lat:>5}ms | ${cost:.5f} | score={score:.3f}")

            results.append({
                "question":     q,
                "answer":       d.get("answer", "")[:150],
                "latency_ms":   lat,
                "cost_usd":     cost,
                "avg_score":    round(score, 4),
                "sources_count": len(srcs),
            })

        except Exception as e:
            print(f"  [{i:02d}] ERROR: {e}")

        time.sleep(REQUEST_DELAY_S)

    # Calcula p95 de latencia
    sorted_lat = sorted(latencies)
    if sorted_lat:
        p95_idx = int(len(sorted_lat) * 0.95)
        p95_lat = sorted_lat[min(p95_idx, len(sorted_lat) - 1)]
        p50_lat = sorted_lat[len(sorted_lat) // 2]
    else:
        p95_lat = p50_lat = 0

    summary = {
        "strategy":         strategy,
        "questions_tested": len(QUESTIONS),
        "latency_p50_ms":   p50_lat,
        "latency_p95_ms":   p95_lat,
        "avg_cost_usd":     round(sum(costs) / len(costs), 5) if costs else 0,
        "total_cost_usd":   round(sum(costs), 5),
        "avg_retrieval_score": round(sum(avg_scores) / len(avg_scores), 4) if avg_scores else 0,
        "results":          results,
    }

    print(f"\n  Latencia p50: {summary['latency_p50_ms']}ms")
    print(f"  Latencia p95: {summary['latency_p95_ms']}ms")
    print(f"  Costo total:  ${summary['total_cost_usd']:.4f}")
    print(f"  Score prom:   {summary['avg_retrieval_score']:.4f}")

    return summary


def print_comparison_table(summaries: list[dict]):
    """Imprime tabla comparativa en terminal."""
    print(f"\n{'='*70}")
    print("  COMPARATIVA FINAL")
    print(f"{'='*70}")
    print(f"  {'Estrategia':<12} {'p50':<8} {'p95':<8} {'Score':<8} {'Costo/10q'}")
    print(f"  {'-'*58}")
    for s in summaries:
        print(
            f"  {s['strategy']:<12} "
            f"{s['latency_p50_ms']:>5}ms  "
            f"{s['latency_p95_ms']:>5}ms  "
            f"{s['avg_retrieval_score']:.4f}   "
            f"${s['total_cost_usd']:.4f}"
        )
    print(f"{'='*70}")
    print("\n  NOTA: 'Score' es similitud coseno promedio del vector search.")
    print("  Para Faithfulness real, corre el eval suite con RAGAS (Sprint 3).")


def main():
    print("\nComparativa de estrategias de chunking — SupportRAG Sprint 2")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Preguntas por estrategia: {len(QUESTIONS)}")

    summaries = []
    for strategy in STRATEGIES:
        summary = run_strategy(strategy)
        summaries.append(summary)

    print_comparison_table(summaries)

    # Guarda resultados
    output = {
        "run_at":    datetime.now().isoformat(),
        "summaries": summaries,
    }
    out_path = Path("results/chunking_comparison.json")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\n  Resultados guardados en {out_path}")
    print("  Usa estos números para la tabla comparativa del README.")


if __name__ == "__main__":
    main()
