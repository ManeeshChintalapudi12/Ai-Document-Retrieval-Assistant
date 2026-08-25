import pytest

from src.schemas import RAGResponse


def test_rag_response_defaults() -> None:
    response = RAGResponse(answer="ok", confidence_score=0.5)

    assert response.sources == []
    assert response.access_denied is False


def test_rag_response_rejects_out_of_bounds_confidence() -> None:
    with pytest.raises(ValueError):
        RAGResponse(answer="ok", confidence_score=1.5)
