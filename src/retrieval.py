from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from src.config import get_settings
from src.embeddings import embed_query
from src.schemas import UserContext


@dataclass(slots=True)
class RetrievedChunk:
    content: str
    source: str
    page_number: int | None
    score: float
    metadata: dict[str, object]


@dataclass(slots=True)
class RetrievalResult:
    chunks: list[RetrievedChunk]
    access_restricted: bool = False


def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    kwargs: dict[str, Any] = {"url": settings.qdrant_url}
    if settings.qdrant_api_key:
        kwargs["api_key"] = settings.qdrant_api_key
    return QdrantClient(**kwargs)


def build_rbac_filter(user_context: UserContext) -> rest.Filter:
    return rest.Filter(
        must=[
            rest.FieldCondition(
                key="access_level",
                range=rest.Range(lte=user_context.clearance_level),
            ),
            rest.Filter(
                should=[
                    rest.FieldCondition(
                        key="department",
                        match=rest.MatchValue(value=user_context.department or "company-wide"),
                    ),
                    rest.FieldCondition(
                        key="department",
                        match=rest.MatchValue(value="company-wide"),
                    ),
                ]
            ),
        ]
    )


def retrieve_with_rbac(query: str, user_context: UserContext, top_k: int = 5) -> RetrievalResult:
    settings = get_settings()
    client = get_qdrant_client()
    query_vector = embed_query(query)

    results = client.search(
        collection_name=settings.qdrant_collection_name,
        query_vector=query_vector,
        query_filter=build_rbac_filter(user_context),
        limit=top_k,
        with_payload=True,
    )

    chunks: list[RetrievedChunk] = []
    for item in results:
        payload = item.payload or {}
        chunks.append(
            RetrievedChunk(
                content=str(payload.get("content", "")),
                source=str(payload.get("source", "")),
                page_number=payload.get("page_number"),
                score=float(item.score or 0.0),
                metadata={key: value for key, value in payload.items() if key not in {"content", "source", "page_number"}},
            )
        )

    return RetrievalResult(chunks=chunks, access_restricted=not bool(chunks))
