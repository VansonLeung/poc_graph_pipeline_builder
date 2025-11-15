"""
Configuration module for Neo4j GraphRAG system.
Handles environment variables and connection settings.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for Neo4j GraphRAG system."""
    
    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Google Cloud Configuration
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    GOOGLE_CLOUD_PROJECT: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    # Cohere Configuration
    CO_API_KEY: Optional[str] = os.getenv("CO_API_KEY")
    
    # MistralAI Configuration
    MISTRAL_API_KEY: Optional[str] = os.getenv("MISTRAL_API_KEY")
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
    
    # Ollama Configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    
    # Vector Index Configuration
    VECTOR_INDEX_NAME: str = os.getenv("VECTOR_INDEX_NAME", "document_embeddings")
    VECTOR_DIMENSIONS: int = int(os.getenv("VECTOR_DIMENSIONS", "1536"))
    FULLTEXT_INDEX_NAME: str = os.getenv("FULLTEXT_INDEX_NAME", "document_fulltext")
    
    # Embedding Model
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL", "http://localhost:18000/v1")
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    
    # OpenAI Base URL
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL")
    
    @classmethod
    def get_neo4j_driver(cls):
        """Create and return a Neo4j driver instance."""
        return GraphDatabase.driver(
            cls.NEO4J_URI,
            auth=(cls.NEO4J_USERNAME, cls.NEO4J_PASSWORD)
        )
    
    @classmethod
    def get_llm(cls):
        """Create and return the configured LLM instance."""
        provider = cls.LLM_PROVIDER.lower()
        
        if provider == "openai":
            from neo4j_graphrag.llm import OpenAILLM
            return OpenAILLM(
                model_name=cls.LLM_MODEL,
                api_key=cls.OPENAI_API_KEY,
                base_url=cls.OPENAI_BASE_URL,
                model_params={
                    "temperature": cls.LLM_TEMPERATURE,
                    "max_tokens": cls.LLM_MAX_TOKENS,
                }
            )
        elif provider == "anthropic":
            from neo4j_graphrag.llm import AnthropicLLM
            if not cls.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
            return AnthropicLLM(
                model_name=cls.LLM_MODEL,
                api_key=cls.ANTHROPIC_API_KEY,
                model_params={
                    "temperature": cls.LLM_TEMPERATURE,
                    "max_tokens": cls.LLM_MAX_TOKENS,
                }
            )
        elif provider == "cohere":
            from neo4j_graphrag.llm import CohereLLM
            if not cls.CO_API_KEY:
                raise ValueError("CO_API_KEY is required for Cohere provider")
            return CohereLLM(
                model_name=cls.LLM_MODEL,
                api_key=cls.CO_API_KEY,
                model_params={
                    "temperature": cls.LLM_TEMPERATURE,
                    "max_tokens": cls.LLM_MAX_TOKENS,
                }
            )
        elif provider == "mistral":
            from neo4j_graphrag.llm import MistralAILLM
            if not cls.MISTRAL_API_KEY:
                raise ValueError("MISTRAL_API_KEY is required for MistralAI provider")
            return MistralAILLM(
                model_name=cls.LLM_MODEL,
                api_key=cls.MISTRAL_API_KEY,
                model_params={
                    "temperature": cls.LLM_TEMPERATURE,
                    "max_tokens": cls.LLM_MAX_TOKENS,
                }
            )
        elif provider == "azure_openai":
            from neo4j_graphrag.llm import AzureOpenAILLM
            if not cls.AZURE_OPENAI_API_KEY or not cls.AZURE_OPENAI_ENDPOINT:
                raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are required for Azure OpenAI provider")
            return AzureOpenAILLM(
                model_name=cls.LLM_MODEL,
                api_key=cls.AZURE_OPENAI_API_KEY,
                azure_endpoint=cls.AZURE_OPENAI_ENDPOINT,
                api_version=cls.AZURE_OPENAI_API_VERSION,
                model_params={
                    "temperature": cls.LLM_TEMPERATURE,
                    "max_tokens": cls.LLM_MAX_TOKENS,
                }
            )
        elif provider == "ollama":
            from neo4j_graphrag.llm import OllamaLLM
            return OllamaLLM(
                model_name=cls.LLM_MODEL,
                host=cls.OLLAMA_HOST,
                model_params={
                    "temperature": cls.LLM_TEMPERATURE,
                    "max_tokens": cls.LLM_MAX_TOKENS,
                }
            )
        elif provider == "vertexai":
            from neo4j_graphrag.llm import VertexAILLM
            if not cls.GOOGLE_APPLICATION_CREDENTIALS or not cls.GOOGLE_CLOUD_PROJECT:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_PROJECT are required for VertexAI provider")
            return VertexAILLM(
                model_name=cls.LLM_MODEL,
                project_id=cls.GOOGLE_CLOUD_PROJECT,
                location="us-central1",  # Default location, can be made configurable
                model_params={
                    "temperature": cls.LLM_TEMPERATURE,
                    "max_tokens": cls.LLM_MAX_TOKENS,
                }
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.NEO4J_URI or not cls.NEO4J_PASSWORD:
            raise ValueError("Neo4j connection details are required")
        
        # Check for the selected LLM provider's API key
        provider = cls.LLM_PROVIDER.lower()
        if provider == "openai" and not cls.OPENAI_API_KEY:
            # raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            pass
        elif provider == "anthropic" and not cls.ANTHROPIC_API_KEY:
            # raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
            pass
        elif provider == "cohere" and not cls.CO_API_KEY:
            # raise ValueError("CO_API_KEY is required for Cohere provider")
            pass
        elif provider == "mistral" and not cls.MISTRAL_API_KEY:
            # raise ValueError("MISTRAL_API_KEY is required for MistralAI provider")
            pass
        elif provider == "azure_openai" and (not cls.AZURE_OPENAI_API_KEY or not cls.AZURE_OPENAI_ENDPOINT):
            # raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are required for Azure OpenAI provider")
            pass
        elif provider == "vertexai" and (not cls.GOOGLE_APPLICATION_CREDENTIALS or not cls.GOOGLE_CLOUD_PROJECT):
            # raise ValueError("GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_PROJECT are required for VertexAI provider")
            pass
        elif provider == "ollama":
            # Ollama doesn't require API key, but host should be accessible
            pass
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        return True
    
    @classmethod
    def get_llm_config(cls) -> dict:
        """Get LLM configuration as a dictionary."""
        return {
            "model_name": cls.LLM_MODEL,
            "model_params": {
                "temperature": cls.LLM_TEMPERATURE,
                "max_tokens": cls.LLM_MAX_TOKENS,
                "response_format": {"type": "json_object"}
            }
        }
    
    @classmethod
    def get_embedder_config(cls) -> dict:
        """Get embedder configuration as a dictionary."""
        return {
            "model": cls.EMBEDDING_MODEL,
            "base_url": cls.EMBEDDING_BASE_URL,
        }


# Validate configuration on import - commented out to allow setup_check to run
# Config.validate_config()
