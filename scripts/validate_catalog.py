#!/usr/bin/env python3
"""Validator: Validate documents.json, categories.json, and schema integration."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(".")
META_DIR = ROOT / "data" / "metadata"

ID_RE = re.compile(r"^D[0-9]{3,}$")
CAT_RE = re.compile(r"^C(0[1-9]|10)$")
SLUG_RE = re.compile(r"^[a-z0-9_]+$")
FILENAME_RE = re.compile(r"^D[0-9]{3,}_[a-z0-9_]+\.html$")
PATH_RE = re.compile(r"^data/corpus/[0-9]{2}_[a-z0-9_]+/D[0-9]{3,}_[a-z0-9_]+\.html$")
VALID_DOC_TYPES = {"category_hub", "specialized"}
VALID_STATUSES = {"planned", "created"}


def validate() -> int:
    errors: list[str] = []
    warnings: list[str] = []

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

    # Validar categories.json
    categories = cats_data.get("categories", [])
    if len(categories) != 10:
        errors.append(f"Expected 10 categories, found {len(categories)}")
    if cats_data.get("total_categories") != len(categories):
        errors.append("categories.json total_categories mismatch")
    if "total_subcategories" in cats_data:
        errors.append("categories.json still contains obsolete total_subcategories")

    cat_map = {}
    for cat in categories:
        cid = cat.get("category_id")
        if not cid or not CAT_RE.match(cid):
            errors.append(f"Invalid category_id: {cid}")
            continue
        if "subcategories" in cat:
            errors.append(f"Category {cid} still contains obsolete subcategories")
        cat_map[cid] = cat

    # Validar documents.json
    documents = docs_data.get("documents", [])
    if docs_data.get("total_documents") != len(documents):
        errors.append(
            f"documents.json total_documents={docs_data.get('total_documents')} != {len(documents)}"
        )

    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    seen_paths: set[str] = set()
    cat_counts: Counter[str] = Counter()

    req_fields = set(schema_data["$defs"]["document"]["required"])

    for doc in documents:
        doc_id = doc.get("id", "<missing>")
        missing = req_fields - set(doc.keys())
        if missing:
            errors.append(f"{doc_id}: missing required fields {sorted(missing)}")
            continue

        for obsolete in ("subcategory_id", "subcategory_code", "subcategory"):
            if obsolete in doc:
                errors.append(f"{doc_id}: contains obsolete field '{obsolete}'")

        if not ID_RE.match(doc_id):
            errors.append(f"Invalid document id: {doc_id}")
        if doc_id in seen_ids:
            errors.append(f"Duplicate document id: {doc_id}")
        seen_ids.add(doc_id)

        slug = doc["slug"]
        if not SLUG_RE.match(slug):
            errors.append(f"{doc_id}: invalid slug '{slug}'")
        if slug in seen_slugs:
            errors.append(f"{doc_id}: duplicate slug '{slug}'")
        seen_slugs.add(slug)

        filename = doc["filename"]
        if not FILENAME_RE.match(filename):
            errors.append(f"{doc_id}: invalid filename '{filename}'")

        cid = doc["category_id"]
        if cid not in cat_map:
            errors.append(f"{doc_id}: unknown category_id '{cid}'")
        else:
            cat = cat_map[cid]
            expected_path = f"data/corpus/{cat['dir_name']}/{filename}"
            if doc["path"] != expected_path:
                errors.append(f"{doc_id}: path '{doc['path']}' != expected '{expected_path}'")
            if not PATH_RE.match(doc["path"]):
                errors.append(f"{doc_id}: path '{doc['path']}' does not match pattern")
            if doc["path"] in seen_paths:
                errors.append(f"{doc_id}: duplicate path '{doc['path']}'")
            seen_paths.add(doc["path"])
            cat_counts[cid] += 1

        if doc["document_type"] not in VALID_DOC_TYPES:
            errors.append(f"{doc_id}: invalid document_type '{doc['document_type']}'")
        if doc["status"] not in VALID_STATUSES:
            errors.append(f"{doc_id}: invalid status '{doc['status']}'")

    # Verificar cantidad de documentos por categoría (5-10 recomendado)
    for cid in cat_map:
        count = cat_counts[cid]
        if count < 5 or count > 10:
            warnings.append(f"Category {cid} has {count} documents (recommended: 5-10)")

    # Verificar coherencia con links.json
    links = links_data.get("links", [])
    if links_data.get("total_links") != len(links):
        errors.append("links.json total_links mismatch")

    for link in links:
        if link.get("source_id") not in seen_ids:
            errors.append(f"Link source_id '{link.get('source_id')}' not in documents.json")
        if link.get("target_id") not in seen_ids:
            errors.append(f"Link target_id '{link.get('target_id')}' not in documents.json")

    if errors:
        print(f"CATALOG VALIDATION FAILED ({len(errors)} errors):")
        for e in errors[:20]:
            print(f"  - {e}")
        return 1

    print("CATALOG VALIDATION PASSED:")
    print(f"  - Documents: {len(documents)} (all IDs and slugs unique)")
    print(f"  - Categories: {len(categories)} (counts: {dict(sorted(cat_counts.items()))})")
    if warnings:
        for w in warnings:
            print(f"  - WARNING: {w}")
    print("  - Metadata integration (documents.json <-> categories.json <-> links.json <-> schema): OK")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
