#!/usr/bin/env python3
"""Validator 2: Validate planned links in data/metadata/links.json."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(".")
META_DIR = ROOT / "data" / "metadata"

VALID_RELATIONS = {
    "intra_subcategory",
    "related_concept",
    "category_navigation",
    "prerequisite",
    "implementation",
    "comparison",
    "security_relation",
    "architecture_relation",
}


def validate() -> int:
    errors: list[str] = []

    docs_data = json.loads((META_DIR / "documents.json").read_text(encoding="utf-8"))
    cats_data = json.loads((META_DIR / "categories.json").read_text(encoding="utf-8"))
    links_data = json.loads((META_DIR / "links.json").read_text(encoding="utf-8"))

    docs = {d["id"]: d for d in docs_data["documents"]}
    links = links_data["links"]

    seen_edges: set[tuple[str, str]] = set()
    out_deg: Counter[str] = Counter()
    in_deg: Counter[str] = Counter()
    rel_counts: Counter[str] = Counter()

    for idx, edge in enumerate(links):
        src = edge.get("source_id", "")
        tgt = edge.get("target_id", "")
        rel = edge.get("relation_type", "")
        just = edge.get("justification", "")

        if src not in docs:
            errors.append(f"Edge {idx}: invalid source_id '{src}'")
        if tgt not in docs:
            errors.append(f"Edge {idx}: invalid target_id '{tgt}'")
        if src == tgt:
            errors.append(f"Edge {idx}: self-loop on '{src}'")
        if (src, tgt) in seen_edges:
            errors.append(f"Edge {idx}: duplicate edge ({src} -> {tgt})")
        seen_edges.add((src, tgt))

        if rel not in VALID_RELATIONS:
            errors.append(f"Edge {idx} ({src}->{tgt}): invalid relation_type '{rel}'")
        if not isinstance(just, str) or len(just.strip()) < 10:
            errors.append(f"Edge {idx} ({src}->{tgt}): empty or too short justification")

        if src in docs and tgt in docs:
            if rel == "intra_subcategory" and docs[src]["subcategory_id"] != docs[tgt]["subcategory_id"]:
                errors.append(f"Edge ({src}->{tgt}): marked intra_subcategory across different subcategories")

        out_deg[src] += 1
        in_deg[tgt] += 1
        rel_counts[rel] += 1

    # Check isolated nodes, zero out-degree, zero in-degree, and hub coherence
    no_out = [did for did in docs if out_deg[did] == 0]
    no_in = [did for did in docs if in_deg[did] == 0]
    isolated = [did for did in docs if out_deg[did] == 0 and in_deg[did] == 0]

    if no_out:
        errors.append(f"Nodes with 0 outgoing links: {no_out[:10]}")
    if no_in:
        errors.append(f"Nodes with 0 incoming links: {no_in[:10]}")
    if isolated:
        errors.append(f"Isolated nodes: {isolated[:10]}")

    # Check category hub coherence
    for cat in cats_data["categories"]:
        for chub in cat["category_hub_ids"]:
            if out_deg[chub] < 5:
                errors.append(f"Category hub {chub} has too few outgoing links ({out_deg[chub]})")

    if errors:
        print(f"LINKS VALIDATION FAILED ({len(errors)} errors):")
        for err in errors[:30]:
            print(f"  - {err}")
        return 1

    print("LINKS VALIDATION PASSED:")
    print(f"  - Total edges: {len(links)}")
    print(f"  - Out-degree range: {min(out_deg.values())}..{max(out_deg.values())}")
    print(f"  - In-degree range: {min(in_deg.values())}..{max(in_deg.values())}")
    print(f"  - Isolated nodes: 0 | Zero out-degree: 0 | Zero in-degree: 0")
    print(f"  - Relation types: {dict(rel_counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
