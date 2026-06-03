import time
import anthropic
from typing import AsyncGenerator
from app.core.config import settings
from .base import LLMProvider
from .exceptions import (
    LLMRateLimitError,
    LLMAuthError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMServerError,
    LLMError
)

class ClaudeProvider(LLMProvider):
    def __init__(self):
        # We assume is_configured() is checked before stream is called
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=settings.LLM_TIMEOUT_SECONDS
        )

    def name(self) -> str:
        return "anthropic"

    def display_name(self) -> str:
        return "Claude Sonnet 4.5"

    def is_configured(self) -> bool:
        k = settings.ANTHROPIC_API_KEY
        return bool(k and k.strip() and k.strip().lower() != "null" and "your" not in k.lower() and len(k) >= 20)

    def pricing(self) -> dict[str, float]:
        return {"input_per_1m": 3.0, "output_per_1m": 15.0}

    async def stream(self, system_prompt: str, messages: list[dict], max_tokens: int = 1024) -> AsyncGenerator[str | dict, None]:
        start_time = time.time()
        try:
            stream = await self.client.messages.create(
                model="claude-3-5-sonnet-latest",
                system=system_prompt,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1,
                stream=True
            )
            
            prompt_tokens = 0
            completion_tokens = 0
            
            async for event in stream:
                if event.type == "message_start":
                    prompt_tokens = event.message.usage.input_tokens
                elif event.type == "content_block_delta":
                    yield event.delta.text
                elif event.type == "message_delta":
                    completion_tokens = event.usage.output_tokens

            latency_ms = int((time.time() - start_time) * 1000)
            cost_usd = (prompt_tokens * self.pricing()["input_per_1m"] / 1000000) + (completion_tokens * self.pricing()["output_per_1m"] / 1000000)
            
            yield {
                "type": "usage",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms
            }

        except anthropic.RateLimitError as e:
            raise LLMRateLimitError(str(e)) from e
        except anthropic.AuthenticationError as e:
            raise LLMAuthError(str(e)) from e
        except anthropic.APITimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except anthropic.APIConnectionError as e:
            raise LLMConnectionError(str(e)) from e
        except anthropic.InternalServerError as e:
            raise LLMServerError(str(e)) from e
        except Exception as e:
            raise LLMError(str(e)) from e
