"""Behavior checks for public GitHub acquisition and its durable snapshot."""

from datetime import date, datetime, timedelta, timezone
import copy
import io
import json
from pathlib import Path
import ssl
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from scripts import github_stats


class CalendarTests(unittest.TestCase):
    def parse(self, html, start, end):
        self.assertTrue(
            hasattr(github_stats, "_parse_calendar_html"),
            "The public contribution calendar parser is not implemented",
        )
        return github_stats._parse_calendar_html(html, start, end)

    def test_tooltips_supply_actual_counts_and_dates_are_sorted(self):
        # Inferring a count from the color level would lose 1,234 contributions.
        html = '''
        <td id="new" data-date="2026-01-01" data-level="4"></td>
        <tool-tip for="new">1,234 contributions on January 1st.</tool-tip>
        <td id="old" data-date="2025-12-31" data-level="0"></td>
        <tool-tip for="old"><span>No contributions</span> on December 31st.</tool-tip>
        '''
        self.assertEqual(
            self.parse(html, date(2025, 12, 31), date(2026, 1, 1)),
            [
                {"date": "2025-12-31", "count": 0, "level": 0},
                {"date": "2026-01-01", "count": 1234, "level": 4},
            ],
        )

    def test_legacy_data_count_preserves_zero(self):
        html = '<rect data-date="2024-02-29" data-count="0" data-level="0" />'
        self.assertEqual(
            self.parse(html, date(2024, 2, 29), date(2024, 2, 29)),
            [{"date": "2024-02-29", "count": 0, "level": 0}],
        )

    def test_a_missing_date_is_unavailable_rather_than_zero(self):
        html = '<rect data-date="2024-02-28" data-count="7" data-level="2" />'
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.parse(html, date(2024, 2, 28), date(2024, 3, 1))

    def test_a_level_without_a_count_cannot_become_a_metric(self):
        html = '<td id="unknown" data-date="2026-01-01" data-level="0"></td>'
        with self.assertRaisesRegex(ValueError, "count"):
            self.parse(html, date(2026, 1, 1), date(2026, 1, 1))

    def test_conflicting_duplicate_dates_are_rejected(self):
        html = '''
        <rect data-date="2026-01-01" data-count="1" data-level="1" />
        <rect data-date="2026-01-01" data-count="8" data-level="4" />
        '''
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.parse(html, date(2026, 1, 1), date(2026, 1, 1))

    def test_rolling_calendar_year_keeps_leap_day(self):
        self.assertTrue(hasattr(github_stats, "_calendar_window"))
        self.assertEqual(
            github_stats._calendar_window(date(2024, 2, 29)),
            (date(2023, 3, 1), date(2024, 2, 29)),
        )
        self.assertEqual(
            github_stats._calendar_window(date(2025, 2, 28)),
            (date(2024, 2, 29), date(2025, 2, 28)),
        )


