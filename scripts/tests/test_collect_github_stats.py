"""Tests for scripts/collect_github_stats.py. Run: python3 -m unittest discover -s scripts/tests"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import collect_github_stats as cgs  # noqa: E402


def window(start_day, days, count=10, uniques=4):
    """A GitHub-shaped list of daily points starting on 2026-10-<start_day>."""
    return [{"timestamp": f"2026-10-{start_day + i:02d}T00:00:00Z", "count": count + i, "uniques": uniques}
            for i in range(days)]


class MergeRules(unittest.TestCase):
    def test_overlapping_windows_are_upserted_not_summed(self):
        first = cgs.points_by_day(window(1, 14))
        second = cgs.points_by_day(window(2, 14))
        quiet = lambda *_: None  # noqa: E731
        merged = cgs.upsert_points(cgs.upsert_points({}, first, log=quiet), second, log=quiet)
        self.assertEqual(len(merged), 15)  # 1..15, each day once
        self.assertEqual(merged["2026-10-02"], {"count": 10, "uniques": 4})  # second run's value
        self.assertEqual(sum(v["count"] for v in merged.values()),
                         sum(p["count"] for p in window(2, 14)) + 10)

    def test_duplicate_run_changes_nothing(self):
        fresh = cgs.points_by_day(window(5, 14))
        once = cgs.upsert_points({}, fresh)
        self.assertEqual(cgs.upsert_points(once, fresh), once)

    def test_a_drop_is_kept_and_logged(self):
        logged = []
        stored = {"2026-10-05": {"count": 50, "uniques": 9}}
        merged = cgs.upsert_points(stored, {"2026-10-05": {"count": 40, "uniques": 8}}, "r views", logged.append)
        self.assertEqual(merged["2026-10-05"]["count"], 40)
        self.assertEqual(len(logged), 1)
        self.assertIn("fell from 50 to 40", logged[0])

    def test_days_outside_the_window_are_left_alone(self):
        stored = {"2026-09-01": {"count": 3, "uniques": 1}}
        merged = cgs.upsert_points(stored, cgs.points_by_day(window(5, 14)))
        self.assertEqual(merged["2026-09-01"], {"count": 3, "uniques": 1})

    def test_points_split_into_their_own_months(self):
        points = {"2026-09-30": {"count": 1}, "2026-10-01": {"count": 2}}
        self.assertEqual(sorted(cgs.split_by_month(points)), ["2026-09", "2026-10"])

    def test_bad_timestamps_are_ignored(self):
        self.assertEqual(cgs.points_by_day([{"timestamp": "nope", "count": 1}, {"count": 2}]), {})


class Assets(unittest.TestCase):
    CASES = {
        "iLEAPP-2026.4.4-windows-x64-portable.zip": ("windows", "x64"),
        "iLEAPP-2026.4.4-windows-arm64-setup.exe": ("windows", "arm64"),
        "iLEAPP-2026.4.4-macos-arm64.dmg": ("macos", "arm64"),
        "ileappGUI-v2.1-macos_mac_intel.dmg": ("macos", "x64"),
        "ileappGUI-v2.1-macos_apple_silicon.dmg": ("macos", "arm64"),
        "aleapp-v3.2-linux_x86_64.AppImage": ("linux", "x64"),
        "iLEAPP-2026.4.4-linux-arm64.AppImage": ("linux", "arm64"),
        "ileappGUI.exe": ("windows", "arch not stated"),
        "ileappGUI-v1.18-ubuntu.zip": ("linux", "arch not stated"),
        "iLEAPP-2.0.0-Ununtu.zip": ("linux", "arch not stated"),
        "SHA256SUMS.txt": ("checksum", None),
        "ewfprobe.py": ("script", None),
        "Parsed_MVS2026-iPhone14_iLEAPP-2.3.1.zip": ("other", None),
    }

    def test_classifier(self):
        for name, expected in self.CASES.items():
            with self.subTest(name=name):
                self.assertEqual(cgs.classify_asset(name), expected)

    def test_summary_excludes_checksums_and_drafts(self):
        releases = [
            {"tag_name": "v2", "published_at": "2026-10-01T00:00:00Z", "assets": [
                {"name": "x-windows-x64.zip", "download_count": 10},
                {"name": "x-macos-arm64.dmg", "download_count": 5},
                {"name": "SHA256SUMS.txt", "download_count": 3}]},
            {"tag_name": "v3-draft", "draft": True, "assets": [{"name": "x-windows-x64.zip", "download_count": 99}]},
        ]
        summary = cgs.summarise_releases(releases)
        self.assertEqual(summary["by_os"], {"macos": 5, "windows": 10})
        self.assertEqual(summary["by_os_arch"], {"macos/arm64": 5, "windows/x64": 10})
        self.assertEqual(summary["checksum_downloads_excluded"], 3)
        self.assertEqual([r["tag"] for r in summary["releases"]], ["v2"])
        self.assertEqual(summary["releases"][0]["downloads"], 15)


class Community(unittest.TestCase):
    SAVED = {"repo": "a/b", "group": "tool", "status": "forbidden", "series": [["2026-01-01", 1], ["2026-10-19", 9]]}

    def test_star_count_is_added_and_saved_history_kept(self):
        ok = cgs.ApiResult("ok", {"stargazers_count": 10}, 200)
        entry = cgs.record_star_count(self.SAVED, "a/b", "tool", "2026-10-20", ok)
        self.assertEqual(entry["series"], self.SAVED["series"])
        self.assertEqual(entry["daily"], {"2026-10-20": 10})
        self.assertEqual(entry["status"], "ok")

    def test_same_day_rerun_replaces_the_count(self):
        first = cgs.record_star_count(self.SAVED, "a/b", "tool", "2026-10-20",
                                      cgs.ApiResult("ok", {"stargazers_count": 10}, 200))
        again = cgs.record_star_count(first, "a/b", "tool", "2026-10-20",
                                      cgs.ApiResult("ok", {"stargazers_count": 11}, 200))
        self.assertEqual(again["daily"], {"2026-10-20": 11})

    def test_a_failed_read_keeps_everything_and_records_the_status(self):
        first = cgs.record_star_count(self.SAVED, "a/b", "tool", "2026-10-20",
                                      cgs.ApiResult("ok", {"stargazers_count": 10}, 200))
        failed = cgs.record_star_count(first, "a/b", "tool", "2026-10-21", cgs.ApiResult("forbidden", None, 403))
        self.assertEqual(failed["daily"], {"2026-10-20": 10})
        self.assertEqual(failed["series"], self.SAVED["series"])
        self.assertEqual(failed["status"], "forbidden")

    def test_seen_counts_cover_the_last_n_snapshots(self):
        snaps = {f"2026-10-{d:02d}": [{"referrer": "a"}] + ([{"referrer": "b"}] if d > 8 else [])
                 for d in range(1, 11)}
        self.assertEqual(cgs.seen_counts(snaps, "referrer", last_n=5), {"a": 5, "b": 2})

    def test_staleness(self):
        now = datetime(2026, 10, 20, 5, tzinfo=timezone.utc)
        self.assertFalse(cgs.is_stale("2026-10-18T05:00:00Z", now))
        self.assertTrue(cgs.is_stale("2026-10-16T04:00:00Z", now))
        self.assertTrue(cgs.is_stale(None, now))


class RepoList(unittest.TestCase):
    def test_lists_come_from_the_download_workflow(self):
        lists = cgs.load_repo_lists()
        self.assertEqual(len(lists["tool"]), 8)
        self.assertEqual(len(lists["probe"]), 5)
        self.assertEqual(lists["tool"]["lava"], "leapps-org/LAVA-releases")
        self.assertNotIn("leapps-org/LAVA-beta", lists["tool"].values())


class FakeApi:
    """Serves canned responses by path prefix; anything unknown is a 404."""

    def __init__(self, routes):
        self.routes = routes

    def __call__(self, path, token, accept="application/vnd.github+json"):
        if path in self.routes:
            result = self.routes[path]
            return result(token) if callable(result) else result
        for prefix, result in self.routes.items():
            if path.startswith(prefix):
                return result(token) if callable(result) else result
        return cgs.ApiResult("not_found", None, 404)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.patches = [mock.patch.object(cgs, name, self.tmp / rel) for name, rel in (
            ("DATA", "data"), ("TRAFFIC_DIR", "data/traffic"), ("INDEX_PATH", "data/traffic/index.json"),
            ("ASSETS_PATH", "data/assets.json"), ("COMMUNITY_PATH", "data/community.json"))]
        self.patches.append(mock.patch.object(cgs, "load_repo_lists",
                                              return_value={"tool": {"t": "abrignoni/T"}, "probe": {}}))
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def run_collect(self, routes, env, day=20):
        api = FakeApi(routes)
        with mock.patch.object(cgs, "api_get", api), mock.patch.object(cgs, "api_get_all", api), \
                mock.patch.dict("os.environ", env, clear=True):
            cgs.collect(now=datetime(2026, 10, day, 5, tzinfo=timezone.utc), log=lambda *_: None,
                        sleep=lambda *_: None)

    def traffic_routes(self, start):
        ok = lambda data: cgs.ApiResult("ok", data, 200)  # noqa: E731
        return {
            "/repos/abrignoni/T/traffic/views?per=day": ok({"count": 99, "uniques": 7, "views": window(start, 14)}),
            "/repos/abrignoni/T/traffic/views?per=week": ok({"views": [{"timestamp": "2026-10-05T00:00:00Z", "count": 70, "uniques": 6}]}),
            "/repos/abrignoni/T/traffic/clones?per=day": ok({"count": 5, "uniques": 2, "clones": window(start, 14, 1, 1)}),
            "/repos/abrignoni/T/traffic/clones?per=week": ok({"clones": []}),
            "/repos/abrignoni/T/traffic/popular/referrers": ok([]),
            "/repos/abrignoni/T/traffic/popular/paths": ok([{"path": "/abrignoni/T", "title": "T", "count": 3, "uniques": 2}]),
            "/repos/abrignoni/T/releases": ok([{"tag_name": "v1", "assets": [{"name": "t-windows-x64.zip", "download_count": 4}]}]),
            "/repos/abrignoni/T": ok({"stargazers_count": 1}),
            "/repos/abrignoni/T/stats/commit_activity": cgs.ApiResult("computing", None, 202),
        }

    def read(self, rel):
        return json.loads((self.tmp / rel).read_text())

    def test_two_runs_with_overlapping_windows(self):
        self.run_collect(self.traffic_routes(1), {"GH_TOKEN_ABRIGNONI": "x"}, day=16)
        self.run_collect(self.traffic_routes(2), {"GH_TOKEN_ABRIGNONI": "x"}, day=17)
        month = self.read("data/traffic/2026-10.json")["repos"]["t"]
        self.assertEqual(len(month["views_daily"]), 15)
        self.assertEqual(month["referrers"], {"2026-10-16": [], "2026-10-17": []})  # empty list, not missing
        index = self.read("data/traffic/index.json")
        self.assertEqual(index["repos"]["t"]["status"], {k: "ok" for k in cgs.TRAFFIC_KINDS})
        self.assertEqual(index["repos"]["t"]["window"]["views"]["uniques"], 7)
        self.assertEqual(index["months"], ["2026-10"])
        self.assertEqual(self.read("data/community.json")["commit_activity"]["t"]["status"], "computing")
        self.assertEqual(self.read("data/assets.json")["repos"]["t"]["by_os"], {"windows": 4})

    def test_same_day_rerun_only_moves_timestamps(self):
        self.run_collect(self.traffic_routes(1), {"GH_TOKEN_ABRIGNONI": "x"})
        before = self.read("data/traffic/2026-10.json")
        self.run_collect(self.traffic_routes(1), {"GH_TOKEN_ABRIGNONI": "x"})
        self.assertEqual(self.read("data/traffic/2026-10.json"), before)

    def test_forbidden_is_a_status_not_a_zero(self):
        routes = self.traffic_routes(1)
        for kind in ("views?per=day", "views?per=week", "clones?per=day", "clones?per=week",
                     "popular/referrers", "popular/paths"):
            routes[f"/repos/abrignoni/T/traffic/{kind}"] = cgs.ApiResult("forbidden", None, 403)
        self.run_collect(routes, {"GH_TOKEN_ABRIGNONI": "x"})
        entry = self.read("data/traffic/index.json")["repos"]["t"]
        self.assertEqual(set(entry["status"].values()), {"forbidden"})
        self.assertNotIn("last_success", entry)
        self.assertFalse((self.tmp / "data/traffic/2026-10.json").exists())

    def test_no_app_token_means_not_configured_and_other_stats_still_collected(self):
        self.run_collect(self.traffic_routes(1), {"GH_TOKEN": "public"})
        entry = self.read("data/traffic/index.json")["repos"]["t"]
        self.assertEqual(set(entry["status"].values()), {"not_configured"})
        self.assertEqual(self.read("data/community.json")["stars"]["t"]["daily"], {"2026-10-20": 1})
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(cgs.check_stale(now=datetime(2026, 10, 25, tzinfo=timezone.utc), log=lambda *_: None), 0)

    def test_check_stale_fails_when_configured_and_old(self):
        self.run_collect(self.traffic_routes(1), {"GH_TOKEN_ABRIGNONI": "x"}, day=10)
        with mock.patch.dict("os.environ", {"GH_TOKEN_ABRIGNONI": "x"}, clear=True):
            self.assertEqual(cgs.check_stale(now=datetime(2026, 10, 11, tzinfo=timezone.utc), log=lambda *_: None), 0)
            self.assertEqual(cgs.check_stale(now=datetime(2026, 10, 20, tzinfo=timezone.utc), log=lambda *_: None), 1)


if __name__ == "__main__":
    unittest.main()
