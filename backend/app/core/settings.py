"""Application settings for the backend API."""

from dataclasses import dataclass
from functools import lru_cache
from config import Config as ProjectConfig


@dataclass
class Settings:
    """Typed settings derived from the project Config."""
    neo4j_uri: str = ProjectConfig.NEO4J_URI
    neo4j_username: str = ProjectConfig.NEO4J_USERNAME
    neo4j_password: str = ProjectConfig.NEO4J_PASSWORD
    neo4j_database: str = ProjectConfig.NEO4J_DATABASE
    vector_index_name: str = ProjectConfig.VECTOR_INDEX_NAME
    vector_dimensions: int = ProjectConfig.VECTOR_DIMENSIONS
    default_top_k: int = 5
    embedding_model: str = ProjectConfig.EMBEDDING_MODEL
    embedding_base_url: str = ProjectConfig.EMBEDDING_BASE_URL
    embedding_api_key: str | None = ProjectConfig.OPENAI_API_KEY
    llm_model: str = ProjectConfig.LLM_MODEL
    llm_base_url: str | None = ProjectConfig.OPENAI_BASE_URL
    llm_api_key: str | None = ProjectConfig.OPENAI_API_KEY
    llm_temperature: float = ProjectConfig.LLM_TEMPERATURE
    llm_max_tokens: int = ProjectConfig.LLM_MAX_TOKENS


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
