from __future__ import annotations

import argparse
from pathlib import Path

from qdrant_client import QdrantClient

from src.chunking import chunk_documents
from src.config import get_settings
from src.embeddings import embed_chunks
from src.ingestion import ingest_directory
from src.vector_store import create_collection, upsert_embeddings


def main() -> None:
    parser = argparse.ArgumentParser(description="Index documents into Qdrant.")
    parser.add_argument("--source", default="data/documents", help="Directory containing source documents.")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate the collection before indexing.")
    args = parser.parse_args()

    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    collection_name = settings.qdrant_collection_name

    if args.reset and client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    documents = ingest_directory(
        str(Path(args.source)),
        department_map={"documents": "company-wide"},
        access_level_map={"documents": 1},
    )
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    create_collection(client, collection_name)
    upsert_embeddings(client, collection_name, embedded_chunks)
    print(f"Indexed {len(documents)} documents and {len(chunks)} chunks in {collection_name}.")


if __name__ == "__main__":
    main()
