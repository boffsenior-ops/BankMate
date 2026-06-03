import asyncio
import logging
import time
import traceback
from typing import AsyncGenerator

from redis.asyncio import Redis

from app.core.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.claude_provider import ClaudeProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.deepseek_provider import DeepSeekProvider
from app.services.llm.deepseek_openrouter_provider import DeepSeekOpenRouterProvider
from app.services.llm.qwen_provider import QwenProvider
from app.services.llm.exceptions import (
    LLMRateLimitError, LLMAuthError, LLMQuotaError,
    LLMConnectionError, LLMTimeoutError, LLMServerError, LLMError
)

logger = logging.getLogger(__name__)

# Patterns that indicate error even in a HTTP 200 body
ERROR_BODY_PATTERNS = [
    "error:", "internal server error", "rate limit", "rate_limit",
    "unauthorized", "quota exceeded", "model not found",
    "context length exceeded", "bad request"
]

PLACEHOLDER_PATTERNS = ["your", "xxxxx", "sk-ant-xxxxx", "your-key", "placeholder", "change_me"]


class ConfigurationError(Exception):
    pass


def _is_valid_key(key: str | None, env_var: str) -> tuple[bool, str]:
    """
    Returns (is_valid, reason_if_not).
    Never logs the key value itself.
    """
    if not key:
        return False, f"{env_var} is empty"
    k = key.strip()
    if not k:
        return False, f"{env_var} is whitespace-only"
    if k.lower() in ("null", "none", ""):
        return False, f"{env_var} is null/none"
    if any(p in k.lower() for p in PLACEHOLDER_PATTERNS):
        return False, f"{env_var} looks like a placeholder"
    if len(k) < 20:
        return False, f"{env_var} too short (< 20 chars)"
    return True, ""


def _check_error_in_buffer(buffer: str) -> bool:
    """Return True if buffer matches known error patterns."""
    buf_lower = buffer.lower().strip()
    return any(pat in buf_lower for pat in ERROR_BODY_PATTERNS)


