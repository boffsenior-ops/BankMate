from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None

class Source(BaseModel):
    document_id: Optional[int]
    title: str
    page_number: Any
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    conversation_id: int
    message_id: int
    usage: Dict[str, Any]
