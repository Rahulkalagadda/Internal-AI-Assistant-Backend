from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .docs import SourceType, DocumentMetadata

class EmbeddingVector(BaseModel):
    vector: List[float]
    text: str
    metadata: DocumentMetadata

class SearchResult(BaseModel):
    text: str
    metadata: DocumentMetadata
    score: float = Field(ge=0, le=1)

class RAGRequest(BaseModel):
    question: str
    context: Optional[str] = None
    max_tokens: int = Field(default=1500, le=2000)
    temperature: float = Field(default=0.7, ge=0, le=1)
    source_types: Optional[List[SourceType]] = None
    num_sources: int = Field(default=3, ge=1, le=5)

class RAGResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    context_used: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChunkingConfig(BaseModel):
    chunk_size: int = Field(default=1000, ge=100, le=2000)
    chunk_overlap: int = Field(default=200, ge=0, le=500)
    length_function: str = "char"  # or "token"

class IndexConfig(BaseModel):
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunking: ChunkingConfig = ChunkingConfig()
    similarity_metric: str = "cosine"  # or "euclidean", "dot_product" 