from __future__ import annotations

import base64
import json
import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - import guard for optional dependency
    OpenAI = None  # type: ignore[assignment]

from src.config import get_settings
from src.guardrails import apply_guardrails
from src.rbac import build_user_context
from src.retrieval import RetrievalResult, retrieve_with_rbac
from src.schemas import RAGResponse, Role, SourceRef

app = FastAPI(title="Enterprise RAG with RBAC")
logger = logging.getLogger(__name__)

MOCK_USERS: dict[str, dict[str, Any]] = {
    "user-hr": {"role": Role.hr, "department": "hr"},
    "user-eng": {"role": Role.engineering, "department": "engineering"},
    "user-fin": {"role": Role.finance, "department": "finance"},
    "user-admin": {"role": Role.admin, "department": "company-wide"},
}


def _decode_mock_jwt(token: str) -> str:
    try:
        _header, payload, _signature = token.split(".")
        padding = "=" * (-len(payload) % 4)
        payload_json = base64.urlsafe_b64decode((payload + padding).encode("utf-8")).decode("utf-8")
        claims = json.loads(payload_json)
        return str(claims["sub"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc


@app.middleware("http")
async def mock_jwt_auth_middleware(request: Request, call_next):
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing bearer token"},
        )

    request.state.authenticated_user_id = _decode_mock_jwt(authorization.removeprefix("Bearer ").strip())
    return await call_next(request)


class ChatRequest(BaseModel):
    query: str
    user_id: str
    role: Role = Role.engineering


def _build_openai_client(client: Any | None = None) -> Any:
    if client is not None:
        return client
    if OpenAI is None:
        return None

    settings = get_settings()
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def generate_answer(query: str, retrieval_result: RetrievalResult, client: Any | None = None) -> tuple[str, float]:
    if not retrieval_result.chunks:
        return "No grounded sources were available for this answer.", 0.0

    openai_client = _build_openai_client(client)

    if openai_client is None:
        best_chunk = retrieval_result.chunks[0]
        return (
            "OpenAI is not configured, so this is the most relevant grounded excerpt "
            f"from {best_chunk.source}:\n\n{best_chunk.content}",
            min(1.0, 0.5 + 0.1 * len(retrieval_result.chunks)),
        )

    context = "\n\n".join(
        f"Source: {chunk.source}\nPage: {chunk.page_number}\nContent: {chunk.content}" for chunk in retrieval_result.chunks
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer using only the provided company document context."},
            {"role": "user", "content": f"Question: {query}\n\nContext:\n{context}"},
        ],
    )
    answer = response.choices[0].message.content or ""
    confidence = min(1.0, 0.5 + 0.1 * len(retrieval_result.chunks))
    return answer, confidence


@app.post("/chat", response_model=RAGResponse)
def chat(payload: ChatRequest, http_request: Request) -> RAGResponse:
    user_record = MOCK_USERS.get(payload.user_id)
    if user_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown user")

    authenticated_user_id = getattr(http_request.state, "authenticated_user_id", None)
    if authenticated_user_id != payload.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token user does not match request user_id")

    user_context = build_user_context(payload.user_id, user_record["role"])
    allowed, reason = apply_guardrails(payload.query, user_context)
    if not allowed:
        return RAGResponse(
            answer=reason,
            sources=[],
            confidence_score=0.0,
            access_denied=True,
        )

    retrieval_result = retrieve_with_rbac(payload.query, user_context)
    if retrieval_result.retrieval_failed:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document retrieval is temporarily unavailable. Please try again later.",
        )
    if retrieval_result.access_restricted or not retrieval_result.chunks:
        return RAGResponse(
            answer="Access denied: no documents matched your RBAC clearance.",
            sources=[],
            confidence_score=0.0,
            access_denied=True,
        )

    answer, confidence_score = generate_answer(payload.query, retrieval_result)
    sources = [SourceRef(doc_name=chunk.source, page=chunk.page_number) for chunk in retrieval_result.chunks]

    return RAGResponse(
        answer=answer,
        sources=sources,
        confidence_score=confidence_score,
        access_denied=False,
    )