def snapshot():
    return {
        "schema_version": 2,
        "login": "Fiudeus",
        "fetched_at": "2026-11-14T09:30:00Z",
        "source": "github-rest-public",
        "created_at": "2022-04-07T12:00:00Z",
        "repos": 10,
        "stars": 1,
        "followers": 1,
        "following": 2,
        "commits": None,
        "prs": 1,
        "issues": 0,
        "contributions": None,
        "period_start": "2025-11-15",
        "period_end": "2026-11-14",
        "languages": [{"name": "Python", "bytes": 100}],
        "language_repositories": [{"name": "project-a", "languages": [{"name": "Python", "bytes": 100}]}],
        "days": None,
        "calendar_source": "unavailable: public calendar could not be verified",
        "last_public_activity": None,
        "activity_source": "unavailable: no valid public events",
    }


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "github.json"

    def save(self, data):
        self.assertTrue(hasattr(github_stats, "save_snapshot"), "Snapshot saving is not implemented")
        return github_stats.save_snapshot(self.path, data)

    def load(self, login="Fiudeus"):
        self.assertTrue(hasattr(github_stats, "load_snapshot"), "Snapshot loading is not implemented")
        return github_stats.load_snapshot(self.path, login)

    def test_roundtrip_preserves_genuine_zero_and_unavailable_metrics(self):
        data = snapshot()
        data.update(stars=0, followers=None, languages=None, language_repositories=None)
        self.save(data)
        self.assertEqual(self.load("fiudeus"), data)
        self.assertTrue(self.path.read_bytes().endswith(b"\n"))

    def test_snapshot_for_another_login_is_rejected(self):
        self.path.write_text(json.dumps(snapshot()), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "login"):
            self.load("someone-else")

    def test_invalid_metrics_or_unexpected_raw_fields_are_never_saved(self):
        for changes in [
            {"stars": -1},
            {"followers": True},
            {"languages": [{"name": "Python", "bytes": -2}]},
            {"languages": [{"name": "Python", "bytes": 1}, {"name": "Python", "bytes": 2}]},
            {"schema_version": True},
            {"schema_version": 1},
            {"fetched_at": "2026-11-14T09:30:00"},
            {"created_at": "2022-04-07"},
            {"following": -1},
            {"commits": True},
            {"period_start": "2025-11-16"},
            {"email": "not-a-snapshot-field@example.invalid"},
        ]:
            with self.subTest(changes=changes):
                data = snapshot()
                data.update(changes)
                with self.assertRaises(ValueError):
                    self.save(data)
                self.assertFalse(self.path.exists())

    def test_incomplete_calendar_in_a_cache_is_rejected(self):
        data = snapshot()
        data.update(
            days=[{"date": "2026-11-14", "count": 0, "level": 0}],
            calendar_source="github-public-contributions-html",
        )
        self.path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.load()

    def test_failed_atomic_replacement_preserves_the_previous_snapshot(self):
        data = snapshot()
        self.save(data)
        before = self.path.read_bytes()
        changed = copy.deepcopy(data)
        changed["stars"] = 2
        with patch("scripts.github_stats.os.replace", side_effect=OSError("disk busy")):
            with self.assertRaises(OSError):
                self.save(changed)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual([file.name for file in self.path.parent.iterdir()], ["github.json"])

    def test_broken_json_does_not_masquerade_as_an_empty_snapshot(self):
        self.path.write_text('{"repos":', encoding="utf-8")
        with self.assertRaises(ValueError):
            self.load()

    def test_repository_language_provenance_must_sum_to_the_aggregate(self):
        data = snapshot()
        data["language_repositories"] = [
            {"name": "project-a", "languages": [{"name": "Python", "bytes": 60}]},
            {"name": "project-b", "languages": [{"name": "Python", "bytes": 40}]},
        ]
        self.save(data)
        self.assertEqual(self.load(), data)
        data["language_repositories"][0]["languages"][0]["bytes"] = 61
        with self.assertRaisesRegex(ValueError, "sum|aggregate"):
            self.save(data)

    def test_provenance_rejects_duplicate_excluded_or_malformed_repositories(self):
        cases = [
            None,
            [],
            [{"name": "project-a", "languages": [{"name": "Python", "bytes": -1}]}],
            [{"name": "project-a", "languages": [{"name": "Python", "bytes": True}]}],
            [{"name": "project-a", "languages": [{"name": "Python", "bytes": "100"}]}],
            [{"name": "project-a", "languages": [{"name": "Python", "bytes": 100}], "private": False}],
            [{"name": "project-a", "languages": [{"name": "Python", "bytes": 50}, {"name": "PYTHON", "bytes": 50}]}],
            [{"name": "Project-a", "languages": [{"name": "Python", "bytes": 50}]}, {"name": "project-A", "languages": [{"name": "Python", "bytes": 50}]}],
            [{"name": "fIuDeUs", "languages": [{"name": "Python", "bytes": 100}]}],
            [{"name": "lUmInArEaD", "languages": [{"name": "Python", "bytes": 100}]}],
            [{"name": "other/private-repo", "languages": [{"name": "Python", "bytes": 100}]}],
        ]
        for repositories in cases:
            with self.subTest(repositories=repositories):
                data = snapshot()
                data["language_repositories"] = repositories
                with self.assertRaises(ValueError):
                    self.save(data)

    def test_activity_timestamp_requires_valid_source_and_fetch_time_bounds(self):
        data = snapshot()
        data.update(last_public_activity="2026-11-14T09:00:00Z", activity_source="github-public-events")
        self.save(data)
        self.assertEqual(self.load()["last_public_activity"], "2026-11-14T09:00:00Z")
        for stamp, source in [
            (None, "github-public-events"),
            ("2026-11-14T09:00:00Z", "unavailable: request failed"),
            ("2026-11-14T09:31:00Z", "github-public-events"),
            ("2020-01-01T00:00:00Z", "github-public-events"),
            ("2026-11-14T09:00:00", "github-public-events"),
        ]:
            with self.subTest(stamp=stamp, source=source):
                data.update(last_public_activity=stamp, activity_source=source)
                with self.assertRaises(ValueError):
                    self.save(data)


