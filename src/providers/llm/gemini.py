import google.generativeai as genai
from src.providers.llm.base import BaseLLMProvider, LLMResponse
from src.config import settings
import os

class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self._model = genai.GenerativeModel(
            model_name=settings.llm_model,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=800,
            ),
        )

    def complete(self, prompt: str, system: str = "") -> LLMResponse:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = self._model.generate_content(full_prompt)
        usage = response.usage_metadata
        return LLMResponse(
            content=response.text,
            input_tokens=usage.prompt_token_count,
            output_tokens=usage.candidates_token_count,
            model=settings.llm_model,
        )

    def cost_per_token(self) -> dict:
        return {"input": 0.00000010, "output": 0.00000040}
