import asyncio
import os
import sys

from app.core.config import settings
from app.services.llm.claude_provider import ClaudeProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.deepseek_provider import DeepSeekProvider
from app.services.llm.deepseek_openrouter_provider import DeepSeekOpenRouterProvider
from app.services.llm.qwen_provider import QwenProvider

async def main():
    providers = [
        ClaudeProvider(),
        OpenAIProvider(),
        DeepSeekProvider(),
        DeepSeekOpenRouterProvider(),
        QwenProvider()
    ]
    
    messages = [{"role": "user", "content": "Salom, qisqacha javob ber"}]
    
    for p in providers:
        if p.is_configured():
            print(f"Testing {p.display_name()}...")
            try:
                gen = p.stream("You are a helpful assistant.", messages, max_tokens=20)
                # Just get the first token
                first_token = None
                async for chunk in gen:
                    if isinstance(chunk, str) and chunk.strip():
                        first_token = chunk
                        break
                print(f"  [SUCCESS] First token: {repr(first_token)}")
            except Exception as e:
                print(f"  [ERROR] {type(e).__name__}: {e}")
        else:
            print(f"Skipping {p.display_name()} (not configured)")

if __name__ == "__main__":
    asyncio.run(main())