class LLMRouter:
    """
    Routes LLM requests to a priority-ordered list of configured providers.
    Implements pre-commit buffering, exception-based failover, cooldown via Redis.
    """

    def __init__(self):
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

        provider_classes = {
            "anthropic": (ClaudeProvider, "ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY),
            "openai": (OpenAIProvider, "OPENAI_API_KEY", settings.OPENAI_API_KEY),
            "deepseek": (DeepSeekProvider, "DEEPSEEK_API_KEY", settings.DEEPSEEK_API_KEY),
            "deepseek_or": (DeepSeekOpenRouterProvider, "OPENROUTER_API_KEY", settings.OPENROUTER_API_KEY),
            "qwen": (QwenProvider, "OPENROUTER_API_KEY", settings.OPENROUTER_API_KEY),
        }

        order = [p.strip() for p in settings.LLM_PROVIDER_ORDER.split(",") if p.strip()]

        self.providers: list[LLMProvider] = []
        for p_name in order:
            if p_name not in provider_classes:
                logger.warning(f"LLMRouter: Unknown provider '{p_name}' in LLM_PROVIDER_ORDER, skipping.")
                continue
            cls, env_var, key_val = provider_classes[p_name]
            valid, reason = _is_valid_key(key_val, env_var)
            if not valid:
                logger.info(f"LLMRouter: skipping {p_name}: {reason}")
                continue
            self.providers.append(cls())
            logger.info(f"LLMRouter: provider '{p_name}' is configured and ready.")

        if not self.providers:
            raise ConfigurationError(
                "No LLM providers configured. Set at least one of: "
                "ANTHROPIC_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY, OPENROUTER_API_KEY"
            )

    # ── Cooldown helpers ─────────────────────────────────────────────────────

    async def _in_cooldown(self, name: str) -> bool:
        return bool(await self.redis.exists(f"llm_cooldown:{name}"))

    async def _set_cooldown(self, name: str, seconds: int):
        await self.redis.setex(f"llm_cooldown:{name}", seconds, "1")

    async def _get_cooldown_ttl(self, name: str) -> int:
        ttl = await self.redis.ttl(f"llm_cooldown:{name}")
        return max(ttl, 0)

    # ── Main streaming entry point ────────────────────────────────────────────

    async def stream(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 1024,
    ) -> AsyncGenerator[dict, None]:
        """
        Yields dicts:
          {"type": "provider_start", "name": ..., "display": ...}
          {"type": "token", "content": ...}
          {"type": "usage", "provider": ..., "prompt_tokens": ..., "completion_tokens": ..., "cost_usd": ..., "latency_ms": ...}
          {"type": "done"}
          OR on total failure:
          {"type": "all_failed", "providers_tried": [...], "reasons": [...]}
        """
        start_time = time.time()
        providers_tried: list[str] = []
        reasons: list[str] = []

        first_valid_provider = None
        for p in self.providers:
            if not await self._in_cooldown(p.name()):
                first_valid_provider = p
                break

        if first_valid_provider:
            yield {"type": "provider_start", "name": first_valid_provider.name(), "display": first_valid_provider.display_name()}

        for provider in self.providers:
            p_name = provider.name()

            # A) Pre-call: cooldown check
            if await self._in_cooldown(p_name):
                ttl = await self._get_cooldown_ttl(p_name)
                logger.info(f"LLMRouter: skipping {p_name} (in cooldown, {ttl}s remaining)")
                continue

            providers_tried.append(p_name)
            attempt_start = time.time()

            # We implement pre-commit buffering here
            buffer_tokens: list[str] = []
            buffer_chars = 0
            PRE_COMMIT_TOKENS = 50
            PRE_COMMIT_CHARS = 200
            committed = False
            usage_event: dict | None = None
            fail_reason: str | None = None

            try:
                gen = provider.stream(system_prompt, messages, max_tokens)

                # --- Pre-commit phase: collect first 50 tokens / 200 chars ---
                first_token_deadline = attempt_start + settings.LLM_TIMEOUT_SECONDS / 2

                async for chunk in gen:
                    # Usage dict signals end of stream
                    if isinstance(chunk, dict):
                        usage_event = chunk
                        break

                    # Timeout check before we've committed
                    if not committed and time.time() > first_token_deadline and not buffer_tokens:
                        fail_reason = "timeout_no_first_token"
                        break

                    token = chunk
                    buffer_tokens.append(token)
                    buffer_chars += len(token)

                    # Once buffer is full enough, validate it
                    if not committed and (len(buffer_tokens) >= PRE_COMMIT_TOKENS or buffer_chars >= PRE_COMMIT_CHARS):
                        buffered_text = "".join(buffer_tokens)
                        # C) Content-based checks
                        if not buffered_text.strip():
                            fail_reason = "empty_or_whitespace_response"
                            break
                        if len(buffered_text.strip()) < 3:
                            fail_reason = "response_too_short"
                            break
                        if _check_error_in_buffer(buffered_text):
                            fail_reason = f"error_pattern_in_body: {buffered_text[:80]!r}"
                            break

                        # Buffer passed — commit and stream it out
                        committed = True
                        for t in buffer_tokens:
                            yield {"type": "token", "content": t}
                        buffer_tokens = []

                    elif committed:
                        # Already committed: stream directly
                        yield {"type": "token", "content": token}

                # After loop: if not yet committed, validate remaining buffer
                if not committed and not fail_reason:
                    buffered_text = "".join(buffer_tokens)
                    if not buffered_text.strip():
                        fail_reason = "empty_or_whitespace_response"
                    elif len(buffered_text.strip()) < 3:
                        fail_reason = "response_too_short"
                    elif _check_error_in_buffer(buffered_text):
                        fail_reason = f"error_pattern_in_body: {buffered_text[:80]!r}"
                    else:
                        # Small response that never hit the buffer threshold — commit it
                        committed = True
                        for t in buffer_tokens:
                            yield {"type": "token", "content": t}

            except LLMRateLimitError as e:
                cooldown = settings.LLM_COOLDOWN_RATE_LIMIT_MIN * 60
                fail_reason = f"rate_limit: {e}"
                await self._set_cooldown(p_name, cooldown)
                logger.info(f"LLMRouter: {p_name} rate-limited, cooldown {cooldown}s. Trying next.")
                reasons.append(f"{p_name}:rate_limit")
                continue

            except LLMAuthError as e:
                cooldown = settings.LLM_COOLDOWN_AUTH_ERROR_MIN * 60
                fail_reason = f"auth_error: {e}"
                await self._set_cooldown(p_name, cooldown)
                logger.info(f"LLMRouter: {p_name} auth error, cooldown {cooldown}s. Trying next.")
                reasons.append(f"{p_name}:auth_error")
                continue

            except LLMQuotaError as e:
                cooldown = 30 * 60  # 30 min
                fail_reason = f"quota_exceeded: {e}"
                await self._set_cooldown(p_name, cooldown)
                logger.info(f"LLMRouter: {p_name} quota exceeded, cooldown 30min. Trying next.")
                reasons.append(f"{p_name}:quota_exceeded")
                continue

            except LLMTimeoutError as e:
                cooldown = 60
                fail_reason = f"timeout: {e}"
                await self._set_cooldown(p_name, cooldown)
                logger.info(f"LLMRouter: {p_name} timeout, cooldown 60s. Trying next.")
                reasons.append(f"{p_name}:timeout")
                continue

            except LLMConnectionError as e:
                cooldown = 30
                fail_reason = f"connection_error: {e}"
                await self._set_cooldown(p_name, cooldown)
                logger.info(f"LLMRouter: {p_name} connection error, cooldown 30s. Trying next.")
                reasons.append(f"{p_name}:connection_error")
                continue

            except LLMServerError as e:
                cooldown = 2 * 60
                fail_reason = f"server_error: {e}"
                await self._set_cooldown(p_name, cooldown)
                logger.info(f"LLMRouter: {p_name} server error, cooldown 2min. Trying next.")
                reasons.append(f"{p_name}:server_error")
                continue

            except Exception as e:
                cooldown = 60
                fail_reason = f"unexpected: {e}"
                await self._set_cooldown(p_name, cooldown)
                logger.warning(
                    f"LLMRouter: {p_name} unexpected error, cooldown 60s.\n{traceback.format_exc()}"
                )
                reasons.append(f"{p_name}:unexpected")
                continue

            # If we got a fail_reason from content checks, apply cooldown and continue
            if fail_reason and not committed:
                cooldown = 60
                await self._set_cooldown(p_name, cooldown)
                logger.info(
                    f"LLMRouter: {p_name} content-based failover ({fail_reason}), "
                    f"elapsed {time.time()-attempt_start:.1f}s. Trying next."
                )
                reasons.append(f"{p_name}:{fail_reason}")
                continue

            # Mid-stream break detection: committed but no usage event received
            if committed and usage_event is None:
                logger.error(f"LLMRouter: {p_name} stream broken mid-stream (no usage/done signal).")
                yield {"type": "stream_broken"}
                return

            # SUCCESS
            if usage_event:
                latency_ms = int((time.time() - attempt_start) * 1000)
                is_failover = (p_name != self.providers[0].name())
                yield {
                    "type": "usage",
                    "provider": p_name,
                    "display": provider.display_name(),
                    "prompt_tokens": usage_event.get("prompt_tokens", 0),
                    "completion_tokens": usage_event.get("completion_tokens", 0),
                    "cost_usd": usage_event.get("cost_usd", 0.0),
                    "latency_ms": latency_ms,
                    "was_failover": is_failover,
                }
            yield {"type": "done"}
            return

        # ALL providers failed
        logger.error(
            f"LLMRouter: All providers failed. tried={providers_tried}, reasons={reasons}, "
            f"total_elapsed={time.time()-start_time:.1f}s"
        )
        yield {
            "type": "token",
            "content": "Hozir AI xizmati vaqtinchalik mavjud emas. Iltimos, birozdan keyin qayta urinib ko'ring.",
        }
        yield {"type": "all_failed", "providers_tried": providers_tried, "reasons": reasons}
        yield {"type": "done"}

    # ── Admin sync helper ─────────────────────────────────────────────────────

    async def test_provider(self, provider_name: str) -> dict:
        """
        Direct single-provider test for admin endpoints.
        Returns {"success": bool, "display": str, "response": str, "latency_ms": int, "reason": str}
        """
        target = next((p for p in self.providers if p.name() == provider_name), None)
        if not target:
            return {"success": False, "display": provider_name, "response": "", "latency_ms": 0, "reason": "not_configured"}

        start = time.time()
        buffer = []
        try:
            async for chunk in target.stream("You are a helpful assistant.", [{"role": "user", "content": "Bir gapda javob: 2+2 nechi?"}], max_tokens=50):
                if isinstance(chunk, str):
                    buffer.append(chunk)
                elif isinstance(chunk, dict) and chunk.get("type") == "usage":
                    break

            response = "".join(buffer)
            latency = int((time.time() - start) * 1000)

            if not response.strip():
                return {"success": False, "display": target.display_name(), "response": "", "latency_ms": latency, "reason": "empty_response"}
            if _check_error_in_buffer(response):
                return {"success": False, "display": target.display_name(), "response": response[:200], "latency_ms": latency, "reason": "error_pattern_in_body"}

            return {"success": True, "display": target.display_name(), "response": response[:500], "latency_ms": latency, "reason": ""}

        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return {"success": False, "display": target.display_name(), "response": "", "latency_ms": latency, "reason": type(e).__name__}

    async def provider_statuses(self) -> list[dict]:
        """Returns status of all providers in order for admin UI."""
        result = []
        for p in self.providers:
            in_cd = await self._in_cooldown(p.name())
            ttl = await self._get_cooldown_ttl(p.name()) if in_cd else 0
            result.append({
                "name": p.name(),
                "display": p.display_name(),
                "configured": True,
                "in_cooldown": in_cd,
                "cooldown_ttl_sec": ttl,
            })
        return result


# ── Singleton ─────────────────────────────────────────────────────────────────

_llm_router: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
