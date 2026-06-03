import asyncio
from typing import List
from fastembed import TextEmbedding
import logging

logger = logging.getLogger(__name__)

# Initialize the model once. It will be downloaded on first run.
# intfloat/multilingual-e5-large is highly recommended for multilingual setups including Uzbek and Russian.
logger.info("Initializing FastEmbed intfloat/multilingual-e5-large model...")
embedding_model = TextEmbedding(model_name="intfloat/multilingual-e5-large")

async def embed_texts_batched(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """
    Embeds a list of texts using FastEmbed BAAI/bge-m3 locally.
    """
    if not texts:
        return []
        
    try:
        # fastembed.embed() handles batching internally, but we can just pass the list.
        # It's a blocking call, so we wrap it in asyncio.to_thread for async contexts.
        embeddings_generator = await asyncio.to_thread(
            embedding_model.embed, texts, batch_size
        )
        
        # Convert generator to list of lists (fastembed returns numpy arrays)
        all_embeddings = [list(emb) for emb in embeddings_generator]
        return all_embeddings
    except Exception as e:
        logger.exception(f"Failed to embed texts locally: {e}")
        raise e
