from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal

from app.core.evaluator import Evaluator
from app.core.graph_engine import GraphEngine
from app.core.inverted_index import InvertedIndex
from app.models.schemas import (
    DocumentDetailResponse,
    DocumentLinkRef,
    DocumentTermWeight,
    EvaluationComparisonResponse,
    GraphEdge,
    GraphNode,
    GraphResponse,
    SearchResponse,
    SearchResultItem,
    StatsResponse,
    TermFrequencyItem,
    TopHITSItem,
    TopPageRankItem,
)
from app.utils.parser import ParsedDocument, normalize_text, parse_corpus


def _resolve_data_dir() -> Path:
    env_dir = os.getenv("DATA_DIR")
    if env_dir:
        return Path(env_dir)
    docker_data = Path("/app/data")
    if docker_data.exists():
        return docker_data
    # Fallback relativo al repositorio (backend/app/core/search_engine.py -> repo/data)
    return Path(__file__).resolve().parents[3] / "data"


class SearchEngine:
    """Motor unificado de Recuperación de Información (TF-IDF + PageRank)."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir: Path = data_dir or _resolve_data_dir()
        self.corpus_dir: Path = self.data_dir / "corpus"
        self.categories_file: Path = self.data_dir / "metadata" / "categories.json"
        self.links_file: Path = self.data_dir / "metadata" / "links.json"

        self.documents: list[ParsedDocument] = parse_corpus(
            self.corpus_dir, self.categories_file
        )
        self.doc_map: dict[str, ParsedDocument] = {
            doc.doc_id: doc for doc in self.documents
        }
        self.index: InvertedIndex = InvertedIndex(self.documents)
        self.graph: GraphEngine = GraphEngine(self.documents)
        self.evaluator: Evaluator = Evaluator(self.data_dir / "relevance_judgments.json")

    def _build_snippet(self, text: str, matched_terms: list[str], max_len: int = 240) -> str:
        if not text:
            return ""

        if not matched_terms:
            snippet = text[:max_len].strip()
            return f"{snippet}..." if len(text) > max_len else snippet

        # Buscar primera aparición de cualquier término coincidente usando texto normalizado
        norm_text = normalize_text(text)
        first_pos = -1
        for term in matched_terms:
            match = re.search(rf"\b{re.escape(term)}\w*", norm_text)
            if match:
                pos = match.start()
                if first_pos == -1 or pos < first_pos:
                    first_pos = pos

        if first_pos == -1:
            start = 0
        else:
            start = max(0, first_pos - 70)
            if start > 0:
                space_idx = text.find(" ", start)
                if space_idx != -1 and space_idx < first_pos:
                    start = space_idx + 1

        end = min(len(text), start + max_len)
        if end < len(text):
            last_space = text.rfind(" ", start, end)
            if last_space > start + 60:
                end = last_space

        snippet = text[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        # Resaltar términos coincidentes en el snippet preservando mayúsculas/acentos originales
        term_set = set(matched_terms)
        def _highlight(m: re.Match[str]) -> str:
            word = m.group(0)
            norm_word = normalize_text(word)
            for t in term_set:
                if norm_word == t or norm_word.startswith(t):
                    return f"<mark>{word}</mark>"
            return word

        return re.sub(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", _highlight, snippet)

    def search(
        self,
        query: str,
        mode: Literal["tfidf", "pagerank", "hits", "hybrid"] = "hybrid",
        alpha: float = 0.7,
        limit: int = 10,
    ) -> SearchResponse:
        tfidf_scores, matched_map, query_terms = self.index.search(query)

        # Determinar candidatos según el modo
        if mode == "tfidf":
            candidate_ids = list(tfidf_scores.keys())
        elif mode == "pagerank":
            # Si hay consulta con coincidencias textuales, rankear esos candidatos por PageRank;
            # si la consulta está vacía, mostrar top global por PageRank.
            if query.strip():
                candidate_ids = list(tfidf_scores.keys())
            else:
                candidate_ids = list(self.doc_map.keys())
        elif mode == "hits":
            candidate_ids = (
                list(tfidf_scores.keys()) if query.strip() else list(self.doc_map.keys())
            )
        else:
            # hybrid: combinar TF-IDF y PageRank sobre documentos con relevancia textual (o todos si q vacío)
            candidate_ids = (
                list(tfidf_scores.keys()) if query.strip() else list(self.doc_map.keys())
            )

        items: list[SearchResultItem] = []
        for doc_id in candidate_ids:
            doc = self.doc_map[doc_id]
            tfidf_val = tfidf_scores.get(doc_id, 0.0)
            pr_raw = self.graph.pagerank.get(doc_id, 0.0)
            pr_norm = self.graph.pagerank_norm.get(doc_id, 0.0)
            auth_norm = self.graph.authority_norm.get(doc_id, 0.0)

            if mode == "tfidf":
                combined = tfidf_val
            elif mode == "pagerank":
                combined = pr_raw
            elif mode == "hits":
                combined = alpha * tfidf_val + (1.0 - alpha) * auth_norm
            else:
                combined = alpha * tfidf_val + (1.0 - alpha) * pr_norm

            matched = matched_map.get(doc_id, [])
            snippet = self._build_snippet(doc.text, matched or query_terms)

            items.append(
                SearchResultItem(
                    doc_id=doc_id,
                    title=doc.title,
                    category=doc.category,
                    path=doc.path,
                    snippet=snippet,
                    tfidf_score=round(tfidf_val, 6),
                    pagerank_score=round(pr_raw, 6),
                    combined_score=round(combined, 6),
                    matched_terms=matched,
                )
            )

        items.sort(key=lambda x: (x.combined_score, x.tfidf_score, x.pagerank_score), reverse=True)
        limited = items[:limit]

        return SearchResponse(
            query=query,
            mode=mode,
            alpha=alpha,
            total_results=len(items),
            results=limited,
        )

    def get_stats(self) -> StatsResponse:
        top_terms = [
            TermFrequencyItem(term=term, df=df, total_tf=total_tf)
            for term, df, total_tf in self.index.get_top_terms(limit=15)
        ]

        sorted_pr = sorted(
            self.graph.pagerank.items(), key=lambda kv: kv[1], reverse=True
        )[:10]
        top_pagerank = [
            TopPageRankItem(
                doc_id=doc_id,
                title=self.doc_map[doc_id].title,
                category=self.doc_map[doc_id].category,
                pagerank=round(pr_val, 6),
                in_degree=self.graph.in_degree(doc_id),
                out_degree=self.graph.out_degree(doc_id),
            )
            for doc_id, pr_val in sorted_pr
        ]

        pr_sum = sum(self.graph.pagerank.values())

        sorted_auth = sorted(
            self.graph.authority.items(), key=lambda kv: kv[1], reverse=True
        )[:10]
        top_authorities = [
            TopHITSItem(
                doc_id=doc_id,
                title=self.doc_map[doc_id].title,
                category=self.doc_map[doc_id].category,
                authority_score=round(self.graph.authority.get(doc_id, 0.0), 6),
                hub_score=round(self.graph.hub.get(doc_id, 0.0), 6),
                in_degree=self.graph.in_degree(doc_id),
                out_degree=self.graph.out_degree(doc_id),
            )
            for doc_id, _ in sorted_auth
        ]

        sorted_hubs = sorted(
            self.graph.hub.items(), key=lambda kv: kv[1], reverse=True
        )[:10]
        top_hubs = [
            TopHITSItem(
                doc_id=doc_id,
                title=self.doc_map[doc_id].title,
                category=self.doc_map[doc_id].category,
                authority_score=round(self.graph.authority.get(doc_id, 0.0), 6),
                hub_score=round(self.graph.hub.get(doc_id, 0.0), 6),
                in_degree=self.graph.in_degree(doc_id),
                out_degree=self.graph.out_degree(doc_id),
            )
            for doc_id, _ in sorted_hubs
        ]

        return StatsResponse(
            total_documents=self.index.total_documents,
            vocabulary_size=self.index.vocabulary_size,
            total_edges=len(self.graph.edges),
            pagerank_iterations=self.graph.iterations,
            pagerank_damping=self.graph.damping,
            pagerank_epsilon=self.graph.epsilon,
            pagerank_sum=round(pr_sum, 6),
            convergence_history=self.graph.convergence_history,
            hits_iterations=self.graph.hits_iterations,
            hits_convergence_history=self.graph.hits_convergence_history,
            top_terms=top_terms,
            top_pagerank=top_pagerank,
            top_authorities=top_authorities,
            top_hubs=top_hubs,
        )

    def get_graph(self) -> GraphResponse:
        nodes = [
            GraphNode(
                id=doc.doc_id,
                title=doc.title,
                category=doc.category,
                pagerank=round(self.graph.pagerank.get(doc.doc_id, 0.0), 6),
                authority_score=round(self.graph.authority.get(doc.doc_id, 0.0), 6),
                hub_score=round(self.graph.hub.get(doc.doc_id, 0.0), 6),
                in_degree=self.graph.in_degree(doc.doc_id),
                out_degree=self.graph.out_degree(doc.doc_id),
            )
            for doc in self.documents
        ]
        edges = [GraphEdge(source=s, target=t) for s, t in self.graph.edges]
        validation = self.graph.compare_with_planned_links(self.links_file)
        return GraphResponse(nodes=nodes, edges=edges, validation=validation)

    def evaluate(
        self, k: int = 5, alpha: float = 0.7, beta: float = 1.0
    ) -> EvaluationComparisonResponse:
        return self.evaluator.evaluate(engine=self, k=k, alpha=alpha, beta=beta)

    def get_document(self, doc_id: str) -> DocumentDetailResponse | None:
        doc = self.doc_map.get(doc_id)
        if doc is None:
            return None

        top_terms = [
            DocumentTermWeight(
                term=term,
                tfidf=round(tfidf, 6),
                tf=round(tf, 6),
                idf=round(idf, 6),
            )
            for term, tfidf, tf, idf in self.index.get_document_top_terms(doc_id, limit=15)
        ]

        in_links = [
            DocumentLinkRef(
                doc_id=src,
                title=self.doc_map[src].title,
                category=self.doc_map[src].category,
            )
            for src in self.graph.in_links.get(doc_id, [])
            if src in self.doc_map
        ]

        out_links = [
            DocumentLinkRef(
                doc_id=tgt,
                title=self.doc_map[tgt].title,
                category=self.doc_map[tgt].category,
            )
            for tgt in self.graph.out_links.get(doc_id, [])
            if tgt in self.doc_map
        ]

        preview = doc.text[:600].strip()
        if len(doc.text) > 600:
            preview += "..."

        return DocumentDetailResponse(
            doc_id=doc.doc_id,
            title=doc.title,
            category=doc.category,
            path=doc.path,
            word_count=self.index.doc_word_counts.get(doc_id, 0),
            pagerank=round(self.graph.pagerank.get(doc_id, 0.0), 6),
            in_degree=self.graph.in_degree(doc_id),
            out_degree=self.graph.out_degree(doc_id),
            top_terms=top_terms,
            in_links=in_links,
            out_links=out_links,
            content_preview=preview,
        )
