from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - import guard for optional dependency
    PdfReader = None  # type: ignore[assignment]
    _PDF_IMPORT_ERROR = exc
else:
    _PDF_IMPORT_ERROR = None

try:
    import camelot
except ImportError as exc:  # pragma: no cover - import guard for optional dependency
    camelot = None  # type: ignore[assignment]
    _CAMELOT_IMPORT_ERROR = exc
else:
    _CAMELOT_IMPORT_ERROR = None

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - import guard for optional dependency
    OpenAI = None  # type: ignore[assignment]
    _OPENAI_IMPORT_ERROR = exc
else:
    _OPENAI_IMPORT_ERROR = None


SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".webm", ".flac"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}


@dataclass(slots=True)
class IngestedDocument:
    content: str
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


def _require_pdf_dependency() -> None:
    if PdfReader is None:
        raise ImportError("pypdf is required. Install it with: pip install pypdf") from _PDF_IMPORT_ERROR


def _require_camelot_dependency() -> None:
    if camelot is None:
        raise ImportError("camelot-py is required. Install it with: pip install camelot-py") from _CAMELOT_IMPORT_ERROR


def _require_openai_dependency() -> None:
    if OpenAI is None:
        raise ImportError("openai is required. Install it with: pip install openai") from _OPENAI_IMPORT_ERROR


def ingest_pdf_text(file_path: str, department: str, access_level: int) -> list[IngestedDocument]:
    _require_pdf_dependency()
    path = Path(file_path)
    documents: list[IngestedDocument] = []

    with path.open("rb") as handle:
        reader = PdfReader(handle)
        for page_number, page in enumerate(reader.pages, start=1):
            content = (page.extract_text() or "").strip()
            if not content:
                continue
            documents.append(
                IngestedDocument(
                    content=content,
                    source=str(path),
                    page_number=page_number,
                    doc_type="pdf_text",
                    department=department,
                    access_level=access_level,
                    metadata={"department": department, "access_level": access_level},
                )
            )

    return documents


def ingest_pdf_tables(
    file_path: str,
    department: str,
    access_level: int,
    flavor: str = "lattice",
) -> list[IngestedDocument]:
    _require_camelot_dependency()
    path = Path(file_path)

    try:
        tables = camelot.read_pdf(str(path), flavor=flavor)  # type: ignore[attr-defined]
    except Exception as exc:
        if flavor != "stream":
            logger.info("Camelot lattice failed for %s, retrying with stream: %s", path, exc)
            return ingest_pdf_tables(file_path, department, access_level, flavor="stream")
        raise

    documents: list[IngestedDocument] = []
    for index, table in enumerate(tables, start=1):
        markdown_table = table.df.to_markdown(index=False)
        documents.append(
            IngestedDocument(
                content=markdown_table,
                source=str(path),
                page_number=index,
                doc_type="pdf_table",
                department=department,
                access_level=access_level,
                metadata={"department": department, "access_level": access_level, "table_index": index, "flavor": flavor},
            )
        )

    return documents


def ingest_audio(
    file_path: str,
    department: str,
    access_level: int,
    model: str = "whisper-1",
) -> list[IngestedDocument]:
    _require_openai_dependency()
    path = Path(file_path)
    client = OpenAI()

    with path.open("rb") as handle:
        transcription = client.audio.transcriptions.create(model=model, file=handle)

    text = getattr(transcription, "text", "") or ""
    return [
        IngestedDocument(
            content=text.strip(),
            source=str(path),
            page_number=None,
            doc_type="audio",
            department=department,
            access_level=access_level,
            metadata={"department": department, "access_level": access_level, "model": model},
        )
    ]


def ingest_file(file_path: str, department: str, access_level: int) -> list[IngestedDocument]:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in SUPPORTED_PDF_EXTENSIONS:
        documents = ingest_pdf_text(file_path, department, access_level)
        documents.extend(ingest_pdf_tables(file_path, department, access_level))
        return documents

    if suffix in SUPPORTED_AUDIO_EXTENSIONS:
        return ingest_audio(file_path, department, access_level)

    raise ValueError(f"Unsupported file type: {suffix}")


def ingest_directory(
    dir_path: str,
    department_map: dict[str, str],
    access_level_map: dict[str, int],
) -> list[IngestedDocument]:
    root = Path(dir_path)
    documents: list[IngestedDocument] = []

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        department = department_map.get(file_path.parent.name, department_map.get(root.name, "company-wide"))
        access_level = access_level_map.get(file_path.parent.name, access_level_map.get(root.name, 1))

        try:
            documents.extend(ingest_file(str(file_path), department, access_level))
        except Exception as exc:  # pragma: no cover - logging path
            logger.exception("Skipping %s due to ingestion error: %s", file_path, exc)

    return documents


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_documents = ingest_directory(
        dir_path="data",
        department_map={"data": "company-wide"},
        access_level_map={"data": 1},
    )
    for document in sample_documents:
        print(document.to_payload())
