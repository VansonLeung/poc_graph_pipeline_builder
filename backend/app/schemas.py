"""Pydantic schemas for the backend API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, constr


class IndexBase(BaseModel):
    description: Optional[str] = Field(default=None, max_length=500)
    dimension: Optional[int] = Field(default=None, ge=1)


class IndexCreate(IndexBase):
    name: constr(min_length=1, max_length=120)


class IndexUpdate(IndexBase):
    pass


class IndexResponse(IndexBase):
    name: str
    vector_index_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None


class DocumentResponse(DocumentBase):
    doc_id: str
    index_name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    index_name: str
    query: str
    keywords: Optional[List[str]] = None
    top_k: int = Field(default=5, ge=1, le=20)


class SearchChunk(BaseModel):
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    score: float


class SearchResponse(BaseModel):
    answer: str
    chunks: List[SearchChunk]
