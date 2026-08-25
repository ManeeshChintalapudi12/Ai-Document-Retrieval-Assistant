from types import SimpleNamespace

from src.chunking import ChunkedDocument
from src.embeddings import embed_chunks


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.calls = []

    class embeddings:
        @staticmethod
        def create(model: str, input: list[str]):
            return SimpleNamespace(
                data=[SimpleNamespace(embedding=[float(index)] * 3) for index, _ in enumerate(input)]
            )


def test_embed_chunks_returns_payload_ready_dicts() -> None:
    chunks = [
        ChunkedDocument(
            content="hello world",
            chunk_id="doc1:1:1",
            source="doc1.pdf",
            page_number=1,
            doc_type="pdf_text",
            department="engineering",
            access_level=2,
            metadata={"department": "engineering", "access_level": 2, "source": "doc1.pdf", "page_number": 1, "doc_type": "pdf_text"},
        )
    ]

    result = embed_chunks(chunks, client=FakeOpenAIClient(), batch_size=1)

    assert len(result) == 1
    assert result[0]["content"] == "hello world"
    assert result[0]["vector"] == [0.0, 0.0, 0.0]
    assert result[0]["payload"]["department"] == "engineering"
