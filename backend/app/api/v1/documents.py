from typing import List
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbDep, require_role
from app.models.models import Document, RoleEnum, User
from app.schemas.document import DocumentResponse
from app.services.audit import log_action
from app.services.documents.storage import upload_file_to_minio

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    request: Request,
    db: DbDep,
    current_user: User = require_role([RoleEnum.ADMIN, RoleEnum.CONTENT_MANAGER]),
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(...),
):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX allowed.")

    try:
        file_path = upload_file_to_minio(file.file, file.filename, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to storage: {str(e)}")

    doc = Document(
        title=title,
        category=category,
        file_path=file_path,
        status="uploaded",
        version=1,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.flush()

    await log_action(
        db, "DOCUMENT_UPLOADED",
        user_id=current_user.id,
        resource_type="document",
        resource_id=str(doc.id),
        request=request,
        metadata={"title": title, "category": category, "filename": file.filename},
    )
    await db.commit()
    await db.refresh(doc)

    # Trigger Celery processing task
    from app.tasks.document_tasks import process_document_task
    process_document_task.delay(doc.id)

    return doc


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(db: DbDep, current_user: CurrentUser):
    result = await db.execute(
        select(Document).where(Document.status != "deleted").order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: int, db: DbDep, current_user: CurrentUser):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.status != "deleted")
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    request: Request,
    doc_id: int,
    db: DbDep,
    current_user: User = require_role([RoleEnum.ADMIN]),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = "deleted"
    await log_action(
        db, "DOCUMENT_DELETED",
        user_id=current_user.id,
        resource_type="document",
        resource_id=str(doc_id),
        request=request,
        metadata={"title": doc.title},
    )
    await db.commit()
    return None
