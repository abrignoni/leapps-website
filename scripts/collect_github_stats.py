#!/usr/bin/env python3
"""Collect GitHub statistics for the stats page: repository traffic, downloads by platform, stars.

Writes, beside data/downloads.json (which this script never touches):

  data/traffic/index.json      latest status, 14-day totals and the list of month files
  data/traffic/YYYY-MM.json    daily and weekly views and clones, referrer and path snapshots
  data/assets.json             downloads by OS and architecture per day, and by release
  data/community.json          stars over time and the last year of commit activity

GitHub keeps traffic for 14 days, so every run stores what the API returns and the history
grows from the first run on. The merge rules are the point of this file:

  - Daily and weekly points are upserted by repo and UTC date. The 14-day totals are never
    summed, because the windows overlap from one run to the next.
  - Referrers and popular paths are top-10 summaries of the last 14 days with no dates of their
    own. They are stored as one snapshot per collection day and never added together.
  - A failure is stored as a status, never as a zero.

The repo lists come from .github/workflows/download-snapshot.yml, so there is one list to keep.

Traffic needs repository Administration read, which GITHUB_TOKEN cannot give for other repos.
The workflow mints one GitHub App installation token per owner and passes them as
GH_TOKEN_ABRIGNONI and GH_TOKEN_LEAPPS_ORG. Without them, traffic is recorded as
"not_configured" and everything else is still collected with GH_TOKEN.

Usage:
  python3 scripts/collect_github_stats.py               collect and write
  python3 scripts/collect_github_stats.py --check-stale exit 1 when traffic is configured and a
                                                        repo has had no success for 3 days
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TRAFFIC_DIR = DATA / "traffic"
INDEX_PATH = TRAFFIC_DIR / "index.json"
ASSETS_PATH = DATA / "assets.json"
COMMUNITY_PATH = DATA / "community.json"
SNAPSHOT_WORKFLOW = ROOT / ".github" / "workflows" / "download-snapshot.yml"

SCHEMA_VERSION = 1
API = "https://api.github.com"
STALE_DAYS = 3
ACTIVITY_RETRY_SECONDS = 20
# LAVA's source repo (leapps-org/LAVA-beta) is private and deliberately absent: its traffic
# would show only people with access. LAVA-releases is what the snapshot workflow already uses.
OWNER_TOKEN_ENV = {"abrignoni": "GH_TOKEN_ABRIGNONI", "leapps-org": "GH_TOKEN_LEAPPS_ORG"}

TRAFFIC_KINDS = ("views", "clones", "referrers", "paths")


# --------------------------------------------------------------------------------------------
# Repo list
# --------------------------------------------------------------------------------------------

def load_repo_lists(workflow_path: Path = SNAPSHOT_WORKFLOW) -> dict[str, dict[str, str]]:
    """Read the REPOS and PROBES dicts out of the download snapshot workflow.

    Returns {"tool": {key: "owner/repo"}, "probe": {key: "owner/repo"}}.
    """
    text = workflow_path.read_text(encoding="utf-8")
    lists = {}
    for name, group in (("REPOS", "tool"), ("PROBES", "probe")):
        match = re.search(rf"^\s*{name}\s*=\s*(\{{.*?\}})", text, re.S | re.M)
        if not match:
            raise ValueError(f"{name} not found in {workflow_path}")
        lists[group] = ast.literal_eval(match.group(1))
    return lists


# --------------------------------------------------------------------------------------------
# Pure merge helpers (tested in scripts/tests/test_collect_github_stats.py)
# --------------------------------------------------------------------------------------------

def points_by_day(api_points: list[dict]) -> dict[str, dict]:
    """GitHub traffic points ("timestamp" at UTC midnight) -> {YYYY-MM-DD: {count, uniques}}."""
    out = {}
    for point in api_points or []:
        stamp = str(point.get("timestamp", ""))[:10]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", stamp):
            out[stamp] = {"count": point.get("count"), "uniques": point.get("uniques")}
    return out


def upsert_points(stored: dict, fresh: dict, label: str = "", log=print) -> dict:
    """Upsert fresh daily or weekly points into stored ones, by date.

    Every date GitHub returns is inside its current window, so GitHub's value replaces the
    stored one. A drop is kept (GitHub is authoritative) but logged, because it is unusual.
    Dates GitHub no longer returns are left as stored.
    """
    merged = dict(stored)
    for day, value in fresh.items():
        old = merged.get(day)
        if old and isinstance(old.get("count"), int) and isinstance(value.get("count"), int) \
                and value["count"] < old["count"]:
            log(f"note: {label} {day} count fell from {old['count']} to {value['count']}")
        merged[day] = value
    return dict(sorted(merged.items()))


def month_of(day: str) -> str:
    return day[:7]


def split_by_month(points: dict) -> dict[str, dict]:
    months: dict[str, dict] = {}
    for day, value in points.items():
        months.setdefault(month_of(day), {})[day] = value
    return months


CHECKSUM_NAME = re.compile(r"(sha\d*sums?\b|\.sha\d+$|\.sig$|\.asc$|checksums?)", re.I)


def classify_asset(name: str) -> tuple[str, str | None]:
    """(os, arch) for a release asset name, or ("checksum", None) / ("other", None).

    Built from every asset name in the 13 repos (1,408 assets, 91 name shapes, 2026-10-19).
    The architecture is taken only from the name; older names such as "iLEAPP.exe" state none,
    so they are "arch not stated" rather than a guess. "Ununtu" is a typo in one iLEAPP 2.0.0
    asset name and is read as Ubuntu. Probe .py files run on any OS and are "script".
    """
    n = name.lower()
    if CHECKSUM_NAME.search(n):
        return "checksum", None
    if n.endswith(".py"):
        return "script", None
    if re.search(r"windows|(^|[-_.])win(64|32)?([-_.]|$)|\.exe$|\.msi$", n):
        os_name = "windows"
    elif re.search(r"mac|darwin|apple_silicon|\.dmg$|\.pkg$", n):
        os_name = "macos"
    elif re.search(r"linux|ubuntu|ununtu|\.appimage$|\.deb$|\.rpm$", n):
        os_name = "linux"
    else:
        return "other", None
    if re.search(r"arm64|aarch64|apple_silicon|(^|[-_])arm([-_.]|$)", n):
        arch = "arm64"
    elif re.search(r"x86_64|x64|amd64|mac_intel|intel", n):
        arch = "x64"
    else:
        arch = "arch not stated"
    return os_name, arch


def summarise_releases(releases: list[dict]) -> dict:
    """Cumulative downloads by OS, by OS and arch, and per release, checksum files excluded."""
    by_os: dict[str, int] = {}
    by_os_arch: dict[str, int] = {}
    per_release = []
    excluded = 0
    for release in releases or []:
        if release.get("draft"):
            continue
        total = 0
        for asset in release.get("assets", []) or []:
            count = int(asset.get("download_count") or 0)
            os_name, arch = classify_asset(asset.get("name", ""))
            if os_name == "checksum":
                excluded += count
                continue
            total += count
            by_os[os_name] = by_os.get(os_name, 0) + count
            key = os_name if arch is None else f"{os_name}/{arch}"
            by_os_arch[key] = by_os_arch.get(key, 0) + count
        per_release.append({"tag": release.get("tag_name"), "published_at": release.get("published_at"),
                            "prerelease": bool(release.get("prerelease")), "downloads": total})
    return {"by_os": dict(sorted(by_os.items())), "by_os_arch": dict(sorted(by_os_arch.items())),
            "releases": per_release, "checksum_downloads_excluded": excluded}


def star_series(stargazers: list[dict]) -> list[list]:
    """[[YYYY-MM-DD, cumulative stars], ...] with one point per day on which the count changed.

    Built from each current stargazer's starred_at, so stars that were later removed are not
    in it: it is the history of today's stars, not of every star ever given.
    """
    days: dict[str, int] = {}
    for entry in stargazers or []:
        stamp = str(entry.get("starred_at") or "")[:10]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", stamp):
            days[stamp] = days.get(stamp, 0) + 1
    series, running = [], 0
    for day in sorted(days):
        running += days[day]
        series.append([day, running])
    return series


def seen_counts(snapshots: dict[str, list], field: str, last_n: int = 30) -> dict[str, int]:
    """How many of the last N daily snapshots each referrer (or path) appeared in."""
    recent = sorted(snapshots)[-last_n:]
    seen: dict[str, int] = {}
    for day in recent:
        for item in snapshots[day] or []:
            name = item.get(field)
            if name:
                seen[name] = seen.get(name, 0) + 1
    return seen


def is_stale(last_success: str | None, now: datetime, days: int = STALE_DAYS) -> bool:
    if not last_success:
        return True
    try:
        when = datetime.fromisoformat(last_success.replace("Z", "+00:00"))
    except ValueError:
        return True
    return now - when > timedelta(days=days)


# --------------------------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------------------------

class ApiResult:
    def __init__(self, status: str, data=None, http: int | None = None, link: str = ""):
        self.status, self.data, self.http, self.link = status, data, http, link


def api_get(path: str, token: str | None, accept: str = "application/vnd.github+json") -> ApiResult:
    url = path if path.startswith("http") else API + path
    headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "leapps-stats"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
                body = resp.read()
                if resp.status == 202:
                    return ApiResult("computing", None, 202)
                return ApiResult("ok", json.loads(body) if body else None, resp.status,
                                 resp.headers.get("Link", "") or "")
        except urllib.error.HTTPError as err:
            if err.code in (500, 502, 503, 504) and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            status = {401: "forbidden", 403: "forbidden", 404: "not_found"}.get(err.code, "error")
            return ApiResult(status, None, err.code)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            return ApiResult("error")
    return ApiResult("error")


def api_get_all(path: str, token: str | None, accept: str = "application/vnd.github+json") -> ApiResult:
    """Follow Link: rel="next" and concatenate list pages."""
    items, url = [], path
    while url:
        result = api_get(url, token, accept)
        if result.status != "ok":
            return result
        items.extend(result.data or [])
        match = re.search(r'<([^>]+)>;\s*rel="next"', result.link)
        url = match.group(1) if match else None
    return ApiResult("ok", items, 200)


# --------------------------------------------------------------------------------------------
# File I/O
# --------------------------------------------------------------------------------------------

def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=1, sort_keys=False, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")


def empty_month(month: str) -> dict:
    return {"schema_version": SCHEMA_VERSION, "month": month, "repos": {}}


def month_repo(month_data: dict, key: str) -> dict:
    return month_data["repos"].setdefault(key, {
        "views_daily": {}, "clones_daily": {}, "views_weekly": {}, "clones_weekly": {},
        "referrers": {}, "paths": {},
    })


# --------------------------------------------------------------------------------------------
# Collection
# --------------------------------------------------------------------------------------------

def collect_traffic(key: str, repo: str, token: str | None, today: str, months: dict, entry: dict,
                    now_iso: str, log=print) -> None:
    """Fetch the four traffic endpoints for one repo and merge them into the month files."""
    statuses = entry.setdefault("status", {})
    if not token:
        for kind in TRAFFIC_KINDS:
            statuses[kind] = "not_configured"
        return

    def month_file(month: str) -> dict:
        if month not in months:
            months[month] = read_json(TRAFFIC_DIR / f"{month}.json", empty_month(month))
        return months[month]

    window = entry.setdefault("window", {})
    for kind in ("views", "clones"):
        daily = api_get(f"/repos/{repo}/traffic/{kind}?per=day", token)
        weekly = api_get(f"/repos/{repo}/traffic/{kind}?per=week", token)
        statuses[kind] = daily.status
        if daily.status != "ok":
            log(f"warn: {repo} {kind}: {daily.status} ({daily.http})")
            continue
        window[kind] = {"count": daily.data.get("count"), "uniques": daily.data.get("uniques"),
                        "as_of": today}
        for granularity, result in (("daily", daily), ("weekly", weekly)):
            if result.status != "ok":
                continue
            fresh = points_by_day(result.data.get(kind, []))
            for month, points in split_by_month(fresh).items():
                bucket = month_repo(month_file(month), key)
                field = f"{kind}_{granularity}"
                bucket[field] = upsert_points(bucket[field], points, f"{repo} {field}", log)
    for kind, field in (("referrers", "referrer"), ("paths", "path")):
        result = api_get(f"/repos/{repo}/traffic/popular/{kind}", token)
        statuses[kind] = result.status
        if result.status != "ok":
            log(f"warn: {repo} {kind}: {result.status} ({result.http})")
            continue
        keep = ("referrer", "count", "uniques") if field == "referrer" else ("path", "title", "count", "uniques")
        items = [{k: item.get(k) for k in keep} for item in (result.data or [])]
        month_repo(month_file(month_of(today)), key)[kind][today] = items
    if all(statuses.get(kind) == "ok" for kind in TRAFFIC_KINDS):
        entry["last_success"] = now_iso


def collect(now: datetime | None = None, log=print, sleep=time.sleep) -> int:
    now = now or datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    public_token = os.environ.get("GH_TOKEN") or None
    lists = load_repo_lists()

    index = read_json(INDEX_PATH, {"schema_version": SCHEMA_VERSION, "repos": {}, "months": []})
    assets = read_json(ASSETS_PATH, {"schema_version": SCHEMA_VERSION, "platform_daily": {}, "repos": {}})
    community = read_json(COMMUNITY_PATH, {"schema_version": SCHEMA_VERSION, "stars": {}, "commit_activity": {}})
    months: dict[str, dict] = {}
    pending_activity = []

    for group, repos in lists.items():
        for key, repo in repos.items():
            owner = repo.split("/", 1)[0]
            owner_token = os.environ.get(OWNER_TOKEN_ENV.get(owner, ""), "") or None
            read_token = owner_token or public_token

            entry = index["repos"].setdefault(key, {})
            entry.update({"repo": repo, "group": group})
            collect_traffic(key, repo, owner_token, today, months, entry, now_iso, log)

            releases = api_get_all(f"/repos/{repo}/releases?per_page=100", read_token)
            repo_assets = assets["repos"].setdefault(key, {})
            repo_assets.update({"repo": repo, "group": group, "status": releases.status})
            if releases.status == "ok":
                summary = summarise_releases(releases.data)
                repo_assets.update(summary)
                assets["platform_daily"].setdefault(today, {})[key] = summary["by_os"]
            else:
                log(f"warn: {repo} releases: {releases.status} ({releases.http})")

            stars = api_get_all(f"/repos/{repo}/stargazers?per_page=100", read_token,
                                accept="application/vnd.github.star+json")
            if stars.status == "ok":
                community["stars"][key] = {"repo": repo, "group": group, "status": "ok",
                                           "series": star_series(stars.data), "as_of": today}
            else:
                previous = community["stars"].get(key, {})
                community["stars"][key] = {**previous, "repo": repo, "group": group, "status": stars.status}
                log(f"warn: {repo} stargazers: {stars.status} ({stars.http})")

            pending_activity.append((key, repo, group, read_token))

    # GitHub answers 202 while it computes commit statistics, and starts computing on that
    # first request. One delayed retry inside the run usually gets the result; otherwise the
    # last weeks we had are kept with status "computing".
    for attempt in range(2):
        retry = []
        for key, repo, group, read_token in pending_activity:
            activity = api_get(f"/repos/{repo}/stats/commit_activity", read_token)
            previous = community["commit_activity"].get(key, {})
            if activity.status == "ok" and isinstance(activity.data, list):
                weeks = [[datetime.fromtimestamp(w["week"], timezone.utc).strftime("%Y-%m-%d"), w["total"]]
                         for w in activity.data if "week" in w and "total" in w]
                community["commit_activity"][key] = {"repo": repo, "group": group, "status": "ok",
                                                     "weeks": weeks, "as_of": today}
                continue
            community["commit_activity"][key] = {**previous, "repo": repo, "group": group,
                                                 "status": activity.status}
            if activity.status == "computing":
                retry.append((key, repo, group, read_token))
        pending_activity = retry
        if not pending_activity or attempt == 1:
            break
        sleep(ACTIVITY_RETRY_SECONDS)

    for month, data in months.items():
        write_json(TRAFFIC_DIR / f"{month}.json", data)
    index["months"] = sorted({p.stem for p in TRAFFIC_DIR.glob("????-??.json")} | set(months))
    index["updated_at"] = now_iso
    index["schema_version"] = SCHEMA_VERSION
    assets["updated_at"] = now_iso
    community["updated_at"] = now_iso
    write_json(INDEX_PATH, index)
    write_json(ASSETS_PATH, assets)
    write_json(COMMUNITY_PATH, community)

    configured = sorted(owner for owner, env in OWNER_TOKEN_ENV.items() if os.environ.get(env))
    log(f"collected {sum(len(r) for r in lists.values())} repos at {now_iso}; "
        f"traffic credentials for: {', '.join(configured) or 'none'}")
    return 0


def check_stale(now: datetime | None = None, log=print) -> int:
    """Exit 1 when traffic is configured for an owner and one of its repos has gone stale."""
    now = now or datetime.now(timezone.utc)
    index = read_json(INDEX_PATH, {"repos": {}})
    stale = []
    for key, entry in sorted(index.get("repos", {}).items()):
        owner = str(entry.get("repo", "")).split("/", 1)[0]
        if not os.environ.get(OWNER_TOKEN_ENV.get(owner, ""), ""):
            continue
        if is_stale(entry.get("last_success"), now):
            stale.append(f"{entry.get('repo')} (last success {entry.get('last_success') or 'never'}, "
                         f"status {entry.get('status')})")
    for line in stale:
        log(f"stale: {line}")
    return 1 if stale else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--check-stale", action="store_true",
                        help=f"exit 1 if a configured repo had no successful traffic run in {STALE_DAYS} days")
    args = parser.parse_args(argv)
    return check_stale() if args.check_stale else collect()


if __name__ == "__main__":
    sys.exit(main())
