from typing import List, Dict, Any
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text: str) -> List[Dict[str, Any]]:
    """
    Chunks the given text recursively using a tiktoken encoder.
    Attempts to extract page numbers based on PyPDF2 fallback formatting '--- Page X ---'.
    """
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="text-embedding-3-large",
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    
    # We will split the raw text into chunks first
    raw_chunks = splitter.split_text(text)
    
    result = []
    current_page = 1
    
    # Regex to catch page markers if present
    page_marker_pattern = re.compile(r"--- Page (\d+) ---")
    
    for idx, chunk in enumerate(raw_chunks):
        # Look for the last page marker in the chunk to guess current page
        # This is a heuristic approach
        matches = page_marker_pattern.findall(chunk)
        if matches:
            current_page = int(matches[-1])
            
        result.append({
            "chunk_index": idx,
            "content": chunk,
            "page_number": current_page,
            # We can expand section extraction later
            "metadata": {} 
        })
        
    return result
