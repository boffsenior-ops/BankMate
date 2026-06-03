from typing import List, Dict, Any, Tuple
from app.core.config import settings

SYSTEM_PROMPT = """
Siz BankMate tizimining sun'iy intellektli yordamchisiz.
Sizning vazifangiz bank xodimlarining savollariga FAQAT berilgan hujjatlar (context) asosida javob berishdir.

QOIDALAR:
1. FAQAT taqdim etilgan matn (context) asosida javob bering. O'zingizdan hech qanday ma'lumot qo'shmang.
2. Agar berilgan matnda savolga javob topilmasa, "Javob mavjud emas" deb ayting.
3. Javobingizda doim qaysi hujjat va qaysi sahifadan olinganini ko'rsating (Masalan: "[Kredit Yo'riqnomasi, 12-sahifa]").
4. Javobingizni o'zbek tilida, rasmiy va tushunarli uslubda yozing.
"""


async def generate_answer(
    query: str,
    retrieved_chunks: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any], str, bool]:
    """
    Generates an answer using LLMRouter (5-provider failover).
    Returns (answer, sources, usage_event, provider_name, was_failover).
    usage_event is the raw usage dict from the router.
    """
    if not retrieved_chunks:
        return (
            "Javob mavjud emas. Kerakli ma'lumot bazada topilmadi.",
            [],
            {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "latency_ms": 0},
            "",
            False
        )

    # Build context string
    context_parts = []
    sources = []
    for i, chunk in enumerate(retrieved_chunks):
        title = chunk.get("title", "Noma'lum hujjat")
        page = chunk.get("page_number", "Noma'lum sahifa")
        content = chunk.get("content", "")
        context_parts.append(f"--- HUJJAT {i+1}: {title} (Sahifa: {page}) ---\n{content}\n")
        sources.append({
            "document_id": chunk.get("document_id"),
            "title": title,
            "page_number": page,
            "score": chunk.get("score")
        })

    context_text = "\n".join(context_parts)
    prompt = f"Kontekst ma'lumotlari:\n{context_text}\n\nFoydalanuvchi savoli: {query}"

    from app.services.llm.router import get_llm_router
    router = get_llm_router()

    answer = ""
    provider_name = ""
    was_failover = False
    usage_event: Dict[str, Any] = {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "latency_ms": 0}

    async for event in router.stream(
        system_prompt=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    ):
        etype = event.get("type")
        if etype == "provider_start":
            provider_name = event["name"]
        elif etype == "token":
            answer += event.get("content", "")
        elif etype == "usage":
            usage_event = event
            provider_name = event.get("provider", provider_name)
            was_failover = event.get("was_failover", False)

    return answer, sources, usage_event, provider_name, was_failover
