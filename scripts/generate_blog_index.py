#!/usr/bin/env python3
"""Generate blog/posts/index.json from Markdown frontmatter."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "blog" / "posts"
INDEX_PATH = POSTS_DIR / "index.json"
FRONTMATTER_RE = re.compile(r"^---\s*\n(?P<body>.*?)\n---\s*", re.DOTALL)
REQUIRED_FIELDS = ("title", "date", "author", "tags", "excerpt")


def parse_scalar(value: str):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def parse_value(value: str):
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part) for part in inner.split(",")]
    return parse_scalar(value)


def parse_frontmatter(markdown: str, path: Path) -> dict:
    match = FRONTMATTER_RE.match(markdown)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter")

    metadata = {}
    for line in match.group("body").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"{path}: invalid frontmatter line: {line}")
        metadata[key.strip()] = parse_value(value)

    missing = [field for field in REQUIRED_FIELDS if field not in metadata]
    if missing:
        raise ValueError(f"{path}: missing required frontmatter field(s): {', '.join(missing)}")
    if not isinstance(metadata["tags"], list):
        raise ValueError(f"{path}: tags must use inline array syntax, e.g. [iLEAPP, research]")

    return metadata


def post_entry(path: Path) -> dict:
    metadata = parse_frontmatter(path.read_text(encoding="utf-8-sig"), path)
    entry = {
        "slug": path.stem,
        "title": metadata["title"],
        "date": metadata["date"],
        "author": metadata["author"],
        "tags": metadata["tags"],
        "excerpt": metadata["excerpt"],
    }
    if metadata.get("pinned"):
        entry["pinned"] = True
    return entry


def main() -> None:
    posts = [post_entry(path) for path in sorted(POSTS_DIR.glob("*.md"))]

    pinned = [post for post in posts if post.get("pinned")]
    unpinned = [post for post in posts if not post.get("pinned")]
    pinned.sort(key=lambda post: (post.get("date", ""), post.get("slug", "")), reverse=True)
    unpinned.sort(key=lambda post: (post.get("date", ""), post.get("slug", "")), reverse=True)

    INDEX_PATH.write_text(
        json.dumps(pinned + unpinned, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
