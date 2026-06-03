from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    id: int
    title: str
    category: str
    file_path: str
    status: str
    version: int
    uploaded_by: int
    created_at: datetime
    indexed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
