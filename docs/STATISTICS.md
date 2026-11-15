# What the profile numbers measure

The language inputs were independently fetched without authentication on **2026-11-14 at 14:06 UTC** and matched the original delivered snapshot byte for byte. The current machine-readable inputs, fetch time and provenance are in [`data/github.json`](../data/github.json). This page documents that dated audit; the JSON is the source for subsequent renders.

## Repository languages

GitHub's [language endpoint](https://docs.github.com/en/rest/repos/repos#list-repository-languages) returns bytes of code classified by [Linguist](https://github.com/github-linguist/linguist), taken from repository default branches. The generator sums those bytes across **owned public non-fork repositories**, excluding the profile repository and LuminaRead.

| Included repository / direct API evidence | Language bytes |
| --- | ---: |
| [leetcode](https://api.github.com/repos/Fiudeus/leetcode/languages) | Python 2,667; C++ 581 |
| [morsegram](https://api.github.com/repos/Fiudeus/morsegram/languages) | Python 25,199 |
| [mutegram](https://api.github.com/repos/Fiudeus/mutegram/languages) | Python 3,281 |
| [password-manager](https://api.github.com/repos/Fiudeus/password-manager/languages) | Python 92,256 |
| [samsung-LogiRisk](https://api.github.com/repos/Fiudeus/samsung-LogiRisk/languages) | Python 109,443; Jupyter Notebook 5,616; Dockerfile 644 |
| [wallpaper-menu](https://api.github.com/repos/Fiudeus/wallpaper-menu/languages) | Shell 1,377 |

| Language | Bytes | Share |
| --- | ---: | ---: |
| Python | 232,846 | 96.590947% |
| Jupyter Notebook | 5,616 | 2.329672% |
| Shell | 1,377 | 0.571218% |
| Dockerfile | 644 | 0.267149% |
| C++ | 581 | 0.241015% |
| **Total** | **241,064** | **100%** |

The four excluded repositories were `Fiudeus` (profile), `bf` (fork), `The-Knot` (fork) and `LuminaRead` (fork and explicit exclusion). This explains the difference between 10 public repositories and six inputs to the language chart. The large Python projects have more influence than small exercises. No forked Java, TypeScript or Rust code enters this denominator.

These figures describe **all classified code in those repositories**. They do not attribute individual lines to Artem, measure skill, indicate time spent, or count only the last year. The chart displays the leading three languages and an `other` bucket, always using the full denominator; one decimal place is shown. Its character bar uses largest-remainder allocation, so a very small language can round to zero visible cells without changing its percentage.

Schema 2 retains each admitted repository and its language bytes in `language_repositories`. Loading and saving verify that the per-repository inputs sum exactly to `languages`; malformed, duplicate or inconsistent data is rejected. No invented sample statistics are used for delivered images.

## Contributions and commits

The contribution calendar and commit count are different metrics. Contributions include eligible commits, PRs, issues and other [GitHub-counted activity](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference). The native contribution graph supplies exact public-visible daily counts for the rolling year. The displayed best streak is within that period.

Commits use the exact GraphQL `totalCommitContributions` field only after its daily calendar agrees with the public calendar. Anonymous GraphQL was unavailable during local verification, so `commits` remains null and the scene says `unavailable`. Rounded HTML percentages, commit-search counts and subtraction from the contribution total are not replacements. Actions supplies its built-in token for authenticated acquisition; a failed or unverified result remains unavailable.

Repositories count all owned public repositories, including forks. Stars count received stars on admitted source repositories. PRs/issues count authored public items created in the rolling period. Account age, followers and following come from public user metadata.

## Last public activity

The generator programmatically reads the **general [public-events feed](https://docs.github.com/en/rest/activity/events#list-public-events-for-a-user)**. It considers push, pull request, issue, review, star, creation and other event types together; it does not hard-code a star action or a date. It chooses the greatest valid `created_at` with `public == true` and an actor matching Fiudeus. Private/foreign/bot entries, malformed dates, events before account creation and future timestamps are excluded. Only the UTC timestamp and source are retained.

`Last public activity` is the latest event GitHub exposed when the snapshot was fetched. It is **not last login or online presence**. GitHub limits the feed to up to 300 events from the last 30 days and can delay events by 30 seconds to six hours. Failed/empty acquisition yields an unavailable value. Scheduled regeneration and GitHub image caches add their own delays.

The reference profile's `Last login` is generated with [`date.today()`](https://github.com/Nyankomintsu/Nyankomintsu/blob/main/scripts/cards.py), so copying that label would give build time the wrong meaning. This profile uses event data instead.

Local generation, refresh and approved default-branch automation are described in [DEVELOPMENT.md](DEVELOPMENT.md).
