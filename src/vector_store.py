from __future__ import annotations

from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from src.config import get_settings


VECTOR_SIZE = 1536


def _build_client(client: QdrantClient | None = None) -> QdrantClient:
    if client is not None:
        return client

    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def _ensure_payload_indexes(client: QdrantClient, collection_name: str) -> None:
    indexes = {
        "department": rest.PayloadSchemaType.KEYWORD,
        "access_level": rest.PayloadSchemaType.INTEGER,
        "doc_type": rest.PayloadSchemaType.KEYWORD,
        "source": rest.PayloadSchemaType.KEYWORD,
    }

    for field_name, field_schema in indexes.items():
        try:
            client.create_payload_index(collection_name=collection_name, field_name=field_name, field_schema=field_schema)
        except Exception:
            continue


def create_collection(client: QdrantClient | None = None, collection_name: str = "enterprise_docs") -> None:
    active_client = _build_client(client)

    if active_client.collection_exists(collection_name):
        _ensure_payload_indexes(active_client, collection_name)
        return

    active_client.create_collection(
        collection_name=collection_name,
        vectors_config=rest.VectorParams(size=VECTOR_SIZE, distance=rest.Distance.COSINE),
        on_disk_payload=True,
    )
    _ensure_payload_indexes(active_client, collection_name)


def upsert_embeddings(
    client: QdrantClient,
    collection_name: str,
    embedded_chunks: list[dict[str, object]],
) -> None:
    points = []
    for chunk in embedded_chunks:
        payload = dict(chunk.get("payload", {}))
        payload.setdefault("content", chunk.get("content", ""))
        points.append(
            rest.PointStruct(
                id=str(uuid4()),
                vector=chunk.get("vector", []),
                payload=payload,
            )
        )

    client.upsert(collection_name=collection_name, points=points)
