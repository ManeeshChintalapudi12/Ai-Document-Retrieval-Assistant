from qdrant_client import QdrantClient

from src.vector_store import VECTOR_SIZE, create_collection, upsert_embeddings


def test_create_collection_and_upsert_embeddings_in_memory() -> None:
    client = QdrantClient(location=":memory:")
    collection_name = "enterprise_docs_test"

    create_collection(client, collection_name=collection_name)
    upsert_embeddings(
        client,
        collection_name=collection_name,
        embedded_chunks=[
            {
                "content": "sample chunk",
                "vector": [0.1] * VECTOR_SIZE,
                "payload": {
                    "department": "engineering",
                    "access_level": 2,
                    "doc_type": "pdf_text",
                    "source": "doc1.pdf",
                    "content": "sample chunk",
                },
            }
        ],
    )

    info = client.get_collection(collection_name)
    assert info.status is not None
    assert client.count(collection_name=collection_name, exact=True).count == 1
