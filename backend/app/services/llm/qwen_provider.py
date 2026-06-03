import time
import openai
from typing import AsyncGenerator
from app.core.config import settings
from .base import LLMProvider
from .exceptions import (
    LLMRateLimitError,
    LLMAuthError,
    LLMQuotaError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMServerError,
    LLMError
)

class QwenProvider(LLMProvider):
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE,
            timeout=settings.LLM_TIMEOUT_SECONDS
        )
        self.model = settings.OPENROUTER_QWEN_MODEL

    def name(self) -> str:
        return "qwen"

    def display_name(self) -> str:
        return "Qwen3-Max"

    def is_configured(self) -> bool:
        k = settings.OPENROUTER_API_KEY
        return bool(k and k.strip() and k.strip().lower() != "null" and "your" not in k.lower() and len(k) >= 20)

    def pricing(self) -> dict[str, float]:
        return {"input_per_1m": 0.78, "output_per_1m": 3.90}

    async def stream(self, system_prompt: str, messages: list[dict], max_tokens: int = 1024) -> AsyncGenerator[str | dict, None]:
        start_time = time.time()
        
        formatted_messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                max_tokens=max_tokens,
                temperature=0.1,
                stream=True,
                stream_options={"include_usage": True}
            )
            
            prompt_tokens = 0
            completion_tokens = 0
            
            async for chunk in stream:
                if len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                
                if chunk.usage:
                    prompt_tokens = chunk.usage.prompt_tokens
                    completion_tokens = chunk.usage.completion_tokens

            latency_ms = int((time.time() - start_time) * 1000)
            cost_usd = (prompt_tokens * self.pricing()["input_per_1m"] / 1000000) + (completion_tokens * self.pricing()["output_per_1m"] / 1000000)
            
            yield {
                "type": "usage",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms
            }

        except openai.RateLimitError as e:
            if "insufficient" in str(e).lower() or "quota" in str(e).lower():
                raise LLMQuotaError(str(e)) from e
            raise LLMRateLimitError(str(e)) from e
        except openai.AuthenticationError as e:
            raise LLMAuthError(str(e)) from e
        except openai.APITimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except openai.APIConnectionError as e:
            raise LLMConnectionError(str(e)) from e
        except openai.InternalServerError as e:
            raise LLMServerError(str(e)) from e
        except Exception as e:
            raise LLMError(str(e)) from e
