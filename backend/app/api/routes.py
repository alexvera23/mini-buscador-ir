from __future__ import annotations

from typing import Literal
from fastapi import APIRouter, HTTPException, Query, Request

from app.core.search_engine import SearchEngine
from app.models.schemas import (
    DocumentDetailResponse,
    EvaluationComparisonResponse,
    GraphResponse,
    SearchResponse,
    StatsResponse,
)

router = APIRouter(prefix="/api", tags=["IR Engine"])


def _get_engine(request: Request) -> SearchEngine:
    engine = getattr(request.app.state, "search_engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    return engine


@router.get("/search", response_model=SearchResponse)
def search_documents(
    request: Request,
    q: str = Query(default="", description="Consulta textual del usuario"),
    mode: Literal["tfidf", "pagerank", "hits", "hybrid"] = Query(
        default="hybrid", description="Modo de ranking: tfidf, pagerank, hits o hybrid"
    ),
    alpha: float = Query(
        default=0.7, ge=0.0, le=1.0, description="Peso de TF-IDF en modo hybrid"
    ),
    limit: int = Query(default=10, ge=1, le=100, description="Máximo de resultados"),
) -> SearchResponse:
    engine = _get_engine(request)
    return engine.search(query=q, mode=mode, alpha=alpha, limit=limit)


@router.get("/stats", response_model=StatsResponse)
def get_stats(request: Request) -> StatsResponse:
    engine = _get_engine(request)
    return engine.get_stats()


@router.get("/graph", response_model=GraphResponse)
def get_graph(request: Request) -> GraphResponse:
    engine = _get_engine(request)
    return engine.get_graph()


@router.get("/documents/{doc_id}", response_model=DocumentDetailResponse)
def get_document_detail(request: Request, doc_id: str) -> DocumentDetailResponse:
    engine = _get_engine(request)
    detail = engine.get_document(doc_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
    return detail


@router.get("/evaluate", response_model=EvaluationComparisonResponse)
def evaluate_engine(
    request: Request,
    k: int = Query(default=5, ge=1, le=50, description="Corte Top-K para evaluación"),
    alpha: float = Query(
        default=0.7, ge=0.0, le=1.0, description="Peso de TF-IDF en modo hybrid"
    ),
    beta: float = Query(
        default=1.0, gt=0.0, le=5.0, description="Parámetro beta para F-beta"
    ),
) -> EvaluationComparisonResponse:
    engine = _get_engine(request)
    return engine.evaluate(k=k, alpha=alpha, beta=beta)
