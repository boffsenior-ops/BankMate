import asyncio
import json
import time
from typing import AsyncIterator, List

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DbDep
from app.models.models import Conversation, Message, LlmUsage
from app.schemas.chat import QueryRequest, QueryResponse
from app.services.rag.generator import SYSTEM_PROMPT, generate_answer
from app.services.rag.retriever import retrieve_relevant_chunks

router = APIRouter(prefix="/chat", tags=["chat"])


class FeedbackRequest(BaseModel):
    feedback: str  # "like" | "dislike"


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest, db: DbDep, current_user: CurrentUser) -> QueryResponse:
    """Non-streaming chat endpoint. Returns full answer with sources."""
    chunks = await retrieve_relevant_chunks(request.query)
    answer, sources, usage_event, provider_name, was_failover = await generate_answer(request.query, chunks)

    conversation_id = request.conversation_id
    if not conversation_id:
        conv = Conversation(user_id=current_user.id, title=request.query[:50])
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conversation_id = conv.id

    user_msg = Message(conversation_id=conversation_id, role="user", content=request.query)
    db.add(user_msg)

    ai_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        sources_json=sources,
    )
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    usage_record = LlmUsage(
        conversation_id=conversation_id,
        message_id=ai_msg.id,
        provider=provider_name or "unknown",
        model=_provider_model(provider_name),
        prompt_tokens=usage_event.get("prompt_tokens", 0),
        completion_tokens=usage_event.get("completion_tokens", 0),
        total_tokens=(usage_event.get("prompt_tokens", 0) + usage_event.get("completion_tokens", 0)),
        estimated_cost_usd=usage_event.get("cost_usd", 0.0),
        latency_ms=usage_event.get("latency_ms", 0),
        was_failover=was_failover,
    )
    db.add(usage_record)
    await db.commit()

    usage_out = {
        "input_tokens": usage_event.get("prompt_tokens", 0),
        "output_tokens": usage_event.get("completion_tokens", 0),
    }
    return QueryResponse(
        answer=answer,
        sources=sources,
        conversation_id=conversation_id,
        message_id=ai_msg.id,
        usage=usage_out,
    )


