from celery import Celery
from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "bankmate_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.document_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tashkent",
    enable_utc=True,
)
