#!/usr/bin/env python3
"""Validator: Validate physical directory structure under data/corpus against categories.json and documents.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(".")
CORPUS_DIR = ROOT / "data" / "corpus"
META_DIR = ROOT / "data" / "metadata"


def validate() -> int:
    errors: list[str] = []

    if not CORPUS_DIR.exists():
        print(f"ERROR: Missing corpus directory: {CORPUS_DIR}")
        return 1

    cats_data = json.loads((META_DIR / "categories.json").read_text(encoding="utf-8"))
    docs_data = json.loads((META_DIR / "documents.json").read_text(encoding="utf-8"))

    expected_cat_dirs = {cat["dir_name"] for cat in cats_data["categories"]}
    actual_cat_dirs = {p.name for p in CORPUS_DIR.iterdir() if p.is_dir()}

    missing_dirs = expected_cat_dirs - actual_cat_dirs
    extra_dirs = actual_cat_dirs - expected_cat_dirs
    if missing_dirs:
        errors.append(f"Missing category directories: {sorted(missing_dirs)}")
    if extra_dirs:
        errors.append(f"Unexpected category directories: {sorted(extra_dirs)}")

    # Verificar ausencia de subdirectorios dentro de cada categoría
    for cat_dir_name in sorted(expected_cat_dirs & actual_cat_dirs):
        cat_path = CORPUS_DIR / cat_dir_name
        subdirs = [p.name for p in cat_path.iterdir() if p.is_dir()]
        if subdirs:
            errors.append(f"Subdirectories found in {cat_path}: {subdirs} (subcategories are not allowed)")

    # Verificar que todos los archivos HTML físicos estén en documents.json
    catalog_paths = {doc["path"] for doc in docs_data["documents"]}
    html_files = sorted(CORPUS_DIR.rglob("*.html"))
    for html_file in html_files:
        rel_path = html_file.as_posix()
        if rel_path not in catalog_paths:
            errors.append(f"Uncatalogued HTML file: {rel_path}")

    if errors:
        print(f"DIRECTORY VALIDATION FAILED ({len(errors)} errors):")
        for e in errors[:20]:
            print(f"  - {e}")
        return 1

    print("DIRECTORY VALIDATION PASSED:")
    print(f"  - Category directories: {len(actual_cat_dirs)}/10")
    print("  - Subcategory directories: 0")
    print(f"  - Catalogued HTML files present: {len(html_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
