import io
import os
import tempfile
from typing import Dict, Any

from llama_parse import LlamaParse
import pypdf
import docx

from app.core.config import settings
from app.services.documents.storage import get_file_from_minio

def parse_document(file_path: str) -> str:
    """
    Downloads file from MinIO, parses it to text (markdown for PDF via LlamaParse, raw text for DOCX).
    """
    file_bytes = get_file_from_minio(file_path)
    extension = file_path.split(".")[-1].lower() if "." in file_path else ""

    if extension == "docx":
        return _parse_docx(file_bytes)
    elif extension == "pdf":
        return _parse_pdf(file_bytes, file_path)
    elif extension == "txt":
        return file_bytes.decode('utf-8', errors='ignore')
    else:
        raise ValueError(f"Unsupported file extension: {extension}")

def _parse_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def _parse_pdf(file_bytes: bytes, file_name: str) -> str:
    # Attempt LlamaParse first
    try:
        # LlamaParse requires a file path, so we write to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        parser = LlamaParse(
            api_key=settings.LLAMA_CLOUD_API_KEY,
            result_type="markdown",
            verbose=True
        )
        # Parse returns a list of Document objects
        documents = parser.load_data(tmp_path)
        
        os.unlink(tmp_path)
        
        if not documents:
            raise ValueError("LlamaParse returned empty results (likely API error or unauthenticated)")
            
        parsed_text = "\n\n".join([doc.text for doc in documents])
        if not parsed_text.strip():
            raise ValueError("LlamaParse returned empty text")
            
        return parsed_text
        
    except Exception as e:
        print(f"LlamaParse failed: {e}. Falling back to PyPDF2.")
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return _parse_pdf_fallback(file_bytes)

def _parse_pdf_fallback(file_bytes: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    text_chunks = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text_chunks.append(f"--- Page {i+1} ---\n{page_text}")
    return "\n\n".join(text_chunks)
