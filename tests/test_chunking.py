from src.chunking import chunk_documents
from src.ingestion import IngestedDocument


def test_chunk_documents_preserves_metadata(monkeypatch) -> None:
    monkeypatch.setenv("CHUNK_SIZE", "20")
    monkeypatch.setenv("CHUNK_OVERLAP", "0")

    docs = [
        IngestedDocument(
            content="This is a sample document that should split into chunks.",
            source="doc1.pdf",
            page_number=2,
            doc_type="pdf_text",
            department="hr",
            access_level=4,
            metadata={"department": "hr", "access_level": 4},
        )
    ]

    chunks = chunk_documents(docs)

    assert len(chunks) >= 2
    assert all(chunk.department == "hr" for chunk in chunks)
    assert all(chunk.access_level == 4 for chunk in chunks)
    assert all(chunk.source == "doc1.pdf" for chunk in chunks)
    assert all(len(chunk.content) <= 20 for chunk in chunks)
