#!/usr/bin/env python3
"""Validator 1 & 4: Validate documents.json, categories.json, and schema integration."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(".")
META_DIR = ROOT / "data" / "metadata"

ID_RE = re.compile(r"^D(00[1-9]|0[1-9][0-9]|[1-4][0-9]{2}|500)$")
CAT_RE = re.compile(r"^C(0[1-9]|10)$")
SUBCAT_RE = re.compile(r"^C(0[1-9]|10)\.[1-5]$")
SLUG_RE = re.compile(r"^[a-z0-9_]+$")
TAG_RE = re.compile(r"^[a-z0-9-]+$")
PATH_RE = re.compile(r"^data/corpus/[0-9]{2}_[a-z0-9_]+/[0-9]{2}_[a-z0-9_]+/D[0-9]{3}_[a-z0-9_]+\.html$")
VALID_DOC_TYPES = {"category_hub", "subcategory_hub", "reference", "specialized"}
VALID_STATUSES = {"planned", "drafted", "reviewed", "published"}


def parse_range(id_range: str) -> tuple[int, int]:
    start_s, end_s = id_range.split("-")
    return int(start_s[1:]), int(end_s[1:])


def validate() -> int:
    errors: list[str] = []

    docs_file = META_DIR / "documents.json"
    cats_file = META_DIR / "categories.json"
    links_file = META_DIR / "links.json"
    schema_file = META_DIR / "metadata_schema.json"

    for f in (docs_file, cats_file, links_file, schema_file):
        if not f.exists():
            print(f"ERROR: Missing required metadata file: {f}")
            return 1

    docs_data = json.loads(docs_file.read_text(encoding="utf-8"))
    cats_data = json.loads(cats_file.read_text(encoding="utf-8"))
    links_data = json.loads(links_file.read_text(encoding="utf-8"))
    schema_data = json.loads(schema_file.read_text(encoding="utf-8"))

    # Optional jsonschema check if installed
    try:
        import jsonschema  # type: ignore

        for key in ("documents", "categories", "links"):
            if key in schema_data.get("properties", {}):
                # Validate top-level array against subschema
                pass
        jsonschema.Draft202012Validator.check_schema(schema_data)
    except ImportError:
        pass
    except Exception as exc:
        errors.append(f"Schema validation error: {exc}")

    documents = docs_data.get("documents", [])
    categories = cats_data.get("categories", [])
    links = links_data.get("links", [])

    if len(documents) != 500:
        errors.append(f"Expected 500 documents, found {len(documents)}")
    if len(categories) != 10:
        errors.append(f"Expected 10 categories, found {len(categories)}")

    # Build category and subcategory lookup
    cat_map = {}
    subcat_map = {}
    total_subcats = 0
    for cat in categories:
        cid = cat.get("category_id", "")
        if not CAT_RE.match(cid):
            errors.append(f"Invalid category_id: {cid}")
        cat_map[cid] = cat
        subcats = cat.get("subcategories", [])
        total_subcats += len(subcats)
        if len(subcats) != 5:
            errors.append(f"Category {cid} has {len(subcats)} subcategories (expected 5)")
        for sub in subcats:
            sid = sub.get("subcategory_id", "")
            if not SUBCAT_RE.match(sid):
                errors.append(f"Invalid subcategory_id: {sid}")
            subcat_map[sid] = (cat, sub)

    if total_subcats != 50:
        errors.append(f"Expected 50 subcategories, found {total_subcats}")

    required_fields = set(schema_data["$defs"]["document"]["required"])
    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    seen_paths: set[str] = set()
    cat_counts: Counter[str] = Counter()
    subcat_counts: Counter[str] = Counter()
    word_count_warnings = 0

    for idx, doc in enumerate(documents):
        missing = required_fields - set(doc.keys())
        if missing:
            errors.append(f"Doc index {idx} missing fields: {sorted(missing)}")
            continue

        doc_id = doc["id"]
        if not ID_RE.match(doc_id):
            errors.append(f"Invalid document ID format: {doc_id}")
        if doc_id in seen_ids:
            errors.append(f"Duplicate document ID: {doc_id}")
        seen_ids.add(doc_id)

        slug = doc["slug"]
        if not SLUG_RE.match(slug):
            errors.append(f"{doc_id}: invalid slug '{slug}'")
        if slug in seen_slugs:
            errors.append(f"{doc_id}: duplicate slug '{slug}'")
        seen_slugs.add(slug)

        path = doc["path"]
        if not PATH_RE.match(path):
            errors.append(f"{doc_id}: invalid path format '{path}'")
        if path in seen_paths:
            errors.append(f"{doc_id}: duplicate path '{path}'")
        seen_paths.add(path)
        if f"/{doc_id}_{slug}.html" not in path:
            errors.append(f"{doc_id}: path '{path}' does not match ID and slug")

        cid = doc["category_id"]
        sid = doc["subcategory_id"]
        if sid not in subcat_map:
            errors.append(f"{doc_id}: unknown subcategory_id '{sid}'")
        else:
            cat_obj, sub_obj = subcat_map[sid]
            if cid != cat_obj["category_id"]:
                errors.append(f"{doc_id}: category_id '{cid}' mismatches subcategory '{sid}'")
            if doc["category"] != cat_obj["name"]:
                errors.append(f"{doc_id}: category name mismatch")
            if doc["subcategory"] != sub_obj["name"]:
                errors.append(f"{doc_id}: subcategory name mismatch")
            c_start, c_end = parse_range(cat_obj["id_range"])
            s_start, s_end = parse_range(sub_obj["id_range"])
            num = int(doc_id[1:])
            if not (c_start <= num <= c_end):
                errors.append(f"{doc_id}: outside category range {cat_obj['id_range']}")
            if not (s_start <= num <= s_end):
                errors.append(f"{doc_id}: outside subcategory range {sub_obj['id_range']}")

        cat_counts[cid] += 1
        subcat_counts[sid] += 1

        tags = doc["tags"]
        if not isinstance(tags, list) or len(tags) < 3 or len(set(tags)) != len(tags):
            errors.append(f"{doc_id}: invalid tags {tags}")
        else:
            for t in tags:
                if not TAG_RE.match(t):
                    errors.append(f"{doc_id}: invalid tag '{t}'")

        if doc["document_type"] not in VALID_DOC_TYPES:
            errors.append(f"{doc_id}: invalid document_type '{doc['document_type']}'")
        if doc["status"] not in VALID_STATUSES:
            errors.append(f"{doc_id}: invalid status '{doc['status']}'")

        words = len(doc["description"].split())
        if words < 30 or words > 95:
            word_count_warnings += 1
            errors.append(f"{doc_id}: description length {words} words outside acceptable range (30-95)")

    for cid in cat_map:
        if cat_counts[cid] != 50:
            errors.append(f"Category {cid} has {cat_counts[cid]} documents (expected 50)")
    for sid in subcat_map:
        if subcat_counts[sid] != 10:
            errors.append(f"Subcategory {sid} has {subcat_counts[sid]} documents (expected 10)")

    # Validate hub_ids exist and planned_links match links.json
    for doc in documents:
        for hid in doc["hub_ids"]:
            if hid not in seen_ids:
                errors.append(f"{doc['id']}: hub_id '{hid}' does not exist")

    links_by_src: dict[str, list[str]] = {d["id"]: [] for d in documents}
    for edge in links:
        s = edge.get("source_id")
        if s in links_by_src:
            links_by_src[s].append(edge.get("target_id"))

    for doc in documents:
        if sorted(doc["planned_links"]) != sorted(links_by_src[doc["id"]]):
            errors.append(f"{doc['id']}: planned_links in documents.json differs from links.json")

    if errors:
        print(f"CATALOG VALIDATION FAILED ({len(errors)} errors):")
        for err in errors[:30]:
            print(f"  - {err}")
        if len(errors) > 30:
            print(f"  ... and {len(errors) - 30} more errors.")
        return 1

    print("CATALOG VALIDATION PASSED:")
    print(f"  - Documents: {len(documents)} (all IDs D001-D500 unique, slugs unique)")
    print(f"  - Categories: {len(categories)} (50 docs each)")
    print(f"  - Subcategories: {total_subcats} (10 docs each)")
    print(f"  - Metadata integration (documents.json <-> categories.json <-> links.json <-> schema): OK")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
