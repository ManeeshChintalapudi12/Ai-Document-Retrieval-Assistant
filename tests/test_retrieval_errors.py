"""A failed vector-store search must not look like an RBAC denial.

Previously ``retrieve_with_rbac`` swallowed every Qdrant error and returned
``access_restricted=True`` with no chunks, so the API answered a service
outage with 200 "Access denied". These tests pin the distinction:
``retrieval_failed`` is True only when the search itself raised.
"""

import base64
import json

import pytest
from fastapi.testclient import TestClient

from src import api, retrieval
from src.rbac import build_user_context
from src.retrieval import RetrievalResult
from src.schemas import Role

client = TestClient(api.app, raise_server_exceptions=False)


def _make_mock_token(user_id: str) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode("utf-8")).decode("utf-8").rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"sub": user_id}).encode("utf-8")).decode("utf-8").rstrip("=")
    return f"{header}.{payload}.signature"


class FailingQdrantClient:
    """Mimics Qdrant being unreachable: every search raises."""

    def search(self, *args, **kwargs):
        raise RuntimeError("connection refused")


class EmptyQdrantClient:
    """A healthy search that simply matches nothing."""

    def search(self, *args, **kwargs):
        return []


@pytest.mark.parametrize("failing_client", [FailingQdrantClient()])
def test_retrieve_marks_search_failure(monkeypatch, failing_client) -> None:
    monkeypatch.setattr(retrieval, "get_qdrant_client", lambda: failing_client)
    monkeypatch.setattr(retrieval, "embed_query", lambda query: [0.1, 0.2, 0.3])
    user_context = build_user_context("user-1", Role.hr)

    result = retrieval.retrieve_with_rbac("salary policy", user_context)

    assert result.retrieval_failed is True
    assert result.chunks == []


def test_retrieve_empty_result_is_not_a_failure(monkeypatch) -> None:
    monkeypatch.setattr(retrieval, "get_qdrant_client", lambda: EmptyQdrantClient())
    monkeypatch.setattr(retrieval, "embed_query", lambda query: [0.1, 0.2, 0.3])
    user_context = build_user_context("user-1", Role.hr)

    result = retrieval.retrieve_with_rbac("quantum computing policy", user_context)

    assert result.retrieval_failed is False
    assert result.chunks == []


def test_chat_returns_503_when_retrieval_fails(monkeypatch) -> None:
    monkeypatch.setattr(api, "apply_guardrails", lambda query, user_context: (True, "Allowed"))
    monkeypatch.setattr(
        api,
        "retrieve_with_rbac",
        lambda query, user_context: RetrievalResult(chunks=[], access_restricted=True, retrieval_failed=True),
    )

    response = client.post(
        "/chat",
        headers={"Authorization": f"Bearer {_make_mock_token('user-hr')}"},
        json={"query": "Summarize HR policy", "user_id": "user-hr"},
    )

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


def test_chat_empty_result_still_reports_access_denied(monkeypatch) -> None:
    monkeypatch.setattr(api, "apply_guardrails", lambda query, user_context: (True, "Allowed"))
    monkeypatch.setattr(
        api,
        "retrieve_with_rbac",
        lambda query, user_context: RetrievalResult(chunks=[], access_restricted=True, retrieval_failed=False),
    )

    response = client.post(
        "/chat",
        headers={"Authorization": f"Bearer {_make_mock_token('user-eng')}"},
        json={"query": "Show HR salaries", "user_id": "user-eng"},
    )

    assert response.status_code == 200
    assert response.json()["access_denied"] is True
    assert "Access denied" in response.json()["answer"]
