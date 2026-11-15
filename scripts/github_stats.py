"""Acquire minimal public GitHub aggregates for the profile snapshot.

Scopes: repos includes all owned public repositories, including forks; stars is
the sum on owned public non-forks excluding the configured repositories;
languages sums bytes on the same scope excluding the profile repository too.
Each admitted repository has minimal language-byte provenance; validation checks
that those bytes sum exactly to the aggregate. This measures repository content,
not individual authorship, skill, or time spent.
PRs and issues count authored public items created in the rolling calendar year.
The calendar contains public-visible counts, which may include anonymous private
contribution counts the account holder elected to display publicly. Authenticated
calendar counts are used only after matching the tokenless public calendar.
The commit total is GitHub's authenticated typed contribution aggregate for the
same period, accepted only after its daily calendar counts match the tokenless
public calendar exactly. No repository or private contribution details are
requested or cached. Missing or invalid typed totals stay null; search-commit
results and rounded HTML percentages are never substituted.
Latest public activity is the maximum valid timestamp in the tokenless public
events feed across event types. It is neither a login time nor online presence.
No event payload or event repository is retained in the snapshot.

HTTPS uses an explicit native certificate-store context from truststore. Fetching
never reads or writes a cache and does not change process-wide SSL defaults.
"""

from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import ssl
import tempfile
import time
import truststore
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen


_SNAPSHOT_FIELDS = {
    "schema_version", "login", "fetched_at", "source", "repos", "stars",
    "followers", "languages", "days", "calendar_source", "created_at",
    "following", "commits", "prs", "issues", "contributions", "period_start", "period_end",
    "language_repositories", "last_public_activity", "activity_source",
}
_MAX_SNAPSHOT_BYTES = 2_000_000
_MAX_RESPONSE_BYTES = 2_000_000
_MAX_REQUESTS = 128
_MAX_PAGES = 10
_MAX_EVENT_PAGES = 3
_MAX_ATTEMPTS = 3
_TIMEOUT_SECONDS = 10
_LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def _login(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", value
    ):
        raise ValueError("login must be a GitHub username")
    return value


def _text(value: object, label: str, maximum: int = 200) -> str:
    if (
        not isinstance(value, str) or not value.strip() or len(value) > maximum
        or re.search(r"[\x00-\x1f\x7f]", value)
    ):
        raise ValueError(f"{label} must be non-empty single-line text")
    return value


def _calendar_window(today: date) -> tuple[date, date]:
    """The previous anniversary is excluded; today is included (365/366 days)."""
    if type(today) is not date or today.year < 2:
        raise ValueError("today must be a date with a previous calendar year")
    try:
        anniversary = today.replace(year=today.year - 1)
    except ValueError:  # February 29 has no anniversary in a non-leap year.
        anniversary = date(today.year - 1, 2, 28)
    return anniversary + timedelta(days=1), today


def _integer(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _utc_datetime(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)", value
    ):
        raise ValueError(f"{label} must be a UTC ISO timestamp")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _language_bytes(value: object, label: str) -> dict[str, int]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    result = {}
    for language in value:
        if not isinstance(language, dict) or set(language) != {"name", "bytes"}:
            raise ValueError(f"{label} entries must contain only name and bytes")
        name = _text(language["name"], "language name", 80).casefold()
        if name in result:
            raise ValueError(f"duplicate language in {label}")
        result[name] = _integer(language["bytes"], "language bytes")
    return result


def _validate_language_provenance(languages: object, repositories: object, login: str) -> None:
    if languages is None:
        if repositories is not None:
            raise ValueError("unavailable languages require unavailable repository provenance")
        return
    aggregate = _language_bytes(languages, "aggregate languages")
    if not isinstance(repositories, list):
        raise ValueError("language repository provenance must be a list")
    seen = set()
    summed = {}
    for repository in repositories:
        if not isinstance(repository, dict) or set(repository) != {"name", "languages"}:
            raise ValueError("language repository provenance must contain only name and languages")
        name = repository["name"]
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", name):
            raise ValueError("invalid language repository name")
        folded = name.casefold()
        if folded in seen:
            raise ValueError("duplicate language repository name")
        if folded in {login.casefold(), "luminaread"}:
            raise ValueError("excluded repository in language provenance")
        seen.add(folded)
        for language, size in _language_bytes(repository["languages"], f"languages for {name}").items():
            summed[language] = summed.get(language, 0) + size
    if {name: size for name, size in aggregate.items() if size} != {name: size for name, size in summed.items() if size}:
        raise ValueError("repository language sums do not match aggregate languages")


