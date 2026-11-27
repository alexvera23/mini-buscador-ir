from __future__ import annotations

import json
import math
from pathlib import Path

from app.models.schemas import GraphEdge, GraphValidationReport
from app.utils.parser import ParsedDocument


class GraphEngine:
    """Grafo dirigido de documentos y cálculo de PageRank iterativo desde cero."""

    def __init__(
        self,
        documents: list[ParsedDocument],
        damping: float = 0.85,
        epsilon: float = 1e-6,
        max_iter: int = 100,
    ) -> None:
        self.damping: float = damping
        self.epsilon: float = epsilon
        self.max_iter: int = max_iter

        self.nodes: list[str] = [doc.doc_id for doc in documents]
        self.node_set: set[str] = set(self.nodes)
        self.out_links: dict[str, list[str]] = {doc.doc_id: [] for doc in documents}
        self.in_links: dict[str, list[str]] = {doc.doc_id: [] for doc in documents}
        self.edges: list[tuple[str, str]] = []

        self.pagerank: dict[str, float] = {}
        self.pagerank_norm: dict[str, float] = {}
        self.convergence_history: list[float] = []
        self.iterations: int = 0

        self.authority: dict[str, float] = {}
        self.hub: dict[str, float] = {}
        self.authority_norm: dict[str, float] = {}
        self.hub_norm: dict[str, float] = {}
        self.hits_convergence_history: list[float] = []
        self.hits_iterations: int = 0

        self._build_graph(documents)
        self._compute_pagerank()
        self._compute_hits()

    def _build_graph(self, documents: list[ParsedDocument]) -> None:
        seen_edges: set[tuple[str, str]] = set()
        for doc in documents:
            src = doc.doc_id
            for tgt in doc.out_links:
                if tgt in self.node_set and tgt != src and (src, tgt) not in seen_edges:
                    seen_edges.add((src, tgt))
                    self.out_links[src].append(tgt)
                    self.in_links[tgt].append(src)
                    self.edges.append((src, tgt))

    def _compute_pagerank(self) -> None:
        n = len(self.nodes)
        if n == 0:
            return

        d = self.damping
        base_teleport = (1.0 - d) / n
        pr: dict[str, float] = {node: 1.0 / n for node in self.nodes}
        dangling_nodes = [node for node in self.nodes if len(self.out_links[node]) == 0]

        self.convergence_history = []
        self.iterations = 0

        for iteration in range(1, self.max_iter + 1):
            dangling_sum = sum(pr[node] for node in dangling_nodes)
            dangling_contrib = d * dangling_sum / n

            new_pr: dict[str, float] = {}
            l1_diff = 0.0

            for node in self.nodes:
                inbound_sum = 0.0
                for src in self.in_links[node]:
                    out_deg = len(self.out_links[src])
                    if out_deg > 0:
                        inbound_sum += pr[src] / out_deg

                val = base_teleport + dangling_contrib + d * inbound_sum
                new_pr[node] = val
                l1_diff += abs(val - pr[node])

            pr = new_pr
            self.convergence_history.append(l1_diff)
            self.iterations = iteration

            if l1_diff < self.epsilon:
                break

        self.pagerank = pr
        max_pr = max(pr.values()) if pr else 0.0
        if max_pr > 0.0:
            self.pagerank_norm = {node: val / max_pr for node, val in pr.items()}
        else:
            self.pagerank_norm = {node: 0.0 for node in self.nodes}

    def _compute_hits(self) -> None:
        """Calcula iterativamente los puntajes Authority y Hub (algoritmo HITS)."""
        n = len(self.nodes)
        if n == 0:
            return

        auth: dict[str, float] = {node: 1.0 for node in self.nodes}
        hub: dict[str, float] = {node: 1.0 for node in self.nodes}

        self.hits_convergence_history = []
        self.hits_iterations = 0

        for iteration in range(1, self.max_iter + 1):
            # 1. Actualizar Authority: a^(t)(p) = sum_{q in In(p)} h^(t-1)(q)
            raw_auth: dict[str, float] = {
                node: sum(hub[src] for src in self.in_links[node])
                for node in self.nodes
            }
            auth_norm_l2 = math.sqrt(sum(v * v for v in raw_auth.values()))
            if auth_norm_l2 > 0.0:
                new_auth = {node: val / auth_norm_l2 for node, val in raw_auth.items()}
            else:
                new_auth = {node: 0.0 for node in self.nodes}

            # 2. Actualizar Hub: h^(t)(p) = sum_{q in Out(p)} a^(t)(q)
            raw_hub: dict[str, float] = {
                node: sum(new_auth[tgt] for tgt in self.out_links[node])
                for node in self.nodes
            }
            hub_norm_l2 = math.sqrt(sum(v * v for v in raw_hub.values()))
            if hub_norm_l2 > 0.0:
                new_hub = {node: val / hub_norm_l2 for node, val in raw_hub.items()}
            else:
                new_hub = {node: 0.0 for node in self.nodes}

            # 3. Criterio de convergencia: max(||a^(t) - a^(t-1)||_1, ||h^(t) - h^(t-1)||_1) < epsilon
            l1_auth = sum(abs(new_auth[node] - auth[node]) for node in self.nodes)
            l1_hub = sum(abs(new_hub[node] - hub[node]) for node in self.nodes)
            diff = max(l1_auth, l1_hub)

            auth = new_auth
            hub = new_hub
            self.hits_convergence_history.append(diff)
            self.hits_iterations = iteration

            if diff < self.epsilon:
                break

        self.authority = auth
        self.hub = hub

        max_auth = max(auth.values()) if auth else 0.0
        self.authority_norm = (
            {node: val / max_auth for node, val in auth.items()}
            if max_auth > 0.0
            else {node: 0.0 for node in self.nodes}
        )

        max_hub = max(hub.values()) if hub else 0.0
        self.hub_norm = (
            {node: val / max_hub for node, val in hub.items()}
            if max_hub > 0.0
            else {node: 0.0 for node in self.nodes}
        )

    def in_degree(self, doc_id: str) -> int:
        return len(self.in_links.get(doc_id, []))

    def out_degree(self, doc_id: str) -> int:
        return len(self.out_links.get(doc_id, []))

    def compare_with_planned_links(self, links_file: Path) -> GraphValidationReport:
        """Compara las aristas extraídas del HTML contra data/metadata/links.json.

        Solo evalúa aristas planificadas cuyos dos extremos existan en el corpus cargado
        (para no penalizar categorías aún no generadas), aunque reporta el total de links.json.
        """
        extracted_set = set(self.edges)

        if not links_file.exists():
            return GraphValidationReport(
                planned_edges_count=0,
                extracted_edges_count=len(extracted_set),
                matching_edges_count=0,
                missing_edges_count=0,
                extra_edges_count=len(extracted_set),
                missing_edges_sample=[],
                extra_edges_sample=[
                    GraphEdge(source=s, target=t) for s, t in sorted(extracted_set)[:20]
                ],
            )

        data = json.loads(links_file.read_text(encoding="utf-8"))
        planned_in_corpus: set[tuple[str, str]] = set()
        for link in data.get("links", []):
            src = link.get("source_id")
            tgt = link.get("target_id")
            if src in self.node_set and tgt in self.node_set and src != tgt:
                planned_in_corpus.add((src, tgt))

        matching = extracted_set & planned_in_corpus
        missing = sorted(planned_in_corpus - extracted_set)
        extra = sorted(extracted_set - planned_in_corpus)

        return GraphValidationReport(
            planned_edges_count=len(planned_in_corpus),
            extracted_edges_count=len(extracted_set),
            matching_edges_count=len(matching),
            missing_edges_count=len(missing),
            extra_edges_count=len(extra),
            missing_edges_sample=[GraphEdge(source=s, target=t) for s, t in missing[:20]],
            extra_edges_sample=[GraphEdge(source=s, target=t) for s, t in extra[:20]],
        )
