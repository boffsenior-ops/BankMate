from typing import BinaryIO
import io
import uuid
from minio import Minio
from minio.error import S3Error

from app.core.config import settings

# Initialize MinIO client
minio_client = Minio(
    settings.minio_url,
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
    secure=settings.MINIO_SECURE
)

BUCKET_NAME = "bankmate-docs"

def ensure_bucket_exists():
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
    except S3Error as e:
        print(f"MinIO error: {e}")

def upload_file_to_minio(file_obj: BinaryIO, filename: str, content_type: str) -> str:
    """Uploads a file to MinIO and returns the generated object name (file path)."""
    ensure_bucket_exists()
    
    # Generate unique name to prevent collisions
    extension = filename.split(".")[-1] if "." in filename else ""
    unique_name = f"{uuid.uuid4().hex}.{extension}"
    
    # Read the file to determine its size for MinIO
    file_bytes = file_obj.read()
    file_size = len(file_bytes)
    file_obj.seek(0)
    
    # Upload
    minio_client.put_object(
        bucket_name=BUCKET_NAME,
        object_name=unique_name,
        data=io.BytesIO(file_bytes),
        length=file_size,
        content_type=content_type
    )
    
    return unique_name

def get_file_from_minio(object_name: str) -> bytes:
    """Retrieves a file from MinIO."""
    try:
        response = minio_client.get_object(BUCKET_NAME, object_name)
        return response.read()
    finally:
        response.close()
        response.release_conn()
