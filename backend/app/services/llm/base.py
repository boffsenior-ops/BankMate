from abc import ABC, abstractmethod
from typing import AsyncGenerator

class LLMProvider(ABC):
    @abstractmethod
    async def stream(self, system_prompt: str, messages: list[dict], max_tokens: int = 1024) -> AsyncGenerator[str | dict, None]:
        """
        Yields string tokens.
        At the very end, yields a dict: {"type": "usage", "prompt_tokens": x, "completion_tokens": y, "cost_usd": z, "latency_ms": t}
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """Logical identifier (e.g., 'anthropic', 'openai')"""
        pass

    @abstractmethod
    def display_name(self) -> str:
        """Human-readable for UI badge"""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider keys are configured properly"""
        pass

    @abstractmethod
    def pricing(self) -> dict[str, float]:
        """Returns pricing per 1M tokens: {"input_per_1m": float, "output_per_1m": float}"""
        pass