def _iso_date(value: object) -> date:
    if not isinstance(value, str):
        raise ValueError("calendar date must be an ISO date")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("calendar date must use YYYY-MM-DD")
    return parsed


def _day(day: dict) -> dict:
    if not isinstance(day, dict) or set(day) != {"date", "count", "level"}:
        raise ValueError("each contribution day must have date, count, and level")
    parsed = _iso_date(day.get("date"))
    count = _integer(day.get("count"), "contribution count")
    level = _integer(day.get("level"), "contribution level")
    if level > 4 or (level == 0) != (count == 0):
        raise ValueError("contribution level must be 0..4 and match zero counts")
    return {"date": parsed.isoformat(), "count": count, "level": level}


def _complete_days(days: list[dict], start: date, end: date) -> list[dict]:
    indexed = {}
    for item in days:
        parsed = _day(item)
        key = parsed["date"]
        if key in indexed:
            raise ValueError(f"duplicate contribution date: {key}")
        if start <= _iso_date(key) <= end:
            indexed[key] = parsed
    expected = (end - start).days + 1
    if len(indexed) != expected:
        raise ValueError(f"incomplete contribution calendar: {len(indexed)}/{expected} days")
    return [indexed[key] for key in sorted(indexed)]


class _ContributionHTML(HTMLParser):
    """Join modern calendar cells to their tooltips by ID, never by position."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells = []
        self.tooltips = {}
        self._target = None
        self._parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-date" in attrs:
            self.cells.append(attrs)
        if tag == "tool-tip":
            self._target = attrs.get("for")
            self._parts = []

    def handle_data(self, text):
        if self._target is not None:
            self._parts.append(text)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self._target is not None:
            self.tooltips[self._target] = " ".join("".join(self._parts).split())
            self._target = None
            self._parts = []


def _parse_calendar_html(html: str, start: date, end: date) -> list[dict]:
    parser = _ContributionHTML()
    parser.feed(html)
    parser.close()
    days = []
    for cell in parser.cells:
        parsed = _iso_date(cell["data-date"])
        if not start <= parsed <= end:
            continue
        raw_count = cell.get("data-count")
        if raw_count is None:
            tooltip = parser.tooltips.get(cell.get("id"), "")
            match = re.match(r"^(No|[0-9]+(?:,[0-9]{3})*) contributions? on\b", tooltip)
            if match is None:
                raise ValueError(f"missing actual contribution count on {parsed}")
            raw_count = "0" if match[1] == "No" else match[1].replace(",", "")
        if not re.fullmatch(r"[0-9]+", raw_count):
            raise ValueError(f"invalid contribution count on {parsed}")
        level = cell.get("data-level", "")
        if level not in {"0", "1", "2", "3", "4"}:
            raise ValueError(f"missing contribution level on {parsed}")
        days.append({"date": parsed.isoformat(), "count": int(raw_count), "level": int(level)})
    return _complete_days(days, start, end)


def _validate_snapshot(data: object, login: str) -> dict:
    if not isinstance(data, dict) or set(data) != _SNAPSHOT_FIELDS:
        raise ValueError("snapshot must contain only the schema 2 aggregate fields")
    if type(data["schema_version"]) is not int or data["schema_version"] != 2:
        raise ValueError("unsupported snapshot schema_version")
    if _login(data["login"]).casefold() != _login(login).casefold():
        raise ValueError("snapshot login does not match the configured login")
    stamp = _utc_datetime(data["fetched_at"], "fetched_at")
    created = _utc_datetime(data["created_at"], "created_at") if data["created_at"] is not None else None
    if created is not None and created > stamp:
        raise ValueError("account creation cannot be later than fetched_at")
    start = _iso_date(data["period_start"])
    end = _iso_date(data["period_end"])
    if _calendar_window(end) != (start, end):
        raise ValueError("snapshot period must be a complete rolling calendar year")
    _text(data["source"], "source")
    _text(data["calendar_source"], "calendar_source")
    _text(data["activity_source"], "activity_source")
    for metric in ("repos", "stars", "followers", "following", "commits", "prs", "issues", "contributions"):
        if data[metric] is not None:
            _integer(data[metric], metric)
    _validate_language_provenance(data["languages"], data["language_repositories"], login)
    activity = data["last_public_activity"]
    if activity is None:
        if not data["activity_source"].startswith("unavailable:"):
            raise ValueError("unavailable public activity requires unavailable provenance")
    else:
        activity = _utc_datetime(activity, "last_public_activity")
        if data["activity_source"] != "github-public-events":
            raise ValueError("public activity must identify the public events source")
        if activity > stamp or (created is not None and activity < created):
            raise ValueError("public activity timestamp is outside account/fetch bounds")
    days = data["days"]
    unavailable = data["calendar_source"].startswith("unavailable:")
    if days is None:
        if not unavailable:
            raise ValueError("an unavailable calendar requires unavailable provenance")
        if data["contributions"] is not None:
            raise ValueError("an unavailable calendar cannot provide verified contribution totals")
    else:
        if not isinstance(days, list) or not days:
            raise ValueError("calendar must be a complete list or null")
        if unavailable:
            raise ValueError("available calendar has unavailable provenance")
        if _complete_days(days, start, end) != days:
            raise ValueError("calendar must be ordered with no dates outside its rolling year")
        if data["contributions"] != sum(day["count"] for day in days):
            raise ValueError("contribution total does not match the public calendar")
    return data


def load_snapshot(path: Path, login: str) -> dict:
    """Load a validated, minimal snapshot; corrupt or wrong-user caches fail closed."""
    with Path(path).open("rb") as handle:
        raw = handle.read(_MAX_SNAPSHOT_BYTES + 1)
    if len(raw) > _MAX_SNAPSHOT_BYTES:
        raise ValueError("snapshot exceeds the aggregate cache size limit")
    return _validate_snapshot(json.loads(raw.decode("utf-8")), login)


def save_snapshot(path: Path, data: dict) -> None:
    """Validate first, then replace atomically so failed refreshes preserve the cache."""
    _validate_snapshot(data, data.get("login") if isinstance(data, dict) else "")
    raw = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(raw) > _MAX_SNAPSHOT_BYTES:
        raise ValueError("snapshot exceeds the aggregate cache size limit")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class GitHubStatsError(RuntimeError):
    """A refresh failed; the caller should retain its previous validated snapshot."""


class _Client:
    def __init__(self):
        self.remaining = _MAX_REQUESTS
        self.context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    def read(self, url: str, *, token=None, payload=None, accept="application/vnd.github+json"):
        destination = urlsplit(url)
        if (
            destination.scheme != "https" or destination.hostname not in {"api.github.com", "github.com"}
            or destination.username is not None or destination.password is not None
            or destination.port not in {None, 443}
        ):
            raise GitHubStatsError("unsupported GitHub request destination")
        headers = {"User-Agent": "fiudeus-terminal-profile/1", "Accept": accept}
        if token:
            if destination.hostname != "api.github.com":
                raise GitHubStatsError("credentials are only permitted on GitHub API requests")
            headers["Authorization"] = f"Bearer {token}"
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")
        request = Request(url, headers=headers, data=body)
        for attempt in range(_MAX_ATTEMPTS):
            if self.remaining <= 0:
                raise GitHubStatsError("GitHub request budget exhausted")
            self.remaining -= 1
            try:
                with urlopen(request, timeout=_TIMEOUT_SECONDS, context=self.context) as response:
                    raw = response.read(_MAX_RESPONSE_BYTES + 1)
                    response_headers = {key.lower(): value for key, value in response.headers.items()}
                if len(raw) > _MAX_RESPONSE_BYTES:
                    raise GitHubStatsError("GitHub response exceeds the size limit")
                return raw, response_headers
            except HTTPError as error:
                status = error.code
                error.close()
                retryable = status in {429, 500, 502, 503, 504}
                message = f"GitHub request failed (HTTP {status})"
            except (URLError, OSError, TimeoutError) as error:
                retryable = True
                message = f"GitHub network request failed ({type(error).__name__})"
            if not retryable or attempt + 1 == _MAX_ATTEMPTS:
                raise GitHubStatsError(message) from None
            time.sleep(0.25 * (2 ** attempt))
        raise GitHubStatsError("GitHub request failed")  # Defensive: attempts is positive.

    def json(self, url: str, **kwargs):
        raw, headers = self.read(url, **kwargs)
        try:
            return json.loads(raw.decode("utf-8")), headers
        except (ValueError, UnicodeError):
            raise GitHubStatsError("invalid GitHub JSON response") from None

    def html(self, url: str) -> str:
        raw, _ = self.read(url, accept="text/html")
        try:
            return raw.decode("utf-8")
        except UnicodeError:
            raise GitHubStatsError("invalid GitHub HTML response") from None


def _repositories(client: _Client, login: str, expected: int, token: str | None) -> list[dict]:
    repos = []
    seen = set()
    for page in range(1, _MAX_PAGES + 1):
        query = urlencode({"type": "owner", "sort": "full_name", "direction": "asc", "per_page": 100, "page": page})
        data, headers = client.json(f"https://api.github.com/users/{login}/repos?{query}", token=token)
        if not isinstance(data, list):
            raise GitHubStatsError("invalid public repository page")
        for repo in data:
            if not isinstance(repo, dict) or not isinstance(repo.get("owner"), dict):
                raise GitHubStatsError("invalid public repository record")
            if type(repo.get("private")) is not bool or type(repo.get("fork")) is not bool:
                raise GitHubStatsError("missing public repository scope flags")
            if repo["private"] or repo["owner"].get("login", "").casefold() != login.casefold():
                continue
            name = repo.get("name")
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", name):
                raise GitHubStatsError("invalid public repository name")
            if name.casefold() in seen:
                raise GitHubStatsError("duplicate public repository across pagination")
            seen.add(name.casefold())
            repos.append({"name": name, "fork": repo["fork"], "stars": _integer(repo.get("stargazers_count"), "stars")})
        has_next = bool(re.search(r';\s*rel="next"', headers.get("link", "")))
        if not has_next and (len(data) < 100 or len(repos) == expected):
            if len(repos) != expected:
                raise GitHubStatsError("public repository count changed or pagination is incomplete")
            return repos
    raise GitHubStatsError("public repository page limit reached")


def _parse_graphql_calendar(data: object, start: date, end: date) -> list[dict]:
    try:
        if not isinstance(data, dict) or data.get("errors"):
            raise ValueError("GitHub GraphQL reported an unavailable calendar")
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        days = []
        for week in weeks:
            for item in week["contributionDays"]:
                if start <= _iso_date(item["date"]) <= end:
                    days.append({
                        "date": item["date"], "count": item["contributionCount"],
                        "level": _LEVELS[item["contributionLevel"]],
                    })
        return _complete_days(days, start, end)
    except (KeyError, TypeError):
        raise ValueError("incomplete GitHub GraphQL calendar") from None


def _calendar(client: _Client, login: str, start: date, end: date, token: str | None):
    authenticated = None
    commits = None
    if token:
        query = """query ProfileCalendar($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) { contributionsCollection(from: $from, to: $to) {
            totalCommitContributions
            contributionCalendar { weeks { contributionDays { date contributionCount contributionLevel } } }
          } }
        }"""
        try:
            response, _ = client.json("https://api.github.com/graphql", token=token, payload={
                "query": query,
                "variables": {"login": login, "from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"},
            })
            authenticated = _parse_graphql_calendar(response, start, end)
            raw_commits = response["data"]["user"]["contributionsCollection"].get("totalCommitContributions")
            if type(raw_commits) is int and raw_commits >= 0:
                commits = raw_commits
        except (GitHubStatsError, ValueError):
            pass
    try:
        public = []
        # GitHub's HTML endpoint selects a single calendar year even for a
        # cross-year from/to query. Request each year separately, then clip.
        for year in range(start.year, end.year + 1):
            query = urlencode({"from": f"{year}-01-01", "to": f"{year}-12-31"})
            html = client.html(f"https://github.com/users/{login}/contributions?{query}")
            public.extend(_parse_calendar_html(html, max(start, date(year, 1, 1)), min(end, date(year, 12, 31))))
        public = _complete_days(public, start, end)
    except GitHubStatsError:
        return None, "unavailable: public contribution calendar request failed", None
    except ValueError:
        return None, "unavailable: public contribution calendar incomplete or changed", None
    if authenticated is not None and [day["count"] for day in authenticated] == [day["count"] for day in public]:
        return authenticated, "github-graphql-contributions", commits
    return public, "github-public-contributions-html", None


def _authored_count(client: _Client, login: str, kind: str, start: date, end: date, token: str | None):
    query = urlencode({"q": f"author:{login} is:{kind} is:public created:{start}..{end}", "per_page": 1})
    try:
        data, _ = client.json(f"https://api.github.com/search/issues?{query}", token=token)
        if not isinstance(data, dict) or data.get("incomplete_results") is not False:
            return None
        return _integer(data.get("total_count"), f"public {kind} count")
    except (GitHubStatsError, ValueError):
        return None


def _read_public_events(client: _Client, login: str) -> list | None:
    """Read at most GitHub's 300 public events, never sending API credentials."""
    events = []
    try:
        for page in range(1, _MAX_EVENT_PAGES + 1):
            response, headers = client.json(
                f"https://api.github.com/users/{login}/events/public?per_page=100&page={page}",
                token=None,
            )
            if not isinstance(response, list):
                return None
            events.extend(response)
            if not re.search(r';\s*rel="next"', headers.get("link", "")):
                return events
    except GitHubStatsError:
        return None
    return None  # A bounded partial feed is not a verified maximum.