@router.post("/stream")
async def stream_rag(
    request: QueryRequest,
    db: DbDep,
    current_user: CurrentUser,
) -> StreamingResponse:
    """
    Streaming chat endpoint using Server-Sent Events.
    Events: provider_start, token, usage, done, all_failed, stream_broken, error
    """

    async def event_stream() -> AsyncIterator[str]:
        # ── Retrieval ─────────────────────────────────────────────────────────
        try:
            chunks = await retrieve_relevant_chunks(request.query)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Qidiruv xatosi: {type(e).__name__}'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        if not chunks:
            _no_answer = "Javob mavjud emas. Kerakli ma\u02bclumot bazada topilmadi."
            yield f"data: {json.dumps({'type': 'token', 'content': _no_answer})}\n\n"
            yield f"data: {json.dumps({'type': 'sources', 'sources': []})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # ── Build context ────────────────────────────────────────────────────
        context_parts, sources = [], []
        for i, chunk in enumerate(chunks):
            title = chunk.get("title", "Noma'lum hujjat")
            page = chunk.get("page_number", "?")
            context_parts.append(
                f"--- HUJJAT {i+1}: {title} (Sahifa: {page}) ---\n{chunk.get('content', '')}\n"
            )
            sources.append({
                "document_id": chunk.get("document_id"),
                "title": title,
                "page_number": page,
                "score": chunk.get("score"),
            })

        context_text = "\n".join(context_parts)
        _kontekst = "Kontekst ma\u02bclumotlari"
        _savol = "Foydalanuvchi savoli"
        prompt = f"{_kontekst}:\n{context_text}\n\n{_savol}: {request.query}"

        # ── LLM streaming ────────────────────────────────────────────────────
        from app.services.llm.router import get_llm_router
        router_instance = get_llm_router()

        full_answer = ""
        provider_name = "unknown"
        was_failover = False
        usage_event: dict = {}

        stream_gen = router_instance.stream(
            system_prompt=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )

        try:
            async for event in stream_gen:
                etype = event.get("type")

                if etype == "provider_start":
                    provider_name = event["name"]
                    yield f"data: {json.dumps({'type': 'provider_start', 'name': event['name'], 'display': event['display']})}\n\n"

                elif etype == "token":
                    content = event.get("content", "")
                    full_answer += content
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

                elif etype == "usage":
                    usage_event = event
                    provider_name = event.get("provider", provider_name)
                    was_failover = event.get("was_failover", False)
                    yield f"data: {json.dumps({'type': 'usage', 'provider': event.get('provider', provider_name), 'display': event.get('display', ''), 'prompt_tokens': event.get('prompt_tokens', 0), 'completion_tokens': event.get('completion_tokens', 0), 'cost_usd': event.get('cost_usd', 0.0), 'latency_ms': event.get('latency_ms', 0)})}\n\n"

                elif etype == "all_failed":
                    yield f"data: {json.dumps({'type': 'all_failed', 'providers_tried': event.get('providers_tried', []), 'reasons': event.get('reasons', [])})}\n\n"

                elif etype == "stream_broken":
                    yield f"data: {json.dumps({'type': 'stream_broken'})}\n\n"
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return

                elif etype == "done":
                    pass  # handled below

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Javob yaratish xatosi: {type(e).__name__}'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # ── Save to DB (after stream ends) ───────────────────────────────────
        conversation_id = request.conversation_id
        if not conversation_id:
            conv = Conversation(user_id=current_user.id, title=request.query[:50])
            db.add(conv)
            await db.commit()
            await db.refresh(conv)
            conversation_id = conv.id

        user_msg = Message(conversation_id=conversation_id, role="user", content=request.query)
        db.add(user_msg)

        ai_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_answer,
            sources_json=sources,
        )
        db.add(ai_msg)
        await db.commit()
        await db.refresh(ai_msg)

        if usage_event or provider_name != "unknown":
            usage_record = LlmUsage(
                conversation_id=conversation_id,
                message_id=ai_msg.id,
                provider=provider_name,
                model=_provider_model(provider_name),
                prompt_tokens=usage_event.get("prompt_tokens", 0),
                completion_tokens=usage_event.get("completion_tokens", 0),
                total_tokens=(usage_event.get("prompt_tokens", 0) + usage_event.get("completion_tokens", 0)),
                estimated_cost_usd=usage_event.get("cost_usd", 0.0),
                latency_ms=usage_event.get("latency_ms", 0),
                was_failover=was_failover,
            )
            db.add(usage_record)
            await db.commit()

        yield f"data: {json.dumps({'type': 'sources', 'sources': sources, 'conversation_id': conversation_id, 'message_id': ai_msg.id})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _provider_model(provider_name: str) -> str:
    """Map logical provider name to model identifier."""
    models = {
        "anthropic": "claude-3-5-sonnet-latest",
        "openai": "gpt-4o",
        "deepseek": "deepseek-chat",
        "deepseek_or": "deepseek/deepseek-chat",
        "qwen": "qwen/qwen3-max",
    }
    return models.get(provider_name, "unknown")


@router.get("/conversations")
async def get_conversations(db: DbDep, current_user: CurrentUser):
    """List conversations for the logged in user, ordered by update time."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: int, db: DbDep, current_user: CurrentUser):
    """Get all messages for a specific conversation."""
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(Message, LlmUsage.provider, LlmUsage.was_failover)
        .outerjoin(LlmUsage, Message.id == LlmUsage.message_id)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )

    messages_out = []
    for msg, provider, failover in result.all():
        msg_dict = {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "role": msg.role,
            "content": msg.content,
            "sources_json": msg.sources_json,
            "feedback": msg.feedback,
            "created_at": msg.created_at.isoformat(),
        }
        if provider:
            msg_dict["provider"] = provider
            msg_dict["was_failover"] = failover
        messages_out.append(msg_dict)

    return messages_out


@router.post("/messages/{message_id}/feedback")
async def save_feedback(message_id: int, request: FeedbackRequest, db: DbDep, current_user: CurrentUser):
    """Save feedback (like/dislike) for a message."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == msg.conversation_id)
    )
    conv = conv_result.scalar_one_or_none()
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    msg.feedback = request.feedback
    await db.commit()
    return {"status": "success", "feedback": request.feedback}
