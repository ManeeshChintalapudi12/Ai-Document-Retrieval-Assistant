from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import get_settings
from src.ingestion import IngestedDocument


@dataclass(slots=True)
class ChunkedDocument:
    content: str
    chunk_id: str
    source: str
    page_number: int | None
    doc_type: str
    department: str
    access_level: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(self.metadata)
        return payload


def chunk_documents(docs: list[IngestedDocument]) -> list[ChunkedDocument]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    chunked_documents: list[ChunkedDocument] = []

    for document in docs:
        chunks = splitter.split_text(document.content)
        for index, chunk in enumerate(chunks, start=1):
            chunked_documents.append(
                ChunkedDocument(
                    content=chunk,
                    chunk_id=f"{document.source}:{document.page_number or 'na'}:{index}",
                    source=document.source,
                    page_number=document.page_number,
                    doc_type=document.doc_type,
                    department=document.department,
                    access_level=document.access_level,
                    metadata={
                        **document.metadata,
                        "source": document.source,
                        "page_number": document.page_number,
                        "doc_type": document.doc_type,
                        "department": document.department,
                        "access_level": document.access_level,
                        "chunk_index": index,
                    },
                )
            )

    return chunked_documents
