from types import SimpleNamespace

from src import retrieval
from src.rbac import build_user_context
from src.schemas import Role


def test_build_user_context_maps_clearance_and_department() -> None:
    context = build_user_context("user-1", Role.hr)

    assert context.user_id == "user-1"
    assert context.clearance_level == 4
    assert context.department == "hr"


class FakeQdrantClient:
    def __init__(self) -> None:
        self.dataset = [
            {
                "content": "HR policy",
                "source": "hr.pdf",
                "page_number": 1,
                "department": "hr",
                "access_level": 4,
                "doc_type": "pdf_text",
            },
        ]

    def search(self, collection_name, query_vector, query_filter, limit, with_payload):
        clearance = query_filter.must[0].range.lte
        department_filter = query_filter.must[1].should
        allowed_departments = {condition.match.value for condition in department_filter}

        matches = []
        for record in self.dataset:
            if record["access_level"] <= clearance and record["department"] in allowed_departments:
                matches.append(
                    SimpleNamespace(
                        score=0.9,
                        payload=record,
                    )
                )
        return matches[:limit]


def test_retrieve_with_rbac_blocks_hr_only_content_for_engineering(monkeypatch) -> None:
    monkeypatch.setattr(retrieval, "get_qdrant_client", lambda: FakeQdrantClient())
    monkeypatch.setattr(retrieval, "embed_query", lambda query: [0.1, 0.2, 0.3])
    user_context = build_user_context("user-2", Role.engineering)

    result = retrieval.retrieve_with_rbac("salary policy", user_context)

    assert result.access_restricted is True
    assert result.chunks == []


def test_retrieve_with_rbac_allows_hr_content_for_hr(monkeypatch) -> None:
    monkeypatch.setattr(retrieval, "get_qdrant_client", lambda: FakeQdrantClient())
    monkeypatch.setattr(retrieval, "embed_query", lambda query: [0.1, 0.2, 0.3])
    user_context = build_user_context("user-3", Role.hr)

    result = retrieval.retrieve_with_rbac("salary policy", user_context)

    assert result.access_restricted is False
    assert len(result.chunks) == 1
    assert result.chunks[0].source == "hr.pdf"
