#!/usr/bin/env python3
"""Validate search-index.json, and keep the Worker from growing a second copy of it.

The site search index used to exist twice: as this file, which every page
fetches, and as a hardcoded array inside handleSearchIndex() in
leapps-worker.js, which the /search-index route served. Both were maintained by
hand and nothing compared them, so they drifted. The Worker copy fell seven
entries behind, was missing DLEAPP entirely, and both described VLEAPP as
reading logical acquisitions long after it could read raw head unit images.

The Worker now fetches this file instead of carrying its own copy, so the drift
cannot happen again by construction. This script exists to keep it that way and
to check the one remaining copy, because search-index.json is written by hand
and has no generator behind it.

Two things are checked:

    1. search-index.json parses, is a list, and every entry carries the fields
       the search UI reads, with no duplicate titles and no obviously broken URL.
    2. leapps-worker.js does not define search entries inline. That is the
       regression guard: re-introducing a hardcoded array is what this whole
       change removes, and it would be invisible until the two disagreed again.

Usage:
    python3 scripts/check_search_index.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "search-index.json"
WORKER_PATH = ROOT / "leapps-worker.js"

REQUIRED_FIELDS = ("title", "url", "page", "excerpt")

# An inline entry looks like `{ title: "...", url: "..." ...}` in JS source. The
# check is deliberately about *entries*, not about the word "title": the Worker
# may legitimately mention search-index.json, fetch it, and cache it.
INLINE_ENTRY_RE = re.compile(r"\{\s*title:\s*[\"']")


def check_index(errors: list) -> int:
    if not INDEX_PATH.is_file():
        errors.append(f"{INDEX_PATH.name}: not found")
        return 0
    try:
        entries = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{INDEX_PATH.name}: is not valid JSON ({exc})")
        return 0

    if not isinstance(entries, list):
        errors.append(f"{INDEX_PATH.name}: top level must be a list of entries")
        return 0
    if not entries:
        errors.append(f"{INDEX_PATH.name}: is empty")
        return 0

    seen = {}
    for i, entry in enumerate(entries):
        where = f"{INDEX_PATH.name}[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: entry is not an object")
            continue
        for field in REQUIRED_FIELDS:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{where}: missing or empty \"{field}\"")
        url = entry.get("url", "")
        if isinstance(url, str) and url and not url.startswith("https://"):
            errors.append(f"{where}: url should be absolute https, got {url!r}")
        title = entry.get("title")
        if isinstance(title, str):
            if title in seen:
                errors.append(
                    f"{where}: duplicate title {title!r}, also at index {seen[title]}")
            else:
                seen[title] = i
    return len(entries)


def check_worker_has_no_copy(errors: list) -> None:
    if not WORKER_PATH.is_file():
        errors.append(f"{WORKER_PATH.name}: not found")
        return
    source = WORKER_PATH.read_text(encoding="utf-8")
    inline = INLINE_ENTRY_RE.findall(source)
    if inline:
        errors.append(
            f"{WORKER_PATH.name}: found {len(inline)} inline search entr"
            f"{'y' if len(inline) == 1 else 'ies'}. The Worker must fetch "
            f"{INDEX_PATH.name} rather than carry its own copy; a second copy "
            "drifts silently, which is the defect this check exists to prevent.")
    if "search-index.json" not in source:
        errors.append(
            f"{WORKER_PATH.name}: no reference to {INDEX_PATH.name}. The "
            "/search-index route is supposed to serve that file.")


def main() -> int:
    errors: list = []
    count = check_index(errors)
    check_worker_has_no_copy(errors)

    if errors:
        print("Search index problems:\n")
        for err in errors:
            print(f"  {err}")
        print()
        return 1

    print(f"search-index.json valid: {count} entries, "
          "and the Worker holds no second copy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
