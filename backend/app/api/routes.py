"""API routes for the backend service."""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.dependencies import (
    get_document_service,
    get_index_service,
    get_search_service,
)
from backend.app.schemas import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    IndexCreate,
    IndexResponse,
    IndexUpdate,
    SearchRequest,
    SearchResponse,
)
from backend.app.services.document_service import DocumentService
from backend.app.services.index_service import IndexService
from backend.app.services.search_service import SearchService

router = APIRouter(prefix="/api")


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.get("/indexes", response_model=List[IndexResponse])
def list_indexes(index_service: IndexService = Depends(get_index_service)):
    return index_service.list_indexes()


@router.post(
    "/indexes",
    response_model=IndexResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_index(
    payload: IndexCreate,
    index_service: IndexService = Depends(get_index_service),
):
    existing = index_service.get_index(payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="Index already exists")
    return index_service.create_index(payload.model_dump())


@router.get("/indexes/{name}", response_model=IndexResponse)
def get_index(name: str, index_service: IndexService = Depends(get_index_service)):
    index = index_service.get_index(name)
    if not index:
        raise HTTPException(status_code=404, detail="Index not found")
    return index


@router.put("/indexes/{name}", response_model=IndexResponse)
def update_index(
    name: str,
    payload: IndexUpdate,
    index_service: IndexService = Depends(get_index_service),
):
    if not index_service.get_index(name):
        raise HTTPException(status_code=404, detail="Index not found")
    return index_service.update_index(name, payload.model_dump(exclude_unset=True))


@router.delete("/indexes/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_index(name: str, index_service: IndexService = Depends(get_index_service)):
    if not index_service.get_index(name):
        raise HTTPException(status_code=404, detail="Index not found")
    index_service.delete_index(name)


# Document routes ---------------------------------------------------------

@router.get(
    "/indexes/{name}/documents",
    response_model=List[DocumentResponse],
)
def list_documents(
    name: str,
    document_service: DocumentService = Depends(get_document_service),
):
    return document_service.list_documents(name)


@router.post(
    "/indexes/{name}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    name: str,
    payload: DocumentCreate,
    document_service: DocumentService = Depends(get_document_service),
):
    return document_service.create_document(
        index_name=name,
        content=payload.content,
        metadata=payload.metadata,
        embedding=payload.embedding,
    )


@router.get(
    "/indexes/{name}/documents/{doc_id}",
    response_model=DocumentResponse,
)
def get_document(
    name: str,
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    document = document_service.get_document(name, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put(
    "/indexes/{name}/documents/{doc_id}",
    response_model=DocumentResponse,
)
def update_document(
    name: str,
    doc_id: str,
    payload: DocumentUpdate,
    document_service: DocumentService = Depends(get_document_service),
):
    document = document_service.update_document(
        index_name=name,
        doc_id=doc_id,
        content=payload.content,
        metadata=payload.metadata,
        embedding=payload.embedding,
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete(
    "/indexes/{name}/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    name: str,
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    document = document_service.get_document(name, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    document_service.delete_document(name, doc_id)


# Search ------------------------------------------------------------------

@router.post("/search", response_model=SearchResponse)
def rag_search(
    payload: SearchRequest,
    search_service: SearchService = Depends(get_search_service),
):
    result = search_service.rag_search(
        index_name=payload.index_name,
        query=payload.query,
        keywords=payload.keywords,
        top_k=payload.top_k,
    )
    return result
