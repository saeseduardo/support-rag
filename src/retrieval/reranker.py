from src.models.schemas import SourceChunk


def rerank(query: str, chunks: list[SourceChunk], top_n: int = 5) -> list[SourceChunk]:
    return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_n]