class Response(io.BytesIO):
    def __init__(self, data, headers=None):
        raw = data.encode() if isinstance(data, str) else json.dumps(data).encode()
        super().__init__(raw)
        self.headers = headers or {}


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 11, 14, 12, 30, tzinfo=timezone.utc)
        return fixed.astimezone(tz) if tz is not None else fixed.replace(tzinfo=None)


def public_event(kind, stamp, actor="Fiudeus", public=True):
    return {"type": kind, "created_at": stamp, "actor": {"login": actor}, "public": public}


def repository(name, stars=0, fork=False, private=False, owner="Fiudeus"):
    return {
        "name": name,
        "full_name": f"{owner}/{name}",
        "owner": {"login": owner},
        "private": private,
        "fork": fork,
        "stargazers_count": stars,
        "languages_url": f"https://api.github.com/repos/{owner}/{name}/languages",
    }


def calendar_html(start, end, counts):
    cells = []
    while start <= end:
        count = counts.get(start.isoformat(), 0)
        cells.append(
            f'<td id="d-{start}" data-date="{start}" data-level="{1 if count else 0}"></td>'
            f'<tool-tip for="d-{start}">{count} contributions on the date.</tool-tip>'
        )
        start += timedelta(days=1)
    return "".join(cells)


class PublicAPI:
    """A strict network boundary with public REST and observed contribution HTML."""

    def __init__(self):
        self.pages = {
            1: [repository("Fiudeus", 2), repository("own-a", 3), repository("fork", 20, fork=True)],
            2: [repository("LuminaRead", 50), repository("own-b", 4)],
        }
        self.languages = {"own-a": {"Python": 100}, "own-b": {"C": 200, "Python": 10}}
        self.counts = {"2025-11-15": 3, "2026-01-01": 1}
        self.graphql = None
        self.incomplete_search = False
        self.events = [public_event("WatchEvent", "2026-11-14T11:22:00Z")]
        self.break_public_calendar = False
        self.requests = []

    def __call__(self, request, timeout, *, context=None):
        self.requests.append(request)
        if not 0 < timeout <= 15:
            raise AssertionError("Every network request needs a short finite timeout")
        url = urlsplit(request.full_url)
        query = parse_qs(url.query)
        if url.netloc == "github.com":
            if request.get_header("Authorization"):
                raise AssertionError("Tokenless public verification must not send credentials")
            if self.break_public_calendar:
                return Response("<html>The calendar structure changed.</html>")
            year = int(query["from"][0][:4])
            return Response(calendar_html(date(year, 1, 1), date(year, 12, 31), self.counts))
        if url.netloc != "api.github.com":
            raise AssertionError("Unexpected network destination")
        if url.path == "/users/Fiudeus":
            total = sum(not repo["private"] for page in self.pages.values() for repo in page)
            return Response({
                "login": "Fiudeus", "public_repos": total, "followers": 1,
                "following": 2, "created_at": "2022-04-07T12:00:00Z",
            })
        if url.path == "/users/Fiudeus/repos":
            if query.get("type") != ["owner"] or query.get("per_page") != ["100"]:
                raise AssertionError("Only owned public repositories with explicit pagination are expected")
            page = int(query["page"][0])
            headers = {}
            if page < len(self.pages):
                headers["Link"] = f'<https://api.github.com/users/Fiudeus/repos?page={page + 1}>; rel="next"'
            return Response(self.pages.get(page, []), headers)
        if url.path.endswith("/languages"):
            name = url.path.split("/")[-2]
            if name not in self.languages:
                raise AssertionError(f"Language bytes from excluded or forked repo {name} were requested")
            return Response(self.languages[name])
        if url.path == "/search/issues":
            search = query.get("q", [""])[0]
            if not all(term in search for term in (
                "author:Fiudeus", "is:public", "created:2025-11-15..2026-11-14"
            )):
                raise AssertionError("PRs/issues must use the same public rolling-year scope")
            return Response({
                "total_count": 1 if "is:pr" in search else 0,
                "incomplete_results": self.incomplete_search, "items": [],
            })
        if url.path == "/users/Fiudeus/events/public":
            if request.get_header("Authorization"):
                raise AssertionError("The public activity feed must always be tokenless")
            return Response(self.events)
        if url.path == "/graphql":
            if request.get_header("Authorization") != "Bearer secret-test-token":
                raise AssertionError("Authenticated GraphQL must use the configured token")
            payload = json.loads(request.data)
            if payload["variables"] != {
                "login": "Fiudeus", "from": "2025-11-15T00:00:00Z", "to": "2026-11-14T23:59:59Z"
            }:
                raise AssertionError("GraphQL must request the precise rolling year")
            if "totalCommitContributions" not in payload["query"]:
                raise AssertionError("GraphQL must request GitHub's exact typed commit contribution total")
            return Response(self.graphql)
        raise AssertionError(f"Unexpected public endpoint: {url.path}")

    def graphql_calendar(self, changed_count=None):
        start = date(2025, 11, 15)
        days = []
        while start <= date(2026, 11, 14):
            count = self.counts.get(start.isoformat(), 0)
            if start == date(2025, 11, 15) and changed_count is not None:
                count = changed_count
            days.append({
                "date": start.isoformat(), "contributionCount": count,
                "contributionLevel": "FIRST_QUARTILE" if count else "NONE",
            })
            start += timedelta(days=1)
        return {"data": {"user": {"contributionsCollection": {
            "totalCommitContributions": 23,
            "contributionCalendar": {"weeks": [{"contributionDays": days}]}
        }}}}


