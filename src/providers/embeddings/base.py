from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):
    """
    Contrato que todos los proveedores de embeddings deben cumplir.
    """

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para una lista de textos."""
        ...

    @abstractmethod
    def dimensions(self) -> int:
        """Dimensiones del vector de embedding. Debe coincidir con pgvector."""
        ...

    @abstractmethod
    def cost_per_million_tokens(self) -> float:
        """Precio en USD por millon de tokens embeddeados."""
        ...
