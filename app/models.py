from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    pages: int
    status: str
    processing_time_seconds: float


class BuildIndexResponse(BaseModel):
    status: str
    documents_indexed: int
    total_chunks: int
    embedding_time_seconds: float
    index_size_mb: float


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)


class SourceReference(BaseModel):
    doc_id: str
    filename: str
    page: int
    chunk_id: int
    score: float
    text: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceReference]
    latency_ms: int
    retrieval_time_ms: int
    generation_time_ms: int


class DocumentListResponse(BaseModel):
    total: int
    documents: List[Dict[str, Any]]