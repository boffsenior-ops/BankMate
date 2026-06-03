from typing import List, Dict, Any
from app.services.rag.embedder import embed_texts_batched
from app.services.rag.vector_store import get_qdrant_client, COLLECTION_NAME, init_qdrant

async def retrieve_relevant_chunks(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Embeds the user query and searches Qdrant for the most relevant document chunks.
    """
    # 1. Embed query locally
    embeddings = await embed_texts_batched([query])
    if not embeddings:
        return []
    query_embedding = embeddings[0]
    
    # 2. Search Qdrant
    await init_qdrant()
    
    # Note: For production we would use hybrid search (vector + keyword from PostgreSQL).
    # Currently doing pure vector search.
    client = get_qdrant_client()
    search_result = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k,
        score_threshold=0.45,
    )
    
    # 3. Format results
    results = []
    for hit in search_result.points:
        results.append({
            "score": hit.score,
            "document_id": hit.payload.get("document_id"),
            "chunk_index": hit.payload.get("chunk_index"),
            "title": hit.payload.get("title"),
            "page_number": hit.payload.get("page_number"),
            "content": hit.payload.get("content")
        })
        
    return results
