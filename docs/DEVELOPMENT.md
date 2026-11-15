# Running and editing the profile

The final profile has three terminal windows: home, fastfetch and toolbox. The user selected the toolbox with Unicode outline panels and the role `Data Scientist`. All seven original GitHub category names and technologies are retained. The user's latest Languages order is **Python, Java, C++, SQL, Bash**, adding Java for 27 technologies overall; other category orders are unchanged. The greeting is one line; native GitHub pins and the contribution graph handle projects and activity. There are no tmux footers, pets, closing windows or project windows.

## Local use

Python 3.11+ is required. From the repository root on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m scripts.generate
.\.venv\Scripts\python.exe -m scripts.validate
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m http.server 8000 --bind 127.0.0.1
```

Open [the preview](http://127.0.0.1:8000/previews/index.html), or open `previews/index.html` directly. Ctrl+C stops the local server. On Linux/macOS use `python3 -m venv .venv` and `.venv/bin/python`.

Default generation is offline and deterministic from `data/github.json`. Explicit refresh:

```powershell
.\.venv\Scripts\python.exe -m scripts.generate --refresh
```

Optional `GH_TOKEN` or `GITHUB_TOKEN` raises API limits and enables verified GraphQL commit contributions. Never put credentials in TOML or Git. Missing optional metrics display `n/a` or `unavailable`; they are not replaced with fabricated zeroes. Native TLS certificate and hostname verification stay enabled. Actions supplies its built-in token automatically.

Other useful modes:

```powershell
.\.venv\Scripts\python.exe -m scripts.generate --static --out .local/static-preview
.\.venv\Scripts\python.exe -m scripts.generate --out .local/another-preview
.\.venv\Scripts\python.exe -m scripts.generate --config config.toml --snapshot data/github.json --out .local/another-preview
```

## Content and visual choices

Edit text, commands, complete stack, learning topics and palettes in `config.toml`. Window captions are under `[windows]`; `terminal.banner_spacing` controls desktop FIGlet spacing. `profile.banner_font` selects an existing pyfiglet font. The lavender/pink/red banner ramp assigns a solid ANSI foreground to each character. `profile.activity_label` names the actual public-event timestamp at the top of the opening terminal; it is not a login/presence indicator.

`toolbox.style = "panels"` is the selected default. The `tree` and `badges` alternatives remain available in the local preview selector and [comparison page](../previews/toolbox-variants.html). The selector previews without editing configuration. Every variant retains the same full stack. Currently Learning preserves the original five topics and adds the user's Deep learning and Mathematics.

Desktop: 900px, 92 cells, 15px text and 23px row pitch. Compact: 540px, 54 cells, selected at a 600px viewport. Bounds and fastfetch subcolumns are checked before output is written.

## Architecture

| Source | Responsibility |
| --- | --- |
| `scripts/generate.py` | Config/snapshot CLI, three scenes, comparison assets, README, HTML and text exports |
| `scripts/svg.py` | Escaped SVG, definition reuse, CSS registry, static/reduced-motion fallback |
| `scripts/terminal.py` | Unicode text cells, local font outlines, connected symbols, ANSI backgrounds, two-cell logo slots |
| `scripts/icons.py` | Checksummed original logo assets, theme-colored vector symbols and inline PNG luminance mask |
| `scripts/toolbox.py` | Tree, console badges and Unicode outline panels using the same complete inventory |
| `scripts/art.py` | Existing FIGlet lettering through pyfiglet |
| `scripts/motion.py` | One-shot typing, output reveal and cursors |
| `scripts/scenes.py` | Shared window framing and three compositions |
| `scripts/github_stats.py` | Verified TLS, bounded public acquisition, pagination, scoped metrics and atomic snapshots |
| `scripts/validate.py` | XML, references, cell bounds, image budgets and README/comparison resource checks |
| `scripts/render.mjs` | Optional sharp PNG rendering |
| `scripts/browser-qa.mjs` | Optional Playwright/sharp source selection, motion, bounds, scaled frame visibility and preview controls |

JetBrains Mono Regular/Bold v2.304 is vendored with OFL and hashes. Only used glyphs are outlined once per SVG and placed with `use`. `wcwidth` determines text width; NFC normalization preserves combining anchors. Unsupported glyphs and controls fail with useful errors.

Logos are copied from the user's actual original badges, with source URLs/checksums under `assets/icons`. Matplotlib uses the existing repository SVG. Java, subsequently added by the user, uses Devicon v2.17.0's coffee-cup mark with its MIT license vendored locally. XGBoost had no badge icon, so no substitute is shown. SVG geometry is retained and paints adapt to the foreground/background of the current terminal cell. Seaborn retains its original PNG bytes, embedded as a data URI and tinted through an SVG luminance mask. Matplotlib's plotting background takes the cell background. No blue/green/orange brand colors break the palette. No runtime font/icon request or CDN is required. Logo slots occupy two cells; a live-terminal equivalent requires inline graphics support. Surrounding layout is ordinary text/pseudographics. Plain-text exports under `previews/text/` replace private icon markers with matching-width spaces and retain every name. The profile README ends after the three terminal images; documentation and transcripts remain repository files.

## Statistics

The genuine schema-2 JSON snapshot records UTC fetch time, exact rolling dates, language bytes per admitted repository and public-event provenance. The period excludes the previous anniversary and includes today, so it can contain 365 or 366 days. Language volume is taken from the current default branches and is not limited to that year.

- Repositories: public account count, including forks.
- Stars: owned public non-forks, excluding configured repositories.
- Followers/following/account age: public user metadata.
- Languages: GitHub Linguist bytes in owned public non-forks, excluding the profile and LuminaRead; all code in those repositories, not personally authored lines or skill. The chart says how many repositories were included, shows one decimal place and groups the remaining languages as `other` without renormalizing the leading languages. `language_repositories` preserves the exact per-repository inputs; load/save verifies that their sum equals the aggregate.
- PRs/issues: authored public items created within the period, from complete search results.
- Activity/streak: actual public-visible daily contributions. The best streak is explicitly within the displayed year. Today may remain unfinished.
- Commits: authenticated `totalCommitContributions` only when authenticated daily counts agree with the tokenless public calendar. Otherwise unavailable; contribution totals and commit-search counts are not substituted.
- Last public activity: the latest valid timestamp from the general tokenless `/users/{login}/events/public` feed, across push, PR, issue, review, star and other event types. Only the configured user's public events are admitted. Bots/other actors, private entries, malformed/future timestamps and events before account creation are excluded. Only the timestamp and its source are cached. GitHub exposes up to 300 recent events within 30 days, with possible delays from 30 seconds to six hours. An empty/failed feed stays unavailable; it is never replaced by build time or described as online status.

Required metadata/language failures stop refresh. Optional unavailable metrics stay null with provenance. Complete calendar, language sums, timestamp, count and login validation precede an atomic temporary-file replacement. Retries, pagination, response size and total requests are bounded. No private repository details are saved. See [the language audit](STATISTICS.md) for the initial byte breakdown and metric definitions.

## Motion and QA

The opening command types once; output and the next prompt appear in sequence. The resting cursor blinks every 1.25 seconds. All complete states are CSS defaults. `prefers-reduced-motion: reduce` disables every animation; `--static` emits complete static images. README picture sources and the local preview also choose four dedicated still home variants (theme × width), avoiding browser inconsistencies with media preferences inside external SVG images. Generation writes 16 profile SVGs plus 12 toolbox comparisons, 28 total; the README has 16 local resource references. Metrics never animate.

Optional rendering tools:

```powershell
npm install --no-save --prefix .local/node sharp playwright
$env:PROFILE_NODE_MODULES = "$PWD/.local/node/node_modules"
npx --prefix .local/node playwright install chromium
node scripts/render.mjs
node scripts/browser-qa.mjs
```

An installed Chromium/Edge executable can be selected with `PROFILE_BROWSER`. QA binds a temporary server only to 127.0.0.1 and closes it on completion. It also checks actual sharp/librsvg pixels: the seven panel bottoms and sides must remain visible across 20 theme/layout/scale combinations, including the 840px case that previously lost strokes. Box-drawing uses a non-scaling one-pixel stroke so `crispEdges` cannot round a reduced stroke away. Contact sheets are under `previews`; diagnostic screenshots/report are ignored under `previews/qa`.

## Automation and GitHub limits

The workflow tests and compares deterministic offline output on pushes/PRs. Schedule (03:17 UTC) and manual dispatch refresh into temporary artifacts. Hosted schedules use the default branch and may be delayed.

After the workflow is deployed to the repository's default branch with the user's approval, its separate publishing job automatically updates 35 allowlisted generated files after a successful scheduled/manual build. It uses the built-in `GITHUB_TOKEN`; no personal token or extra repository variables are required. Publishing requires the official repository and the exact default branch. `design/profile-terminal-2026` is explicitly barred, even if made the default branch. PRs and ordinary pushes only validate/build artifacts. Source-SHA checks and a normal push reject a moved branch; unrelated files are never staged. No reset, rebase or force push. A push of the reviewed design branch runs read-only CI; deployment to the default branch is a separate approval step. Branch protection can require a separate repository-approved publication route.

README SVGs are images: prompts and window buttons are not interactive. GitHub cannot execute the generator or local preview JS. Theme selection uses picture/prefers-color-scheme; browser preference can differ from a manually selected GitHub theme. Image caches and scheduled-run delays may delay visible updates. Public activity is a dated snapshot, never a live presence indicator. Native pins and the native contribution graph remain separate GitHub UI.

See [research](RESEARCH.md), [validation](VALIDATION.md), [logo sources](../assets/icons/README.md) and [all changed files](CHANGED_FILES.md).

Visual inspiration: [Nyankomintsu](https://github.com/Nyankomintsu). FIGlet lettering via pyfiglet; independent SVG implementation. Font and icon sources/licenses are bundled under `assets/`.
