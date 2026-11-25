#!/usr/bin/env python3
"""Validator 3: Validate the 50 physical corpus directories against categories.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(".")
CORPUS_DIR = ROOT / "data" / "corpus"
CATS_FILE = ROOT / "data" / "metadata" / "categories.json"


def validate() -> int:
    errors: list[str] = []

    if not CORPUS_DIR.exists():
        print(f"ERROR: Missing corpus directory: {CORPUS_DIR}")
        return 1

    cats_data = json.loads(CATS_FILE.read_text(encoding="utf-8"))
    expected_cat_dirs: set[str] = set()
    expected_sub_dirs: set[Path] = set()

    for cat in cats_data["categories"]:
        cat_dir = CORPUS_DIR / cat["dir_name"]
        expected_cat_dirs.add(cat["dir_name"])
        if not cat_dir.is_dir():
            errors.append(f"Missing category directory: {cat_dir}")
            continue
        for sub in cat["subcategories"]:
            sub_dir = cat_dir / sub["dir_name"]
            expected_sub_dirs.add(sub_dir)
            if not sub_dir.is_dir():
                errors.append(f"Missing subcategory directory: {sub_dir}")

    # Check for unknown directories
    actual_cat_dirs = {p.name for p in CORPUS_DIR.iterdir() if p.is_dir()}
    unknown_cats = actual_cat_dirs - expected_cat_dirs
    if unknown_cats:
        errors.append(f"Unknown category directories: {sorted(unknown_cats)}")

    actual_sub_dirs = {
        sub for cat in CORPUS_DIR.iterdir() if cat.is_dir() for sub in cat.iterdir() if sub.is_dir()
    }
    unknown_subs = actual_sub_dirs - expected_sub_dirs
    if unknown_subs:
        errors.append(f"Unknown subcategory directories: {[str(p) for p in sorted(unknown_subs)]}")

    # Ensure no 500 empty HTML files were prematurely created
    html_files = list(CORPUS_DIR.rglob("*.html"))
    if html_files:
        errors.append(f"Found {len(html_files)} HTML files inside data/corpus/ (expected 0 in planning phase)")

    if errors:
        print(f"DIRECTORY VALIDATION FAILED ({len(errors)} errors):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("DIRECTORY VALIDATION PASSED:")
    print(f"  - Category directories: {len(actual_cat_dirs)}/10")
    print(f"  - Subcategory directories: {len(actual_sub_dirs)}/50")
    print("  - No unknown directories, no premature HTML articles.")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