class FetchTests(unittest.TestCase):
    def run_fetch(self, api, token=None, clock=FixedDatetime):
        self.assertTrue(hasattr(github_stats, "fetch"), "Public GitHub acquisition is not implemented")
        with patch.dict("os.environ", {"GH_TOKEN": token or "", "GITHUB_TOKEN": ""}):
            with patch("scripts.github_stats.urlopen", api), patch("scripts.github_stats.datetime", clock):
                return github_stats.fetch("Fiudeus", ["fIuDeUs/lUmInArEaD"], today=date(2026, 11, 14))

    def test_pagination_and_exclusions_aggregate_only_owned_public_code(self):
        data = self.run_fetch(PublicAPI())
        self.assertEqual((data["repos"], data["stars"], data["followers"]), (5, 9, 1))
        self.assertEqual(data["languages"], [{"name": "C", "bytes": 200}, {"name": "Python", "bytes": 110}])
        self.assertEqual(data["schema_version"], 2)
        self.assertEqual(data["language_repositories"], [
            {"name": "own-a", "languages": [{"name": "Python", "bytes": 100}]},
            {"name": "own-b", "languages": [{"name": "C", "bytes": 200}, {"name": "Python", "bytes": 10}]},
        ])
        self.assertEqual(data["last_public_activity"], "2026-11-14T11:22:00Z")
        self.assertEqual(data["activity_source"], "github-public-events")
        self.assertEqual(len(data["days"]), 365)
        self.assertEqual(data["days"][0], {"date": "2025-11-15", "count": 3, "level": 1})
        self.assertEqual(data["days"][-1], {"date": "2026-11-14", "count": 0, "level": 0})
        self.assertEqual(data["calendar_source"], "github-public-contributions-html")
        self.assertEqual(data["source"], "github-rest-public")
        self.assertEqual(data["created_at"], "2022-04-07T12:00:00Z")
        self.assertEqual(data["following"], 2)
        self.assertEqual((data["prs"], data["issues"], data["commits"], data["contributions"]), (1, 0, None, 4))
        self.assertEqual((data["period_start"], data["period_end"]), ("2025-11-15", "2026-11-14"))

    def test_changed_html_is_unavailable_without_erasing_real_metadata(self):
        api = PublicAPI()
        api.break_public_calendar = True
        data = self.run_fetch(api)
        self.assertIsNone(data["days"])
        self.assertTrue(data["calendar_source"].startswith("unavailable:"))
        self.assertEqual(data["stars"], 9)
        self.assertIsNone(data["contributions"])

    def test_incomplete_search_counts_are_unavailable_instead_of_approximate(self):
        api = PublicAPI()
        api.incomplete_search = True
        data = self.run_fetch(api)
        self.assertIsNone(data["prs"])
        self.assertIsNone(data["issues"])

    def test_language_error_does_not_publish_a_partial_aggregate_as_zero(self):
        api = PublicAPI()

        def network(request, timeout, *, context=None):
            if request.full_url.endswith("/own-b/languages"):
                raise HTTPError(request.full_url, 403, "rate limited", {}, None)
            return api(request, timeout, context=context)

        with self.assertRaises(RuntimeError):
            self.run_fetch(network)

    def test_duplicate_repository_pages_do_not_double_count_stars(self):
        api = PublicAPI()
        api.pages[2] = [repository("own-a", 3), repository("own-b", 4)]
        with self.assertRaisesRegex(RuntimeError, "duplicate"):
            self.run_fetch(api)

    def test_repository_pagination_stops_at_a_finite_page_limit(self):
        api = PublicAPI()
        with patch("scripts.github_stats._MAX_PAGES", 1, create=True):
            with self.assertRaisesRegex(RuntimeError, "page"):
                self.run_fetch(api)
        paths = [urlsplit(request.full_url).path for request in api.requests]
        self.assertEqual(paths, ["/users/Fiudeus", "/users/Fiudeus/repos"])

    def test_a_full_final_page_is_complete_when_it_matches_the_public_count(self):
        api = PublicAPI()
        api.pages = {1: [repository(f"fork-{number}", fork=True) for number in range(100)]}
        with patch("scripts.github_stats._MAX_PAGES", 1):
            data = self.run_fetch(api)
        self.assertEqual((data["repos"], data["stars"], data["languages"]), (100, 0, []))

    def test_mixed_public_actions_choose_the_latest_valid_timestamp_not_the_first(self):
        api = PublicAPI()
        api.events = [
            public_event("PushEvent", "2026-11-14T12:01:00Z"),
            public_event("PullRequestEvent", "2026-11-14T12:02:00Z"),
            public_event("FuturePublicActionEvent", "2026-11-14T12:08:00Z", actor="fIuDeUs"),
            public_event("IssuesEvent", "2026-11-14T12:03:00Z"),
            public_event("PullRequestReviewEvent", "2026-11-14T12:04:00Z"),
            public_event("WatchEvent", "2026-11-14T12:05:00Z"),
            public_event("CreateEvent", "2026-11-14T12:06:00Z"),
            public_event("PushEvent", "2026-11-14T12:20:00Z", actor="dependabot[bot]"),
            public_event("WatchEvent", "2026-11-14T12:21:00Z", actor="other-user"),
            public_event("PushEvent", "2026-11-14T12:22:00Z", public=False),
            public_event("PushEvent", "2026-11-14T13:00:00Z"),
            public_event("PushEvent", "2020-01-01T00:00:00Z"),
            public_event("PushEvent", "bad-date"),
            {"created_at": "2026-11-14T12:29:00Z"},
        ]
        data = self.run_fetch(api, "secret-test-token")
        self.assertEqual(data["last_public_activity"], "2026-11-14T12:08:00Z")
        self.assertEqual(data["activity_source"], "github-public-events")
        self.assertNotIn("events", data)

    def test_empty_or_malformed_activity_is_unavailable(self):
        for events in (None, {}, [], [None], [public_event("PushEvent", "bad-date")]):
            with self.subTest(events=events):
                api = PublicAPI()
                api.events = events
                data = self.run_fetch(api)
                self.assertIsNone(data["last_public_activity"])
                self.assertTrue(data["activity_source"].startswith("unavailable:"))

    def test_valid_activity_in_the_fetch_second_keeps_timestamp_precision(self):
        class PreciseDatetime(FixedDatetime):
            @classmethod
            def now(cls, tz=None):
                return super().now(tz).replace(microsecond=500000)

        api = PublicAPI()
        api.events = [public_event("PushEvent", "2026-11-14T12:30:00.250000Z")]
        data = self.run_fetch(api, clock=PreciseDatetime)
        self.assertEqual(data["last_public_activity"], "2026-11-14T12:30:00.250000Z")

    def test_activity_request_failure_does_not_erase_other_real_metrics(self):
        api = PublicAPI()

        def network(request, timeout, *, context=None):
            if "/events/public" in request.full_url:
                raise HTTPError(request.full_url, 403, "unavailable", {}, None)
            return api(request, timeout, context=context)

        data = self.run_fetch(network)
        self.assertIsNone(data["last_public_activity"])
        self.assertTrue(data["activity_source"].startswith("unavailable:"))
        self.assertEqual(data["stars"], 9)

    def test_language_provenance_keeps_admitted_repositories_with_no_code_bytes(self):
        api = PublicAPI()
        api.languages["own-a"] = {}
        data = self.run_fetch(api)
        self.assertEqual(data["language_repositories"][0], {"name": "own-a", "languages": []})
        self.assertEqual(data["languages"], [{"name": "C", "bytes": 200}, {"name": "Python", "bytes": 10}])

    def test_graphql_is_preferred_when_public_counts_agree(self):
        api = PublicAPI()
        api.graphql = api.graphql_calendar()
        data = self.run_fetch(api, "secret-test-token")
        self.assertEqual(data["calendar_source"], "github-graphql-contributions")
        self.assertEqual(data["days"][0]["count"], 3)
        self.assertNotIn("secret-test-token", json.dumps(data))

    def test_matching_public_calendar_exposes_the_exact_graphql_commit_total(self):
        api = PublicAPI()
        api.graphql = api.graphql_calendar()
        data = self.run_fetch(api, "secret-test-token")
        self.assertEqual(data["commits"], 23)

    def test_a_genuine_zero_commit_total_is_preserved(self):
        api = PublicAPI()
        api.graphql = api.graphql_calendar()
        api.graphql["data"]["user"]["contributionsCollection"]["totalCommitContributions"] = 0
        self.assertEqual(self.run_fetch(api, "secret-test-token")["commits"], 0)

    def test_malformed_typed_commit_totals_remain_unavailable(self):
        for invalid in (None, -1, True, "23", 2.5):
            with self.subTest(invalid=invalid):
                api = PublicAPI()
                api.graphql = api.graphql_calendar()
                api.graphql["data"]["user"]["contributionsCollection"]["totalCommitContributions"] = invalid
                data = self.run_fetch(api, "secret-test-token")
                self.assertIsNone(data["commits"])
                self.assertEqual(data["calendar_source"], "github-graphql-contributions")

    def test_a_missing_typed_commit_total_remains_unavailable(self):
        api = PublicAPI()
        api.graphql = api.graphql_calendar()
        del api.graphql["data"]["user"]["contributionsCollection"]["totalCommitContributions"]
        data = self.run_fetch(api, "secret-test-token")
        self.assertIsNone(data["commits"])
        self.assertEqual(data["calendar_source"], "github-graphql-contributions")

    def test_incomplete_authenticated_calendar_drops_the_commit_total(self):
        api = PublicAPI()
        api.graphql = api.graphql_calendar()
        days = api.graphql["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"][0]["contributionDays"]
        del days[0]
        data = self.run_fetch(api, "secret-test-token")
        self.assertIsNone(data["commits"])
        self.assertEqual(data["calendar_source"], "github-public-contributions-html")

    def test_token_only_counts_are_replaced_with_public_counts(self):
        api = PublicAPI()
        api.graphql = api.graphql_calendar(changed_count=40)
        data = self.run_fetch(api, "secret-test-token")
        self.assertEqual(data["calendar_source"], "github-public-contributions-html")
        self.assertEqual(data["days"][0]["count"], 3)
        self.assertIsNone(data["commits"])

    def test_graphql_errors_fall_back_to_public_html(self):
        api = PublicAPI()
        api.graphql = {"errors": [{"message": "Token cannot read this calendar"}]}
        data = self.run_fetch(api, "secret-test-token")
        self.assertEqual(data["calendar_source"], "github-public-contributions-html")
        self.assertEqual(len(data["days"]), 365)
        self.assertIsNone(data["commits"])

    def test_graphql_counts_are_not_cached_when_public_verification_fails(self):
        api = PublicAPI()
        api.graphql = api.graphql_calendar()
        api.break_public_calendar = True
        data = self.run_fetch(api, "secret-test-token")
        self.assertIsNone(data["days"])
        self.assertTrue(data["calendar_source"].startswith("unavailable:"))
        self.assertIsNone(data["commits"])


