"""Centralized audit logging service for BankMate."""
import logging
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AuditLog

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    action: str,
    user_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Write an audit log entry to the database.

    Args:
        db: Async SQLAlchemy session.
        action: Short action code, e.g. 'USER_CREATED', 'DOCUMENT_DELETED'.
        user_id: ID of the acting user (None for anonymous).
        resource_type: Entity being acted on (e.g. 'user', 'document').
        resource_id: ID / identifier of the entity.
        request: FastAPI request object for IP / user-agent extraction.
        metadata: Extra structured data to store alongside the log.
    """
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            metadata_=metadata or {},
        )
        db.add(log)
        await db.commit()
    except Exception as exc:  # pragma: no cover
        logger.error("Audit log write failed: %s", exc)
