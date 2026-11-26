#!/usr/bin/env python3
"""Validator: Validate links.json graph integrity and integration with documents.json."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(".")
META_DIR = ROOT / "data" / "metadata"
VALID_REL_TYPES = {
    "category_navigation",
    "related_concept",
    "prerequisite",
    "implementation",
    "architecture_relation",
    "security_relation",
    "comparison",
}


def validate() -> int:
    errors: list[str] = []

    docs_data = json.loads((META_DIR / "documents.json").read_text(encoding="utf-8"))
    links_data = json.loads((META_DIR / "links.json").read_text(encoding="utf-8"))

    doc_ids = {d["id"] for d in docs_data["documents"]}
    links = links_data.get("links", [])

    if links_data.get("total_links") != len(links):
        errors.append(f"total_links={links_data.get('total_links')} != {len(links)}")

    seen_edges: set[tuple[str, str]] = set()
    out_deg: Counter[str] = Counter()
    in_deg: Counter[str] = Counter()
    rel_counts: Counter[str] = Counter()

    for idx, link in enumerate(links):
        src = link.get("source_id")
        tgt = link.get("target_id")
        rel = link.get("relation_type")

        if src not in doc_ids:
            errors.append(f"Link[{idx}]: unknown source_id '{src}'")
        if tgt not in doc_ids:
            errors.append(f"Link[{idx}]: unknown target_id '{tgt}'")
        if src == tgt:
            errors.append(f"Link[{idx}]: self-loop on '{src}'")
        if (src, tgt) in seen_edges:
            errors.append(f"Link[{idx}]: duplicate edge ({src} -> {tgt})")
        seen_edges.add((src, tgt))

        if rel not in VALID_REL_TYPES:
            errors.append(f"Link[{idx}]: invalid relation_type '{rel}'")

        out_deg[src] += 1
        in_deg[tgt] += 1
        rel_counts[rel] += 1

    isolated = [did for did in doc_ids if out_deg[did] == 0 and in_deg[did] == 0]
    if isolated:
        errors.append(f"Isolated nodes found: {isolated[:10]}")

    if errors:
        print(f"LINKS VALIDATION FAILED ({len(errors)} errors):")
        for e in errors[:20]:
            print(f"  - {e}")
        return 1

    out_vals = [out_deg[d] for d in doc_ids]
    in_vals = [in_deg[d] for d in doc_ids]
    print("LINKS VALIDATION PASSED:")
    print(f"  - Nodes: {len(doc_ids)} | Total edges: {len(links)}")
    print(f"  - Out-degree range: {min(out_vals)}..{max(out_vals)}")
    print(f"  - In-degree range: {min(in_vals)}..{max(in_vals)}")
    print(f"  - Isolated nodes: {len(isolated)}")
    print(f"  - Relation types: {dict(rel_counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