def _last_public_activity(events: list | None, login: str, fetched_at: datetime, created_at: datetime | None):
    """Select across all valid action types; do not infer presence or a login."""
    if events is None:
        return None, "unavailable: public events request failed or malformed"
    latest = None
    for event in events:
        if not isinstance(event, dict) or event.get("public") is not True:
            continue
        actor = event.get("actor")
        kind = event.get("type")
        if (
            not isinstance(actor, dict) or not isinstance(actor.get("login"), str)
            or actor["login"].casefold() != login.casefold()
            or not isinstance(kind, str) or not kind.endswith("Event")
        ):
            continue
        try:
            stamp = _utc_datetime(event.get("created_at"), "public event created_at")
        except ValueError:
            continue
        if stamp > fetched_at or (created_at is not None and stamp < created_at):
            continue
        if latest is None or stamp > latest:
            latest = stamp
    if latest is None:
        return None, "unavailable: no valid public events"
    return latest.isoformat().replace("+00:00", "Z"), "github-public-events"


def fetch(login: str, exclude_repos: list[str], today: date | None = None) -> dict:
    """Refresh public aggregates; required REST failures leave cache policy to the caller.

    GH_TOKEN or GITHUB_TOKEN enables authenticated API rate limits and preferred
    GraphQL calendar and typed commit-total acquisition. Both authenticated
    aggregates require matching public daily counts. Public HTML is always
    fetched without a token.
    A historical ``today`` changes the requested period, never ``fetched_at``.
    """
    login = _login(login)
    if not isinstance(exclude_repos, list) or any(not isinstance(name, str) or not name.strip() for name in exclude_repos):
        raise ValueError("exclude_repos must be a list of repository names or owner/name pairs")
    skip = {name.casefold() for name in exclude_repos}
    skip.add("luminaread")
    now = datetime.now(timezone.utc)
    start, end = _calendar_window(today if today is not None else now.date())
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or None
    client = _Client()
    user, _ = client.json(f"https://api.github.com/users/{login}", token=token)
    if not isinstance(user, dict) or _login(user.get("login")).casefold() != login.casefold():
        raise GitHubStatsError("public user response does not match the requested login")
    login = user["login"]
    public_count = _integer(user.get("public_repos"), "public repository count")
    repos = _repositories(client, login, public_count, token)
    stars = 0
    totals = {}
    language_repositories = []
    for repo in repos:
        name = repo["name"]
        if repo["fork"] or {name.casefold(), f"{login}/{name}".casefold()} & skip:
            continue
        stars += repo["stars"]
        if name.casefold() == login.casefold():
            continue
        languages, _ = client.json(f"https://api.github.com/repos/{login}/{quote(name, safe='')}/languages", token=token)
        if not isinstance(languages, dict):
            raise GitHubStatsError("invalid public repository language response")
        repository_languages = []
        for language, byte_count in languages.items():
            _text(language, "language name", 80)
            byte_count = _integer(byte_count, "language bytes")
            if byte_count:
                totals[language] = totals.get(language, 0) + byte_count
                repository_languages.append({"name": language, "bytes": byte_count})
        language_repositories.append({
            "name": name,
            "languages": sorted(repository_languages, key=lambda item: (-item["bytes"], item["name"])),
        })
    prs = _authored_count(client, login, "pr", start, end, token)
    issues = _authored_count(client, login, "issue", start, end, token)
    days, calendar_source, commits = _calendar(client, login, start, end, token)
    events = _read_public_events(client, login)
    fetched_at = datetime.now(timezone.utc)
    created_at = _utc_datetime(user["created_at"], "created_at") if user.get("created_at") is not None else None
    last_public_activity, activity_source = _last_public_activity(events, login, fetched_at, created_at)
    data = {
        "schema_version": 2, "login": login,
        "fetched_at": fetched_at.isoformat().replace("+00:00", "Z"),
        "source": "github-rest-public", "created_at": user.get("created_at"),
        "repos": public_count, "stars": stars, "followers": user.get("followers"),
        "following": user.get("following"), "commits": commits, "prs": prs, "issues": issues,
        "contributions": sum(day["count"] for day in days) if days is not None else None,
        "period_start": start.isoformat(), "period_end": end.isoformat(),
        "languages": [{"name": name, "bytes": size} for name, size in sorted(totals.items(), key=lambda item: (-item[1], item[0]))],
        "language_repositories": sorted(language_repositories, key=lambda item: item["name"].casefold()),
        "days": days, "calendar_source": calendar_source,
        "last_public_activity": last_public_activity, "activity_source": activity_source,
    }
    return _validate_snapshot(data, login)
