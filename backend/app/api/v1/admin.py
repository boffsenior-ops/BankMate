"""Admin API: stats, user management, document management, audit log viewer."""
import csv
import io
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import delete, func, select
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbDep, require_role
from app.core.security import get_password_hash
from app.models.models import AuditLog, Conversation, Document, Message, RoleEnum, User
from app.services.audit import log_action

router = APIRouter(prefix="/admin", tags=["admin"])

AdminDep = require_role([RoleEnum.ADMIN, RoleEnum.CONTENT_MANAGER])
SuperAdminDep = require_role([RoleEnum.ADMIN])


# ─────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: RoleEnum = RoleEnum.USER
    branch_id: int | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    role: RoleEnum | None = None
    branch_id: int | None = None
    is_active: bool | None = None


class PasswordReset(BaseModel):
    new_password: str


# ─────────────────────────────────────────
# Dashboard stats
# ─────────────────────────────────────────

@router.get("/stats")
async def get_stats(
    db: DbDep,
    current_user: User = AdminDep,
):
    """Return counts for the admin dashboard overview."""
    users_count = (await db.execute(func.count(User.id).select())).scalar() or 0
    docs_count = (
        await db.execute(
            select(func.count(Document.id)).where(Document.status != "deleted")
        )
    ).scalar() or 0
    messages_count = (await db.execute(func.count(Message.id).select())).scalar() or 0
    convos_count = (await db.execute(func.count(Conversation.id).select())).scalar() or 0
    indexed_docs = (
        await db.execute(
            select(func.count(Document.id)).where(Document.status == "indexed")
        )
    ).scalar() or 0
    pending_docs = (
        await db.execute(
            select(func.count(Document.id)).where(Document.status.in_(["uploaded", "processing"]))
        )
    ).scalar() or 0

    await log_action(db, "ADMIN_STATS_VIEW", user_id=current_user.id, resource_type="stats")
    return {
        "users": users_count,
        "documents": docs_count,
        "indexed_documents": indexed_docs,
        "pending_documents": pending_docs,
        "conversations": convos_count,
        "messages": messages_count,
    }


# ─────────────────────────────────────────
# User management
# ─────────────────────────────────────────

@router.get("/users")
async def list_users(
    db: DbDep,
    current_user: User = AdminDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    role: RoleEnum | None = None,
    is_active: bool | None = None,
):
    stmt = select(User)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "branch_id": u.branch_id,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    payload: UserCreate,
    db: DbDep,
    current_user: User = SuperAdminDep,
):
    # Check duplicates
    existing = (
        await db.execute(select(User).where(User.username == payload.username))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    existing_email = (
        await db.execute(select(User).where(User.email == payload.email))
    ).scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        branch_id=payload.branch_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await log_action(
        db, "USER_CREATED", user_id=current_user.id,
        resource_type="user", resource_id=str(user.id),
        request=request,
        metadata={"username": payload.username, "role": payload.role.value},
    )
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role}


