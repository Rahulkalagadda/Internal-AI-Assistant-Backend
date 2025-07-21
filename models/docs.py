from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class SourceType(str, Enum):
    notion = "notion"
    google_docs = "google_docs"
    unknown = "unknown"
    confluence = "confluence"

class DocumentMetadata(BaseModel):
    source_type: SourceType
    source_id: str
    title: str
    url: Optional[str] = None
    last_updated: Optional[str] = None
    author: Optional[str] = None

class Document(BaseModel):
    id: str
    content: str
    metadata: DocumentMetadata
    embedding: Optional[List[float]] = None

class QueryRequest(BaseModel):
    question: str
    context: Optional[str] = None
    max_tokens: Optional[int] = Field(default=1500, le=2000)
    source_types: Optional[List[SourceType]] = None

class SourceInfo(BaseModel):
    title: str
    url: Optional[str]
    source_type: SourceType
    relevance_score: float = Field(ge=0, le=1)

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    context_used: Optional[str] = None

class IndexingStatus(BaseModel):
    status: str
    documents_processed: int
    errors: Optional[List[str]] = None

class DocumentList(BaseModel):
    documents: List[DocumentMetadata]
    total_count: int
    page: int = 1
    page_size: int = 10 