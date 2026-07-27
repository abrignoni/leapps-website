#!/usr/bin/env python3
"""Generate data/recent-artifacts.json — parsers recently added to the LEAPP repos.

Scans each parser repo's commit history for scripts/artifacts and collects .py
files with status "added" within the last WINDOW_DAYS. The artifacts page
renders these as a "recently added" strip, so returning visitors can see new
parser coverage at a glance (and deep-link into the artifact browser).

Runs in CI from .github/workflows/download-snapshot.yml with GH_TOKEN set;
works unauthenticated too (lower rate limit) for local runs.
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "recent-artifacts.json"

REPOS = {
    "iLEAPP": "abrignoni/iLEAPP",
    "ALEAPP": "abrignoni/ALEAPP",
    "RLEAPP": "abrignoni/RLEAPP",
    "VLEAPP": "abrignoni/VLEAPP",
    "DLEAPP": "abrignoni/DLEAPP",
}
WINDOW_DAYS = 45
# All commits in the window get a detail fetch (needed to see per-file add
# status); one page of 100 bounds the worst case. The newest 10 alone is not
# enough — busy modification sweeps (e.g. repo-wide refactors) can push the
# commits that ADDED files past any small cap.
MAX_COMMITS_PER_REPO = 100
MAX_ITEMS = 12


def gh(url: str):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    since = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    items: dict[tuple[str, str], dict] = {}  # (repo, file) -> item, newest wins

    for tool, repo in REPOS.items():
        commits = gh(
            f"https://api.github.com/repos/{repo}/commits"
            f"?path=scripts/artifacts&since={since}&per_page={MAX_COMMITS_PER_REPO}"
        )
        for c in commits:
            detail = gh(f"https://api.github.com/repos/{repo}/commits/{c['sha']}")
            date = c["commit"]["committer"]["date"]
            for f in detail.get("files", []):
                fn = f.get("filename", "")
                if (
                    f.get("status") == "added"
                    and fn.startswith("scripts/artifacts/")
                    and fn.endswith(".py")
                    and not fn.endswith("__init__.py")
                ):
                    stem = fn.rsplit("/", 1)[-1][:-3]
                    key = (repo, fn)
                    if key not in items or date > items[key]["date"]:
                        items[key] = {
                            "name": stem.replace("_", " "),
                            "query": stem,
                            "tool": tool,
                            "date": date[:10],
                        }

    # Round-robin across tools (each tool's additions newest-first, tools
    # ordered by their newest addition) instead of a flat date sort: a bulk
    # sweep that adds a dozen parsers to ONE repo must not evict every other
    # tool from the strip. Every tool with recent additions gets represented;
    # if only one tool has additions, it still fills all the slots.
    by_tool: dict[str, list[dict]] = {}
    for item in items.values():
        by_tool.setdefault(item["tool"], []).append(item)
    for lst in by_tool.values():
        lst.sort(key=lambda i: i["date"], reverse=True)
    tool_order = sorted(by_tool, key=lambda t: by_tool[t][0]["date"], reverse=True)

    ranked: list[dict] = []
    while len(ranked) < MAX_ITEMS and any(by_tool.values()):
        for t in tool_order:
            if by_tool[t]:
                ranked.append(by_tool[t].pop(0))
                if len(ranked) >= MAX_ITEMS:
                    break
    OUT_PATH.write_text(
        json.dumps(
            {
                "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "window_days": WINDOW_DAYS,
                "items": ranked,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT_PATH.relative_to(ROOT)} — {len(ranked)} recent artifact(s)")


if __name__ == "__main__":
    main()
