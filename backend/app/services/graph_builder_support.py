"""Shared helpers for bridging backend services with the KnowledgeGraphBuilder."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional

from config import Config
from kg_builder import KnowledgeGraphBuilder
from neo4j import Driver
from neo4j_graphrag.embeddings import OpenAIEmbeddings

DEFAULT_CHUNK_SIZE = 4000
DEFAULT_CHUNK_OVERLAP = 200


class GraphBuilderSupport:
    """Lazily constructs and executes KnowledgeGraphBuilder workflows."""

    def __init__(
        self,
        driver: Driver,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        self.driver = driver
        self.chunk_size = chunk_size or getattr(Config, "KG_CHUNK_SIZE", DEFAULT_CHUNK_SIZE)
        self.chunk_overlap = chunk_overlap or getattr(Config, "KG_CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP)
        self._builder: KnowledgeGraphBuilder | None = None

    def get_builder(self) -> KnowledgeGraphBuilder:
        """Return (and lazily instantiate) the configured KnowledgeGraphBuilder."""
        if self._builder is None:
            llm = Config.get_llm()
            embedder = OpenAIEmbeddings(
                model=Config.EMBEDDING_MODEL,
                base_url=Config.EMBEDDING_BASE_URL,
            )
            self._builder = KnowledgeGraphBuilder(
                driver=self.driver,
                llm=llm,
                embedder=embedder,
                neo4j_database=Config.NEO4J_DATABASE,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        return self._builder

    def run(self, async_callable: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
        """Execute a builder coroutine using a safe event loop."""

        def _build_coro() -> Awaitable[Any]:
            async def _runner() -> Any:
                return await async_callable(*args, **kwargs)

            return _runner()

        try:
            return asyncio.run(_build_coro())
        except RuntimeError as exc:
            if "asyncio.run()" not in str(exc):
                raise
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(_build_coro())
            finally:
                loop.close()
