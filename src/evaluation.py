from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

from datasets import Dataset
from openai import OpenAI
from ragas import evaluate
from ragas.llms import llm_factory
from ragas.metrics import AnswerRelevancy, ContextPrecision, Faithfulness

from src.api import generate_answer
from src.config import get_settings
from src.guardrails import apply_guardrails
from src.rbac import build_user_context
from src.retrieval import retrieve_with_rbac
from src.schemas import Role

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_SET = ROOT_DIR / "data" / "eval_set.json"
DEFAULT_REPORT_PATH = ROOT_DIR / "reports" / "eval_report.csv"


def load_eval_set(eval_set_path: Path = DEFAULT_EVAL_SET) -> list[dict[str, Any]]:
    with eval_set_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_ragas_llm() -> Any:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    return llm_factory("gpt-4o-mini", client=client)


def run_pipeline_for_sample(sample: dict[str, Any]) -> dict[str, Any]:
    role = Role(sample["role"])
    user_context = build_user_context(sample["user_id"], role)
    allowed, reason = apply_guardrails(sample["question"], user_context)

    if not allowed:
        return {
            "question": sample["question"],
            "answer": reason,
            "ground_truth": sample["ground_truth"],
            "contexts": [],
            "access_denied": True,
        }

    retrieval_result = retrieve_with_rbac(sample["question"], user_context)
    if retrieval_result.retrieval_failed:
        return {
            "question": sample["question"],
            "answer": "Document retrieval failed; the vector store was unavailable.",
            "ground_truth": sample["ground_truth"],
            "contexts": [],
            "access_denied": False,
        }
    if retrieval_result.access_restricted:
        return {
            "question": sample["question"],
            "answer": "Access denied: no documents matched your RBAC clearance.",
            "ground_truth": sample["ground_truth"],
            "contexts": [],
            "access_denied": True,
        }

    answer, _confidence = generate_answer(sample["question"], retrieval_result)
    contexts = [chunk.content for chunk in retrieval_result.chunks]
    return {
        "question": sample["question"],
        "answer": answer,
        "ground_truth": sample["ground_truth"],
        "contexts": contexts,
        "access_denied": False,
    }


def _evaluate_with_ragas(dataset: Dataset) -> Any:
    llm = build_ragas_llm()
    metrics = [
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm),
        ContextPrecision(llm=llm),
    ]
    return evaluate(dataset, metrics=metrics)


def _result_rows(results: Any, samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if hasattr(results, "to_pandas"):
        frame = results.to_pandas()
        records = frame.to_dict(orient="records")
        for sample, record in zip(samples, records, strict=False):
            record.setdefault("question", sample["question"])
            record.setdefault("ground_truth", sample["ground_truth"])
            record.setdefault("access_denied", sample["access_denied"])
        return records

    if isinstance(results, list):
        return results

    raise TypeError("Unsupported Ragas result format")


def write_report(rows: list[dict[str, Any]], report_path: Path = DEFAULT_REPORT_PATH) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["question", "ground_truth", "faithfulness", "answer_relevancy", "context_precision", "access_denied"]
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    samples = load_eval_set()
    evaluated_samples = [run_pipeline_for_sample(sample) for sample in samples]

    dataset = Dataset.from_dict(
        {
            "question": [sample["question"] for sample in evaluated_samples],
            "answer": [sample["answer"] for sample in evaluated_samples],
            "contexts": [sample["contexts"] for sample in evaluated_samples],
            "ground_truths": [[sample["ground_truth"]] for sample in evaluated_samples],
        }
    )

    results = _evaluate_with_ragas(dataset)
    rows = _result_rows(results, evaluated_samples)
    write_report(rows)

    faithfulness_scores = [float(row.get("faithfulness", 0.0)) for row in rows]
    average_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0
    hallucination_rate = max(0.0, 1.0 - average_faithfulness)

    print(f"Average faithfulness: {average_faithfulness * 100:.2f}%")
    print(f"Hallucination rate estimated at {hallucination_rate * 100:.2f}%")
    print(f"Report written to: {DEFAULT_REPORT_PATH}")


if __name__ == "__main__":
    main()
