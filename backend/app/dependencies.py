"""FastAPI dependency wiring."""

from __future__ import annotations

from fastapi import Depends

from backend.app.core.clients import ChatClient, EmbeddingClient
from backend.app.core.db import get_driver
from backend.app.core.settings import get_settings
from backend.app.repositories.neo4j_repository import Neo4jRepository
from backend.app.services.document_service import DocumentService
from backend.app.services.index_service import IndexService
from backend.app.services.search_service import SearchService


def get_repository() -> Neo4jRepository:
    settings = get_settings()
    driver = get_driver()
    return Neo4jRepository(driver=driver, vector_index_name=settings.vector_index_name)


def get_index_service(
    repository: Neo4jRepository = Depends(get_repository),
) -> IndexService:
    return IndexService(repository)


def get_embedder() -> EmbeddingClient:
    settings = get_settings()
    base_url = settings.embedding_base_url or settings.llm_base_url
    if not base_url:
        raise ValueError("Embedding base URL must be configured")
    return EmbeddingClient(
        model=settings.embedding_model,
        base_url=base_url,
        api_key=settings.embedding_api_key,
    )


def get_llm_client() -> ChatClient:
    settings = get_settings()
    base_url = settings.llm_base_url or settings.embedding_base_url
    if not base_url:
        raise ValueError("LLM base URL must be configured")
    return ChatClient(
        model=settings.llm_model,
        base_url=base_url,
        api_key=settings.llm_api_key,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )


def get_document_service(
    repository: Neo4jRepository = Depends(get_repository),
    embedder: EmbeddingClient = Depends(get_embedder),
) -> DocumentService:
    return DocumentService(repository, embedder)


def get_search_service(
    repository: Neo4jRepository = Depends(get_repository),
    embedder: EmbeddingClient = Depends(get_embedder),
    llm: ChatClient = Depends(get_llm_client),
) -> SearchService:
    return SearchService(repository, embedder, llm)
