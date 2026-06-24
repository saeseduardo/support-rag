from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    model: str

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BaseLLMProvider(ABC):
    """
    Contrato que todos los proveedores de LLM deben cumplir.
    Cambiar de OpenAI a Gemini = cambiar 1 linea en config.py
    """

    @abstractmethod
    def complete(self, prompt: str, system: str = "") -> LLMResponse:
        """Genera una respuesta dado un prompt."""
        ...

    @abstractmethod
    def cost_per_token(self) -> dict:
        """Devuelve {'input': precio, 'output': precio} en USD por token."""
        ...

    def calculate_cost(self, response: LLMResponse) -> float:
        prices = self.cost_per_token()
        return (
            response.input_tokens  * prices["input"] +
            response.output_tokens * prices["output"]
        )
