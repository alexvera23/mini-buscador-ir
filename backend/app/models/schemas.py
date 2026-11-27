from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    doc_id: str
    title: str
    category: str
    path: str
    snippet: str
    tfidf_score: float = Field(..., ge=0.0, le=1.0)
    pagerank_score: float = Field(..., ge=0.0)
    combined_score: float = Field(..., ge=0.0)
    matched_terms: list[str]


class SearchResponse(BaseModel):
    query: str
    mode: Literal["tfidf", "pagerank", "hybrid"]
    alpha: float
    total_results: int
    results: list[SearchResultItem]


class TermFrequencyItem(BaseModel):
    term: str
    df: int
    total_tf: int


class TopPageRankItem(BaseModel):
    doc_id: str
    title: str
    category: str
    pagerank: float
    in_degree: int
    out_degree: int


class StatsResponse(BaseModel):
    total_documents: int
    vocabulary_size: int
    total_edges: int
    pagerank_iterations: int
    pagerank_damping: float
    pagerank_epsilon: float
    pagerank_sum: float
    convergence_history: list[float]
    top_terms: list[TermFrequencyItem]
    top_pagerank: list[TopPageRankItem]


class GraphNode(BaseModel):
    id: str
    title: str
    category: str
    pagerank: float
    in_degree: int
    out_degree: int


class GraphEdge(BaseModel):
    source: str
    target: str


class GraphValidationReport(BaseModel):
    planned_edges_count: int
    extracted_edges_count: int
    matching_edges_count: int
    missing_edges_count: int
    extra_edges_count: int
    missing_edges_sample: list[GraphEdge]
    extra_edges_sample: list[GraphEdge]


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    validation: GraphValidationReport


class DocumentTermWeight(BaseModel):
    term: str
    tfidf: float
    tf: float
    idf: float


class DocumentLinkRef(BaseModel):
    doc_id: str
    title: str
    category: str


class DocumentDetailResponse(BaseModel):
    doc_id: str
    title: str
    category: str
    path: str
    word_count: int
    pagerank: float
    in_degree: int
    out_degree: int
    top_terms: list[DocumentTermWeight]
    in_links: list[DocumentLinkRef]
    out_links: list[DocumentLinkRef]
    content_preview: str
