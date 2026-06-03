import uuid
from typing import List, Dict, Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.core.config import settings

def get_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
    )

COLLECTION_NAME = "bankmate_documents"
VECTOR_DIMENSION = 1024  # BGE-M3 has 1024 dimensions

async def init_qdrant():
    """Ensure the Qdrant collection exists and has the correct dimension."""
    client = get_qdrant_client()
    collections_response = await client.get_collections()
    collection_names = [c.name for c in collections_response.collections]
    
    if COLLECTION_NAME in collection_names:
        # Check if the existing collection has the correct dimension
        collection_info = await client.get_collection(collection_name=COLLECTION_NAME)
        # Handle the case where vector config might be a dict or an object depending on qdrant_client version
        try:
            current_dim = collection_info.config.params.vectors.size
            if current_dim != VECTOR_DIMENSION:
                print(f"Dropping collection {COLLECTION_NAME} because dimension changed from {current_dim} to {VECTOR_DIMENSION}")
                await client.delete_collection(collection_name=COLLECTION_NAME)
                collection_names.remove(COLLECTION_NAME)
        except Exception as e:
            print(f"Could not determine collection dimension: {e}. Leaving as is.")
            
    if COLLECTION_NAME not in collection_names:
        print(f"Creating collection {COLLECTION_NAME} with dimension {VECTOR_DIMENSION}")
        try:
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_DIMENSION,
                    distance=models.Distance.COSINE
                )
            )
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Collection {COLLECTION_NAME} was created by another worker. Proceeding.")
            else:
                raise e

async def index_chunks(
    document_id: int, 
    title: str, 
    chunks: List[Dict[str, Any]], 
    embeddings: List[List[float]]
) -> List[str]:
    """
    Indexes document chunks and their embeddings into Qdrant.
    Returns the generated UUIDs for the vectors.
    """
    await init_qdrant()
    
    points = []
    vector_ids = []
    
    for chunk, embedding in zip(chunks, embeddings):
        vector_id = str(uuid.uuid4())
        vector_ids.append(vector_id)
        
        payload = {
            "document_id": document_id,
            "chunk_index": chunk["chunk_index"],
            "title": title,
            "page_number": chunk["page_number"],
            "content": chunk["content"]
        }
        
        points.append(
            models.PointStruct(
                id=vector_id,
                payload=payload,
                vector=embedding
            )
        )
        
    if points:
        # Batch upload to Qdrant
        client = get_qdrant_client()
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
    return vector_ids