@router.patch("/users/{user_id}")
async def update_user(
    request: Request,
    user_id: int,
    payload: UserUpdate,
    db: DbDep,
    current_user: User = SuperAdminDep,
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes: dict[str, Any] = {}
    if payload.full_name is not None:
        changes["full_name"] = payload.full_name
        user.full_name = payload.full_name
    if payload.email is not None:
        changes["email"] = payload.email
        user.email = payload.email
    if payload.role is not None:
        changes["role"] = payload.role.value
        user.role = payload.role
    if payload.branch_id is not None:
        changes["branch_id"] = payload.branch_id
        user.branch_id = payload.branch_id
    if payload.is_active is not None:
        changes["is_active"] = payload.is_active
        user.is_active = payload.is_active

    await log_action(
        db, "USER_UPDATED", user_id=current_user.id,
        resource_type="user", resource_id=str(user_id),
        request=request, metadata=changes,
    )
    await db.commit()
    return {"id": user.id, "username": user.username, "role": user.role, "is_active": user.is_active}


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    request: Request,
    user_id: int,
    payload: PasswordReset,
    db: DbDep,
    current_user: User = SuperAdminDep,
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = get_password_hash(payload.new_password)
    await log_action(
        db, "PASSWORD_RESET", user_id=current_user.id,
        resource_type="user", resource_id=str(user_id),
        request=request,
    )
    await db.commit()
    return {"message": "Password reset successfully"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    request: Request,
    user_id: int,
    db: DbDep,
    current_user: User = SuperAdminDep,
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await log_action(
        db, "USER_DEACTIVATED", user_id=current_user.id,
        resource_type="user", resource_id=str(user_id),
        request=request, metadata={"username": user.username},
    )
    await db.commit()
    return None


# ─────────────────────────────────────────
# Document management (admin enhanced)
# ─────────────────────────────────────────

@router.post("/documents/reindex")
async def trigger_reindex_all(db: DbDep, current_user: User = AdminDep):
    result = await db.execute(select(Document).where(Document.status != "deleted"))
    docs = result.scalars().all()
    count = 0
    from app.tasks.document_tasks import process_document_task
    for doc in docs:
        doc.status = "uploaded"
        process_document_task.delay(doc.id)
        count += 1
    await db.commit()
    await log_action(db, "DOCUMENTS_REINDEX_TRIGGERED", user_id=current_user.id, resource_type="system", metadata={"count": count})
    return {"message": f"Queued {count} documents for re-indexing", "count": count}


@router.get("/documents/stats")
async def get_document_indexing_stats(db: DbDep, current_user: User = AdminDep):
    stmt = select(Document.status, func.count(Document.id)).where(Document.status != "deleted").group_by(Document.status)
    result = await db.execute(stmt)
    counts = dict(result.all())
    
    total = sum(counts.values())
    indexed = counts.get("indexed", 0)
    processing = counts.get("processing", 0)
    uploaded = counts.get("uploaded", 0)
    error = counts.get("error", 0)
    
    return {
        "total": total,
        "indexed": indexed,
        "processing": processing,
        "pending": uploaded,
        "error": error
    }

@router.get("/documents")
async def list_all_documents(
    db: DbDep,
    current_user: User = AdminDep,
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    stmt = select(Document)
    if status_filter:
        stmt = stmt.where(Document.status == status_filter)
    else:
        stmt = stmt.where(Document.status != "deleted")
    if category:
        stmt = stmt.where(Document.category == category)
    stmt = stmt.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "category": d.category,
            "file_path": d.file_path,
            "status": d.status,
            "version": d.version,
            "uploaded_by": d.uploaded_by,
            "created_at": d.created_at,
            "indexed_at": d.indexed_at,
        }
        for d in docs
    ]


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_document(
    request: Request,
    doc_id: int,
    db: DbDep,
    current_user: User = SuperAdminDep,
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = "deleted"
    await log_action(
        db, "DOCUMENT_DELETED", user_id=current_user.id,
        resource_type="document", resource_id=str(doc_id),
        request=request, metadata={"title": doc.title, "category": doc.category},
    )
    await db.commit()
    return None


# ─────────────────────────────────────────
# Audit log viewer
# ─────────────────────────────────────────

@router.get("/audit-logs")
async def get_audit_logs(
    db: DbDep,
    current_user: User = AdminDep,
    action: str | None = None,
    user_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc))
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=timezone.utc))
    if search:
        stmt = stmt.where(
            AuditLog.action.ilike(f"%{search}%") |
            AuditLog.resource_type.ilike(f"%{search}%") |
            AuditLog.resource_id.ilike(f"%{search}%")
        )
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "metadata": log.metadata_,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.get("/audit-logs/export")
async def export_audit_logs_csv(
    db: DbDep,
    current_user: User = AdminDep,
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Export audit logs as a CSV download."""
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(5000)
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc))
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=timezone.utc))

    result = await db.execute(stmt)
    logs = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "action", "resource_type", "resource_id", "ip_address", "created_at"])
    for log in logs:
        writer.writerow([log.id, log.user_id, log.action, log.resource_type, log.resource_id, log.ip_address, log.created_at])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )


# ─────────────────────────────────────────
# LLM Usage stats
# ─────────────────────────────────────────

@router.get("/usage")
async def get_llm_usage(
    db: DbDep,
    current_user: User = SuperAdminDep,
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
):
    """
    Per-provider usage summary for a date range (default: last 30 days).
    Returns: requests_count, total_prompt_tokens, total_completion_tokens,
             total_cost_usd, failover_count, avg_latency_ms
    """
    from datetime import timedelta
    from app.models.models import LlmUsage

    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=30)

    from_dt = datetime(from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc)
    to_dt = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, tzinfo=timezone.utc)

    stmt = (
        select(
            LlmUsage.provider,
            func.count(LlmUsage.id).label("requests_count"),
            func.sum(LlmUsage.prompt_tokens).label("total_prompt_tokens"),
            func.sum(LlmUsage.completion_tokens).label("total_completion_tokens"),
            func.sum(LlmUsage.estimated_cost_usd).label("total_cost_usd"),
            func.sum(func.cast(LlmUsage.was_failover, sa.Integer)).label("failover_count"),
            func.avg(LlmUsage.latency_ms).label("avg_latency_ms"),
        )
        .where(LlmUsage.created_at >= from_dt)
        .where(LlmUsage.created_at <= to_dt)
        .group_by(LlmUsage.provider)
        .order_by(func.count(LlmUsage.id).desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    return {
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
        "providers": [
            {
                "provider": r.provider,
                "requests_count": r.requests_count,
                "total_prompt_tokens": r.total_prompt_tokens or 0,
                "total_completion_tokens": r.total_completion_tokens or 0,
                "total_cost_usd": round(r.total_cost_usd or 0.0, 6),
                "failover_count": r.failover_count or 0,
                "avg_latency_ms": round(r.avg_latency_ms or 0, 1),
            }
            for r in rows
        ],
    }


@router.get("/usage/today")
async def get_today_usage(
    db: DbDep,
    current_user: User = SuperAdminDep,
):
    """Total usage summary for today."""
    import sqlalchemy as sa
    from app.models.models import LlmUsage

    today = date.today()
    from_dt = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    to_dt = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)

    stmt = (
        select(
            func.count(LlmUsage.id).label("requests"),
            func.coalesce(func.sum(LlmUsage.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(LlmUsage.estimated_cost_usd), 0.0).label("total_cost_usd"),
        )
        .where(LlmUsage.created_at >= from_dt)
        .where(LlmUsage.created_at <= to_dt)
    )
    row = (await db.execute(stmt)).one()
    return {
        "requests": row.requests,
        "total_tokens": row.total_tokens,
        "total_cost_usd": round(row.total_cost_usd, 6),
    }


@router.get("/providers/status")
async def get_provider_statuses(
    current_user: User = SuperAdminDep,
):
    """Return configured provider statuses and cooldown info."""
    from app.services.llm.router import get_llm_router
    router_instance = get_llm_router()
    return await router_instance.provider_statuses()


@router.post("/providers/{provider_name}/test")
async def test_provider(
    provider_name: str,
    current_user: User = SuperAdminDep,
):
    """Send a fixed test prompt to a specific provider and return the result."""
    from app.services.llm.router import get_llm_router
    router_instance = get_llm_router()
    result = await router_instance.test_provider(provider_name)
    return result

