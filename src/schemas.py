from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Role(str, Enum):
    general = "general"
    hr = "hr"
    engineering = "engineering"
    finance = "finance"
    admin = "admin"


class DocType(str, Enum):
    pdf = "pdf"
    table = "table"
    audio = "audio"
    company_wide = "company-wide"


class UserContext(BaseModel):
    user_id: str
    role: Role
    clearance_level: int = Field(ge=1, le=5)
    department: str | None = None


class DocumentMetadata(BaseModel):
    department: str
    access_level: int = Field(ge=1, le=5)
    doc_type: str
    extra: dict[str, Any] = Field(default_factory=dict)


class UnifiedDocument(BaseModel):
    content: str
    source: str
    page_number: int | None = None
    doc_type: DocType
    metadata: DocumentMetadata


class SourceRef(BaseModel):
    doc_name: str
    page: int | None = None


class RAGResponse(BaseModel):
    answer: str
    sources: list[SourceRef] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    access_denied: bool = False

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_score(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence_score must be between 0 and 1")
        return value
