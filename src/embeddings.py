from __future__ import annotations

import logging
import os
import time
from dataclasses import asdict
from typing import Any

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - import guard for optional dependency
    OpenAI = None  # type: ignore[assignment]
    _OPENAI_IMPORT_ERROR = exc
else:
    _OPENAI_IMPORT_ERROR = None

from src.config import get_settings
from src.chunking import ChunkedDocument

logger = logging.getLogger(__name__)


def _require_openai_dependency() -> None:
    if OpenAI is None:
        raise ImportError("openai is required. Install it with: pip install openai") from _OPENAI_IMPORT_ERROR


def _build_openai_client(client: Any | None = None) -> Any:
    if client is not None:
        return client

    _require_openai_dependency()
    settings = get_settings()
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _estimate_tokens(texts: list[str]) -> int:
    return sum(max(1, len(text) // 4) for text in texts)


def embed_chunks(
    chunks: list[ChunkedDocument],
    client: Any | None = None,
    batch_size: int = 100,
    model: str = "text-embedding-3-small",
    max_retries: int = 3,
) -> list[dict[str, Any]]:
    openai_client = _build_openai_client(client)
    embedded_chunks: list[dict[str, Any]] = []

    if openai_client is None:
        return [
            {
                "content": chunk.content,
                "vector": [0.0] * 1536,
                "payload": chunk.to_payload(),
            }
            for chunk in chunks
        ]

    for start_index in range(0, len(chunks), batch_size):
        batch = chunks[start_index : start_index + batch_size]
        batch_texts = [chunk.content for chunk in batch]
        estimated_tokens = _estimate_tokens(batch_texts)
        logger.info("Embedding batch size=%s estimated_tokens=%s", len(batch), estimated_tokens)

        attempt = 0
        while True:
            try:
                response = openai_client.embeddings.create(model=model, input=batch_texts)
                vectors = [item.embedding for item in response.data]
                break
            except Exception as exc:  # pragma: no cover - retry branch
                attempt += 1
                if attempt >= max_retries:
                    raise
                sleep_for = 2 ** (attempt - 1)
                logger.warning("Embedding batch failed (attempt %s/%s): %s", attempt, max_retries, exc)
                time.sleep(sleep_for)

        for chunk, vector in zip(batch, vectors, strict=False):
            embedded_chunks.append(
                {
                    "content": chunk.content,
                    "vector": vector,
                    "payload": chunk.to_payload(),
                }
            )

    logger.info("Embedded %s chunks across %s estimated tokens", len(embedded_chunks), _estimate_tokens([chunk.content for chunk in chunks]))
    return embedded_chunks


def embed_texts(
    texts: list[str],
    client: Any | None = None,
    batch_size: int = 100,
    model: str = "text-embedding-3-small",
    max_retries: int = 3,
) -> list[list[float]]:
    openai_client = _build_openai_client(client)
    vectors: list[list[float]] = []

    if openai_client is None:
        return [[0.0] * 1536 for _ in texts]

    for start_index in range(0, len(texts), batch_size):
        batch = texts[start_index : start_index + batch_size]
        estimated_tokens = _estimate_tokens(batch)
        logger.info("Embedding text batch size=%s estimated_tokens=%s", len(batch), estimated_tokens)

        attempt = 0
        while True:
            try:
                response = openai_client.embeddings.create(model=model, input=batch)
                vectors.extend(item.embedding for item in response.data)
                break
            except Exception as exc:  # pragma: no cover - retry branch
                attempt += 1
                if attempt >= max_retries:
                    raise
                sleep_for = 2 ** (attempt - 1)
                logger.warning("Embedding text batch failed (attempt %s/%s): %s", attempt, max_retries, exc)
                time.sleep(sleep_for)

    return vectors


def embed_query(query: str, client: Any | None = None, model: str = "text-embedding-3-small") -> list[float]:
    return embed_texts([query], client=client, batch_size=1, model=model)[0]


class EmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 1536 for _ in texts]
