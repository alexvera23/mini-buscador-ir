from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from app.models.schemas import (
    ContingencyMatrix,
    EvaluationComparisonResponse,
    ModeEvaluationSummary,
    QueryEvaluationMetrics,
)

if TYPE_CHECKING:
    from app.core.search_engine import SearchEngine


class Evaluator:
    """Evaluador experimental de Recuperación de Información (matrices de contingencia y métricas)."""

    def __init__(self, judgments_file: Path) -> None:
        self.judgments_file: Path = judgments_file

    def _load_queries(self) -> list[dict]:
        if not self.judgments_file.exists():
            return []
        data = json.loads(self.judgments_file.read_text(encoding="utf-8"))
        queries = data.get("queries", [])
        return queries if isinstance(queries, list) else []

    def _evaluate_mode(
        self,
        engine: SearchEngine,
        queries: list[dict],
        mode: Literal["tfidf", "hybrid"],
        k: int,
        alpha: float,
        beta: float,
    ) -> ModeEvaluationSummary:
        total_docs = len(engine.doc_map)
        per_query: list[QueryEvaluationMetrics] = []

        for q_entry in queries:
            query_id = str(q_entry.get("query_id", ""))
            query_text = str(q_entry.get("query", ""))
            relevant_set = {
                doc_id
                for doc_id in q_entry.get("relevant_docs", [])
                if doc_id in engine.doc_map
            }

            response = engine.search(query=query_text, mode=mode, alpha=alpha, limit=k)
            retrieved_ids = [item.doc_id for item in response.results]
            retrieved_set = set(retrieved_ids)

            tp = len(relevant_set & retrieved_set)
            fp = len(retrieved_set - relevant_set)
            fn = len(relevant_set - retrieved_set)
            tn = max(0, total_docs - (tp + fp + fn))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (
                2.0 * precision * recall / (precision + recall)
                if (precision + recall) > 0.0
                else 0.0
            )
            beta_sq = beta * beta
            f_beta = (
                (1.0 + beta_sq) * precision * recall / (beta_sq * precision + recall)
                if (beta_sq * precision + recall) > 0.0
                else 0.0
            )
            p_at_k = tp / k if k > 0 else 0.0

            per_query.append(
                QueryEvaluationMetrics(
                    query_id=query_id,
                    query=query_text,
                    relevant_count=len(relevant_set),
                    retrieved_count=len(retrieved_ids),
                    contingency=ContingencyMatrix(tp=tp, fp=fp, fn=fn, tn=tn),
                    precision=round(precision, 4),
                    recall=round(recall, 4),
                    f1=round(f1, 4),
                    f_beta=round(f_beta, 4),
                    precision_at_k=round(p_at_k, 4),
                )
            )

        n_q = len(per_query)
        return ModeEvaluationSummary(
            mode=mode,
            macro_precision=round(sum(m.precision for m in per_query) / n_q, 4) if n_q else 0.0,
            macro_recall=round(sum(m.recall for m in per_query) / n_q, 4) if n_q else 0.0,
            macro_f1=round(sum(m.f1 for m in per_query) / n_q, 4) if n_q else 0.0,
            macro_f_beta=round(sum(m.f_beta for m in per_query) / n_q, 4) if n_q else 0.0,
            macro_precision_at_k=(
                round(sum(m.precision_at_k for m in per_query) / n_q, 4) if n_q else 0.0
            ),
            per_query=per_query,
        )

    def evaluate(
        self,
        engine: SearchEngine,
        k: int = 5,
        alpha: float = 0.7,
        beta: float = 1.0,
    ) -> EvaluationComparisonResponse:
        queries = self._load_queries()
        tfidf_summary = self._evaluate_mode(
            engine=engine, queries=queries, mode="tfidf", k=k, alpha=alpha, beta=beta
        )
        hybrid_summary = self._evaluate_mode(
            engine=engine, queries=queries, mode="hybrid", k=k, alpha=alpha, beta=beta
        )
        return EvaluationComparisonResponse(
            k=k,
            alpha=alpha,
            beta=beta,
            total_queries=len(queries),
            corpus_size=len(engine.doc_map),
            tfidf=tfidf_summary,
            hybrid=hybrid_summary,
        )
