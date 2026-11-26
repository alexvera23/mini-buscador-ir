#!/usr/bin/env python3
"""Structural graph analyzer for the planned IR corpus."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(".")
META_DIR = ROOT / "data" / "metadata"


def count_weak_components(nodes: list[str], adj: dict[str, set[str]], radj: dict[str, set[str]]) -> list[int]:
    visited: set[str] = set()
    sizes: list[int] = []
    for start in nodes:
        if start in visited:
            continue
        q = deque([start])
        visited.add(start)
        size = 0
        while q:
            u = q.popleft()
            size += 1
            for v in adj[u] | radj[u]:
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def tarjan_scc(nodes: list[str], adj: dict[str, set[str]]) -> list[list[str]]:
    """Iterative Tarjan strongly connected components algorithm."""
    index = 0
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    sccs: list[list[str]] = []

    for start in nodes:
        if start in indices:
            continue
        call_stack: list[tuple[str, list[str], int]] = [(start, sorted(adj[start]), 0)]
        indices[start] = lowlink[start] = index
        index += 1
        stack.append(start)
        on_stack.add(start)

        while call_stack:
            v, nbrs, i = call_stack[-1]
            if i < len(nbrs):
                w = nbrs[i]
                call_stack[-1] = (v, nbrs, i + 1)
                if w not in indices:
                    indices[w] = lowlink[w] = index
                    index += 1
                    stack.append(w)
                    on_stack.add(w)
                    call_stack.append((w, sorted(adj[w]), 0))
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], indices[w])
            else:
                call_stack.pop()
                if call_stack:
                    parent = call_stack[-1][0]
                    lowlink[parent] = min(lowlink[parent], lowlink[v])
                if lowlink[v] == indices[v]:
                    comp: list[str] = []
                    while True:
                        w = stack.pop()
                        on_stack.remove(w)
                        comp.append(w)
                        if w == v:
                            break
                    sccs.append(comp)

    return sorted(sccs, key=len, reverse=True)


def bfs_reachable(starts: list[str], adj: dict[str, set[str]]) -> set[str]:
    visited = set(starts)
    q = deque(starts)
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in visited:
                visited.add(v)
                q.append(v)
    return visited


def main() -> int:
    docs_data = json.loads((META_DIR / "documents.json").read_text(encoding="utf-8"))
    cats_data = json.loads((META_DIR / "categories.json").read_text(encoding="utf-8"))
    links_data = json.loads((META_DIR / "links.json").read_text(encoding="utf-8"))

    docs = {d["id"]: d for d in docs_data["documents"]}
    nodes = sorted(docs.keys())
    links = links_data["links"]

    adj: dict[str, set[str]] = {n: set() for n in nodes}
    radj: dict[str, set[str]] = {n: set() for n in nodes}
    dup_count = 0
    invalid_targets: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for edge in links:
        s, t = edge["source_id"], edge["target_id"]
        if (s, t) in seen:
            dup_count += 1
        seen.add((s, t))
        if s not in docs or t not in docs:
            invalid_targets.append((s, t))
            continue
        adj[s].add(t)
        radj[t].add(s)

    n_nodes = len(nodes)
    n_edges = len(seen)
    out_degs = [len(adj[n]) for n in nodes]
    in_degs = [len(radj[n]) for n in nodes]

    zero_out = [n for n in nodes if len(adj[n]) == 0]
    zero_in = [n for n in nodes if len(radj[n]) == 0]
    isolated = [n for n in nodes if len(adj[n]) == 0 and len(radj[n]) == 0]

    density = n_edges / (n_nodes * (n_nodes - 1)) if n_nodes > 1 else 0.0
    weak_comps = count_weak_components(nodes, adj, radj)
    sccs = tarjan_scc(nodes, adj)

    cat_hubs = [h for c in cats_data["categories"] for h in c["category_hub_ids"]]
    reachable_from_cat_hubs = bfs_reachable(cat_hubs, adj)

    # Inter-category matrix
    inter_cat: dict[str, Counter[str]] = defaultdict(Counter)
    for s, t in seen:
        if s in docs and t in docs:
            inter_cat[docs[s]["category_id"]][docs[t]["category_id"]] += 1

    print("=== GRAPH STRUCTURAL ANALYSIS ===")
    print(f"Nodes: {n_nodes}")
    print(f"Edges: {n_edges}")
    print(f"Density: {density:.5f}")
    print(f"Duplicate edges: {dup_count}")
    print(f"Invalid endpoints: {len(invalid_targets)}")
    print(f"Zero out-degree (dangling for PageRank): {len(zero_out)}")
    print(f"Zero in-degree: {len(zero_in)}")
    print(f"Isolated nodes: {len(isolated)}")
    print(f"Out-degree: min={min(out_degs)}, max={max(out_degs)}, avg={sum(out_degs)/n_nodes:.2f}")
    print(f"In-degree:  min={min(in_degs)}, max={max(in_degs)}, avg={sum(in_degs)/n_nodes:.2f}")
    print(f"Out-degree distribution: {dict(sorted(Counter(out_degs).items()))}")
    print(f"Weakly connected components: {len(weak_comps)} (sizes={weak_comps})")
    print(f"Strongly connected components: {len(sccs)} (top sizes={[len(c) for c in sccs[:5]]})")
    print(f"Reachable from the 10 category hubs: {len(reachable_from_cat_hubs)}/{n_nodes}")

    print("\nTop 10 nodes by in-degree:")
    for nid, deg in sorted(((n, len(radj[n])) for n in nodes), key=lambda x: (-x[1], x[0]))[:10]:
        print(f"  {nid} ({docs[nid]['document_type']}): in={deg}, out={len(adj[nid])} — {docs[nid]['title']}")

    print("\nInter-category edge matrix (source -> targets):")
    cat_ids = [c["category_id"] for c in cats_data["categories"]]
    header = "SRC\\TGT " + " ".join(f"{c:>4}" for c in cat_ids)
    print(header)
    for sc in cat_ids:
        row = f"{sc:>7} " + " ".join(f"{inter_cat[sc][tc]:>4}" for tc in cat_ids)
        print(row)

    return 0


if __name__ == "__main__":
    sys.exit(main())
