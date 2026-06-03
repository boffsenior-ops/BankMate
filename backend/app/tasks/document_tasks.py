import asyncio
from typing import List, Dict, Any
from sqlalchemy import select
from celery.utils.log import get_task_logger

from app.worker import celery_app
from app.core.database import async_session_maker
from app.models.models import Document, DocumentChunk
from app.services.documents.parser import parse_document
from app.services.rag.chunker import chunk_text
from app.services.rag.embedder import embed_texts_batched
from app.services.rag.vector_store import index_chunks

logger = get_task_logger(__name__)

async def _process_document_async(document_id: int):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    from app.core.config import settings
    import os
    
    DB_URL = settings.database_url if os.getenv("DOCKER_ENV") else settings.database_url_local
    local_engine = create_async_engine(DB_URL, poolclass=NullPool, echo=False)
    local_session_maker = async_sessionmaker(local_engine, expire_on_commit=False)

    async with local_session_maker() as db:
        # Fetch document
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        
        if not doc:
            logger.error(f"Document {document_id} not found.")
            await local_engine.dispose()
            return

        try:
            # 1. Parse
            doc.status = "processing"
            await db.commit()
            
            logger.info(f"Parsing document {document_id}")
            text = parse_document(doc.file_path)
            
            # 2. Chunk
            logger.info(f"Chunking document {document_id}")
            chunks = chunk_text(text)
            
            # 3. Embed
            logger.info(f"Embedding {len(chunks)} chunks for document {document_id}")
            texts_to_embed = [c["content"] for c in chunks]
            embeddings = await embed_texts_batched(texts_to_embed)
            
            # 4. Index in Qdrant
            logger.info(f"Indexing to Qdrant for document {document_id}")
            vector_ids = await index_chunks(doc.id, doc.title, chunks, embeddings)
            
            # 5. Save chunks to DB
            logger.info(f"Saving chunks to Postgres for document {document_id}")
            db_chunks = []
            for chunk, vector_id in zip(chunks, vector_ids):
                db_chunks.append(DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    metadata_=chunk["metadata"],
                    page_number=chunk["page_number"],
                    vector_id=vector_id
                ))
            db.add_all(db_chunks)
            
            doc.status = "indexed"
            from datetime import datetime
            doc.indexed_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Successfully processed document {document_id}")
            
        except Exception as e:
            logger.exception(f"Error processing document {document_id}: {e}")
            doc.status = "error"
            await db.commit()
        finally:
            await local_engine.dispose()

@celery_app.task
def process_document_task(document_id: int):
    """
    Celery task to run the RAG ingestion pipeline asynchronously.
    """
    asyncio.run(_process_document_async(document_id))
