import asyncio
import argparse
import os
import json

from app.core.database import async_session_maker
from app.models.models import Document, DocumentChunk
from app.services.documents.parser import parse_document
from app.services.rag.chunker import chunk_text
from app.services.rag.embedder import embed_texts_batched
from app.services.rag.vector_store import index_chunks, init_qdrant
from app.services.rag.retriever import retrieve_relevant_chunks
from app.services.rag.generator import generate_answer
from app.services.documents.storage import upload_file_to_minio

async def run_spike(pdf_path: str, question: str):
    print("=== BANKMATE RAG SPIKE ===")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found.")
        return

    # 1. Upload to MinIO
    print(f"\n[1] Uploading {pdf_path} to MinIO...")
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if pdf_path.endswith(".docx") else "application/pdf"
    with open(pdf_path, "rb") as f:
        minio_path = upload_file_to_minio(f, os.path.basename(pdf_path), content_type)
    print(f"Uploaded as: {minio_path}")

    async with async_session_maker() as db:
        # Create dummy document record
        doc = Document(
            title=os.path.basename(pdf_path),
            category="Test",
            file_path=minio_path,
            status="indexing",
            version=1,
            uploaded_by=1 # assuming admin
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        try:
            # 2. Parse
            print("\n[2] Parsing document...")
            text = parse_document(minio_path)
            print(f"Extracted {len(text)} characters.")
            
            # 3. Chunk
            print("\n[3] Chunking document...")
            chunks = chunk_text(text)
            print(f"Created {len(chunks)} chunks.")
            
            # 4. Embed
            print("\n[4] Embedding chunks via OpenAI...")
            texts_to_embed = [c["content"] for c in chunks]
            embeddings = await embed_texts_batched(texts_to_embed)
            print(f"Generated {len(embeddings)} embeddings.")
            
            # 5. Index
            print("\n[5] Indexing into Qdrant...")
            vector_ids = await index_chunks(doc.id, doc.title, chunks, embeddings)
            print("Indexed successfully.")
            
            # Save chunks to DB
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
            doc.status = "ready"
            await db.commit()
            
            # 6. Retrieve
            print(f"\n[6] Testing retrieval for question: '{question}'...")
            retrieved_chunks = await retrieve_relevant_chunks(question, top_k=5)
            print(f"Retrieved {len(retrieved_chunks)} relevant chunks.")
            for rc in retrieved_chunks:
                print(f"  - Score: {rc['score']:.4f} | Page: {rc['page_number']}")
                
            # 7. Generate
            print("\n[7] Generating answer via Claude 3.5 Sonnet...")
            answer, sources, usage = await generate_answer(question, retrieved_chunks)
            
            print("\n=============================================")
            print("Javob (Answer):")
            print(answer)
            print("\nSources:")
            print(json.dumps(sources, indent=2))
            print("\nUsage:")
            print(json.dumps(usage, indent=2))
            print("=============================================")

        except Exception as e:
            print(f"\n[ERROR] Pipeline failed: {e}")
            doc.status = "error"
            await db.commit()
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BankMate RAG Spike")
    parser.add_argument("--pdf", required=True, help="Path to test PDF")
    parser.add_argument("--question", required=True, help="Question in Uzbek")
    
    args = parser.parse_args()
    
    asyncio.run(run_spike(args.pdf, args.question))
