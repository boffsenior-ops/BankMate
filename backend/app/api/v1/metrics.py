"""Prometheus-format /metrics endpoint for BankMate."""
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbDep
from app.models.models import Conversation, Document, Message, User

router = APIRouter(tags=["observability"])


@router.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
async def metrics(db: DbDep):
    """Basic Prometheus-compatible metrics endpoint."""
    try:
        users_total = (await db.execute(select(func.count(User.id)))).scalar() or 0
        active_users = (
            await db.execute(select(func.count(User.id)).where(User.is_active == True))
        ).scalar() or 0
        docs_total = (
            await db.execute(select(func.count(Document.id)).where(Document.status != "deleted"))
        ).scalar() or 0
        docs_indexed = (
            await db.execute(select(func.count(Document.id)).where(Document.status == "indexed"))
        ).scalar() or 0
        conversations_total = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0
        messages_total = (await db.execute(select(func.count(Message.id)))).scalar() or 0

        lines = [
            "# HELP bankmate_users_total Total registered users",
            "# TYPE bankmate_users_total gauge",
            f"bankmate_users_total {users_total}",
            "# HELP bankmate_active_users_total Active users",
            "# TYPE bankmate_active_users_total gauge",
            f"bankmate_active_users_total {active_users}",
            "# HELP bankmate_documents_total Total documents (non-deleted)",
            "# TYPE bankmate_documents_total gauge",
            f"bankmate_documents_total {docs_total}",
            "# HELP bankmate_indexed_documents_total Indexed documents in vector store",
            "# TYPE bankmate_indexed_documents_total gauge",
            f"bankmate_indexed_documents_total {docs_indexed}",
            "# HELP bankmate_conversations_total Total conversations",
            "# TYPE bankmate_conversations_total gauge",
            f"bankmate_conversations_total {conversations_total}",
            "# HELP bankmate_messages_total Total messages",
            "# TYPE bankmate_messages_total gauge",
            f"bankmate_messages_total {messages_total}",
        ]
        return "\n".join(lines) + "\n"
    except Exception as e:
        return f"# ERROR: {e}\n"
