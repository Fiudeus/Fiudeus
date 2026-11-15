# Validation evidence

Local verification on 2026-11-14, branch `design/profile-terminal-2026`, against baseline `655c0983d99305a5d26ddd092306eff90969b725`. The user subsequently authorized committing and pushing this design branch. Merge, PR, main-branch changes, manual hosted workflow dispatch and settings changes remain outside that authorization. Original `assets/matplotlib.svg` and `assets/plchldr` are preserved.

## Contact and palette update — 2026-11-15

The user approved two separators between the three windows and supplied all three
contact targets. After reviewing both local themes and the final contact-color
progression, the user authorized committing and pushing this addition to
`design/profile-terminal-2026`. Integration into main remains a separate decision.

- 69 Python tests pass, including contact-link/order integration and preservation
  of existing outputs when URL or preview configuration fails. The preservation
  regression first reproduced partial replacement, then passed after all HTML
  previews were prepared before the write phase.
- All 36 SVGs validate: 24 profile assets and 12 toolbox comparisons; 16 README
  resource references resolve locally. All 42 generated files reproduce
  byte-for-byte. Static generation also validates.
- Browser QA uses Edge 157.0.4341.60 with both themes/motion preferences at
  900px/DPR 1, 600px/DPR 1.5 and 375px/DPR 1. The three windows retain their
  900px source composition; four separator images retain native 28px height.
  All three configured contact targets are correct and there is no horizontal
  overflow. Existing typing, static-frame and 20-case border regressions pass.
- Both full-profile PNGs were visually inspected. After the user's feedback,
  the generic 16-color sample was replaced by eight exact `theme.banner`
  lavender/pink/red colors, displayed as separate terminal blocks. VK changed
  from red to a cool blue accent. The three contact caps now form a distinct
  lavender → violet → blue progression in both themes. Service labels have no repeated usernames;
  Discord's numeric ID appears only in the target URL.
- The three genuine Simple Icons marks are bundled with pinned source revision,
  SHA-256 checksums and CC0 license text. No network assets or new dependencies
  were added to generation. New separators are static.
- actionlint passes. All 13 local workflow safety checks pass against the exact
  expanded 43-file artifact; publish gates and source-SHA protections are
  unchanged. No hosted refresh workflow was manually dispatched.
- Independent review found one partial-write issue, fixed and verified as above;
  no actionable findings remain.
- All 16 existing terminal SVGs and `data/github.json` are byte-for-byte unchanged.

## Separator spacing — 2026-11-15

The later separator-spacing regression was reproduced in the public GitHub DOM:
standalone terminal pictures gave 6px above the contacts and 22px below. Wrapping
all terminal pictures in the same paragraphs as the separators gives 22px on both
sides. Browser QA now uses GitHub's baseline image alignment and bottom-only
paragraph margins, and asserts equal gaps for both separators in all 12 cases.
The assertion first failed on the original 6px/22px layout.

## Initial profile checks

| Check | Observed result |
| --- | --- |
| Unit suite | 66 passed: 42 stats, 13 generation, 8 renderer, 3 original-logo tests |
| Generation/validation | 16 profile SVGs (including four still home variants) + 12 toolbox comparison SVGs; all XML, internal references, cell bounds, reduced-motion defaults, size budgets and eight wide README image paths valid |
| Reproducibility | 34 generated files byte-identical in an independent output directory |
| Static mode | Complete static variants generated and validated |
| Real refresh | Full tokenless production fetch succeeded with verified TLS; schema-2 snapshot atomically saved; previous schema-1 snapshot backed up locally |
| Browser QA | Chromium/Edge 157.0.4341.57; both palettes at 900px and 375px, with and without reduced motion; correct sources and no horizontal overflow |
| Animation frames | Distinct command states at 0, 900 and 2500ms, with complete final output |
| Reduced motion | All 28 SVGs checked; complete output and in-bounds scene glyphs/logos; README still-home screenshots pixel-identical 900ms apart; still assets have no animations even without a reduced-motion preference |
| Preview controls | All three toolbox styles switch correctly; compact/light comparison assets load |
| Workflow | actionlint 1.7.12; 11 shell blocks passed bash syntax; 13 local safety tests include 288 publishing-gate combinations and an explicit ban on design-branch publishing |
| Independent review | No actionable findings in current SVG/logo/UI/workflow review or schema-2 data/events review |
| Whitespace | git diff --check passed |

Visual review covered dark/light desktop and compact layouts, all three toolbox designs, the selected outline-panel default, one-line greeting, removal of the projects window, complete requested stack and Mathematics. Latest user edits are `Data Scientist` and Languages ordered `Python, Java, C++, SQL, Bash`, for 27 technologies. The reference's current header/neofetch were fetched and inspected again in both themes before this revision.

