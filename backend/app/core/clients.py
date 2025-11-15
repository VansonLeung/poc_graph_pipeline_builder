"""External service clients (LLM + embeddings)."""

from __future__ import annotations

from typing import List, Optional
import httpx


class EmbeddingClient:
    """Simple client for OpenAI-compatible embedding endpoints."""

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def embed(self, text: str) -> List[float]:
        payload = {"model": self.model, "input": text}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        url = f"{self.base_url}/embeddings"
        response = httpx.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        embedding = data["data"][0]["embedding"]
        if not isinstance(embedding, list):
            raise ValueError("Embedding response missing embedding list")
        return embedding


class ChatClient:
    """Client for OpenAI-compatible chat completions endpoints."""

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        url = f"{self.base_url}/chat/completions"
        response = httpx.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