class TransportTests(unittest.TestCase):
    def client(self):
        self.assertTrue(hasattr(github_stats, "_Client"), "Bounded GitHub transport is not implemented")
        return github_stats._Client()

    def test_explicit_native_context_reaches_both_api_and_public_html_requests(self):
        client = self.client()
        contexts = []

        def network(request, timeout, *, context=None):
            self.assertIsNotNone(context, "Every HTTPS request must use the explicit native trust context")
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertIsInstance(context, github_stats.truststore.SSLContext)
            contexts.append(context)
            return Response({"followers": 1})

        with patch("scripts.github_stats.urlopen", network):
            data, _ = client.json("https://api.github.com/users/Fiudeus")
            client.html("https://github.com/users/Fiudeus/contributions")
        self.assertEqual(data, {"followers": 1})
        self.assertIs(contexts[0], contexts[1])

    def test_transient_http_errors_retry_then_return_real_json(self):
        client = self.client()
        calls = []

        def network(request, timeout, *, context=None):
            calls.append(request.full_url)
            if len(calls) < 3:
                raise HTTPError(request.full_url, 503, "temporary", {}, None)
            return Response({"followers": 1})

        with patch("scripts.github_stats.urlopen", network), patch("scripts.github_stats.time.sleep"):
            data, _ = client.json("https://api.github.com/users/Fiudeus")
        self.assertEqual(data, {"followers": 1})
        self.assertEqual(len(calls), 3)

    def test_permanent_errors_stop_after_three_attempts_without_leaking_details(self):
        client = self.client()
        calls = []

        def network(request, timeout, *, context=None):
            calls.append(request.full_url)
            raise URLError("sensitive-proxy-credential")

        with patch("scripts.github_stats.urlopen", network), patch("scripts.github_stats.time.sleep"):
            with self.assertRaises(RuntimeError) as raised:
                client.json("https://api.github.com/users/Fiudeus")
        self.assertEqual(len(calls), 3)
        self.assertNotIn("sensitive-proxy-credential", str(raised.exception))

    def test_non_retryable_http_error_does_not_waste_requests(self):
        client = self.client()
        calls = []

        def network(request, timeout, *, context=None):
            calls.append(request.full_url)
            raise HTTPError(request.full_url, 404, "missing", {}, None)

        with patch("scripts.github_stats.urlopen", network):
            with self.assertRaises(RuntimeError):
                client.json("https://api.github.com/users/Fiudeus")
        self.assertEqual(len(calls), 1)

    def test_oversized_responses_are_rejected_without_retry(self):
        client = self.client()
        with patch("scripts.github_stats.urlopen", return_value=Response(" " * 2_000_001)):
            with self.assertRaisesRegex(RuntimeError, "size"):
                client.json("https://api.github.com/users/Fiudeus")

    def test_the_request_budget_bounds_the_whole_fetch(self):
        with patch("scripts.github_stats._MAX_REQUESTS", 1, create=True):
            client = self.client()
        with patch("scripts.github_stats.urlopen", return_value=Response({"followers": 1})):
            client.json("https://api.github.com/users/Fiudeus")
            with self.assertRaisesRegex(RuntimeError, "budget"):
                client.json("https://api.github.com/users/Fiudeus")


if __name__ == "__main__":
    unittest.main()
