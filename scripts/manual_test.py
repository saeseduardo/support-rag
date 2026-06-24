"""
Prueba manual del endpoint /query con preguntas reales.
Guarda los resultados en data/test_results.json — estos seran
el seed del eval dataset en el Sprint 3 con RAGAS.

Uso:
    uvicorn src.main:app --reload  (en otra terminal)
    python scripts/manual_test.py
"""
import json
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Reemplaza con las preguntas reales de tu equipo de soporte
QUESTIONS = [
    "Como reseteo mi password?",
    "Cuales son los limites del plan gratuito?",
    "Como exporto mis datos en formato CSV?",
    "Donde puedo ver el historial de facturacion?",
    "Como agrego un nuevo usuario al equipo?",
    "Que pasa si supero el limite de llamadas a la API?",
    "Como configuro las notificaciones por email?",
    "Puedo integrar esto con Slack?",
    "Como cancelo mi suscripcion?",
    "Donde estan los logs de actividad?",
]


def run_tests():
    results = []
    total_cost = 0.0

    print(f"\nTesteando {len(QUESTIONS)} preguntas contra {BASE_URL}/query\n")
    print("-" * 60)

    for i, question in enumerate(QUESTIONS, 1):
        try:
            response = httpx.post(
                f"{BASE_URL}/query",
                json={"query": question},
                timeout=30.0,
            )
            data = response.json()

            total_cost += data.get("cost_usd", 0)
            latency = data.get("latency", {}).get("total_ms", 0)
            sources = data.get("sources", [])

            print(f"[{i:02d}] Q: {question}")
            print(f"      A: {data['answer'][:120]}...")
            print(f"      Costo: ${data['cost_usd']:.5f} | Latencia: {latency}ms | Fuentes: {len(sources)}")
            print()

            results.append({
                "id": i,
                "question": question,
                "answer": data["answer"],
                "sources": [s["source_file"] for s in sources],
                "latency_ms": latency,
                "cost_usd": data["cost_usd"],
                "tokens": data.get("tokens_used", 0),
                # Rellena esto manualmente despues de leer cada respuesta:
                # "quality": "correct" | "partial" | "incorrect"
                "quality": "pending",
            })

        except Exception as e:
            print(f"[{i:02d}] ERROR: {e}")
            results.append({"id": i, "question": question, "error": str(e)})

    print("-" * 60)
    print(f"Costo total de la prueba: ${total_cost:.4f}")
    print(f"Costo promedio por query: ${total_cost/len(QUESTIONS):.5f}")

    output = {
        "run_at": datetime.now().isoformat(),
        "total_questions": len(QUESTIONS),
        "total_cost_usd": round(total_cost, 5),
        "results": results,
    }

    with open("data/test_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nResultados guardados en data/test_results.json")
    print("Abre el archivo y rellena el campo 'quality' para cada respuesta.")
    print("Ese archivo sera el seed del eval dataset en el Sprint 3.")


if __name__ == "__main__":
    run_tests()
