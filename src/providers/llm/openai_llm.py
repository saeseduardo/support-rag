import openai as _openai
from src.providers.llm.base import BaseLLMProvider, LLMResponse
from src.config import settings


class OpenAIProvider(BaseLLMProvider):
    """
    Proveedor OpenAI.
    Modelo por defecto: gpt-4o-mini
    """

    def __init__(self):
        self._client = _openai.OpenAI(api_key=settings.openai_api_key)

    def complete(self, prompt: str, system: str = "") -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.1,
            max_tokens=800,
        )
        usage = response.usage
        return LLMResponse(
            content=response.choices[0].message.content,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            model=settings.llm_model,
        )

    def cost_per_token(self) -> dict:
        # gpt-4o-mini pricing
        return {
            "input":  0.00000015,   # $0.15 / 1M tokens
            "output": 0.00000060,   # $0.60 / 1M tokens
        }