The logos were corrected against the actual original badges: 24 badge images plus the original local Matplotlib SVG. The later Java addition uses Devicon v2.17.0's authentic coffee-cup mark, with source and MIT license retained. XGBoost has no invented icon. Every source asset is checksummed. All SVG paints now use terminal ink; Matplotlib retains a cell-background plotting surface. Seaborn's unchanged PNG is embedded locally and tinted through an SVG luminance mask. SVG symbols have internal references only. Both palettes were rasterized and visually inspected. After the scaled-border fix below, the largest rendered SVG is 264,096 bytes, below the 400 KB per-file budget.

The asset tests protect the seven category names, all 27 requested technology names/capitalization/order, icon cell widths, background cell geometry, missing XGBoost icon, actual SciPy SVG, inline Seaborn PNG signature and readable plain-text fallback.

A reduced-motion regression check first failed when the opening SVG was embedded as an image: HTML media emulation reported reduce, but the image still animated. Four explicit still variants and picture-media selection fixed that case. The same browser check now passes with pixel-identical frames. CSS reduced-motion support remains in every SVG for direct opening as well.

## Genuine data and limitations

Delivered snapshot: 2026-11-14 14:19:15.324409 UTC, schema 2, period 2025-11-15–2026-11-14. It contains 10 public repositories, 1 received source-repository star, 1 follower, 7 following, 20 authored public PRs, 12 authored public issues and 453 contributions across 365 complete days. Current streak 0, best within period 18.

An independent fresh audit of all 10 repository language endpoints exactly matched the aggregate: six admitted repositories, 241,064 bytes, including 232,846 Python bytes (96.590947%). Per-repository provenance is preserved in the delivered JSON and checked against the aggregate. The scene labels bytes/public repository scope and shows 96.6%, 2.3%, 0.6% and 0.5% other; it does not normalize only the leading three languages. See [STATISTICS.md](STATISTICS.md).

The general tokenless public-events feed supplied `last_public_activity = 2026-11-14T11:22:00Z`. This came from programmatic acquisition, not a configured date or a single hard-coded action. Tests cover mixed push/PR/issue/review/star/create/unknown event types, pagination, foreign/private/future/malformed entries, account/fetch bounds and unavailable provenance. It is labeled public activity, never last login or online status.

Commits remains null in the tokenless snapshot. Exact verified GraphQL handling is implemented/tested but was not exercised live without a token. No credentials were obtained from a credential store and no totals were guessed.

At the time of the local verification recorded here, hosted Actions execution had not yet been observed. The subsequently approved design-branch push triggers read-only CI. The prepared workflow automatically refreshes only after approved deployment to the default branch; its design-branch write job is barred and no extra repository variables are needed. Static analysis, local build and mocked publication-boundary checks passed. Local diagnostic reports are retained under ignored `previews/qa` and `.local/workflow`.

## Scaled-border regression, 2026-11-15

The reported missing `Familiar with` bottom border was reproduced with sharp/librsvg when rendering the 900px SVG at 840px. The SVG paths existed and Chromium's ordinary geometry checks passed, but a 1.05-unit `crispEdges` stroke scaled below one pixel and vanished during rasterization. Other frame edges could disappear for the same reason.

Procedural single-line box drawing now uses `stroke-width="1"` and `vector-effect="non-scaling-stroke"`, retaining crisp edges and the original cell geometry. The new pixel regression first failed against the original output (zero bottom-border pixels at 840px), then passed after regeneration. It checks the bottoms and both sides of all seven panels in 20 dark/light desktop/compact width cases. The 66 Python tests, 28-SVG validation, existing browser/motion checks and offline reproducibility also pass. The corrected `Familiar with` frame was visually inspected in both themes at the failing scale. No profile data or content was changed.

## Profile layout selection, 2026-11-15

The original README selected 540px compact SVGs at `max-width: 600px`. A narrow logical viewport with a higher display scale could therefore show the long, large-letter composition on a physically large profile card. The exact behavior was reproduced on the public GitHub profile at 600px/DPR 1.5: the first image used a 540px source and fastfetch/toolbox were stacked vertically.

README sources now always select the 900px composition, with only theme and motion alternatives; compact layouts remain local preview options. The new regression first failed on the old compact source, then passed for all 12 theme/motion/viewport combinations, including 600px/DPR 1.5. All 66 Python tests and 28-SVG validation pass. Static frame comparisons remain exact at integer DPR and allow a maximum per-channel difference of 1/255 at fractional DPR, where 12 static channel values were observed to round by one unit.

The local README was also previewed in the actual public GitHub profile and repository DOM at 1440px/DPR 1 and 600px/DPR 1.5, without changing repository/account state. All three images retained 900px natural width and the wide composition in both hosts. At the narrow profile width, fastfetch's rendered height fell from 565.95px to 233.67px and the toolbox from 1294.03px to 405.77px. This was a browser-only preview; it did not deploy the change to main.
