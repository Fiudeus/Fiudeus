# Reference and project research

Research completed before implementation on 2026-11-14. Read access only; no files from unlicensed reference source were copied into the implementation.

## Nyankomintsu

Repository tree examined: [`4899de41ce46ff1149b945067eeb428960e155c2`](https://github.com/Nyankomintsu/Nyankomintsu/tree/4899de41ce46ff1149b945067eeb428960e155c2). The rendered header, fastfetch, activity and footer were inspected in both palettes. Source copies and research rasters are local ignored scratch under `.local/research`.

| Source | Observations |
| --- | --- |
| [`scripts/term.py`](https://github.com/Nyankomintsu/Nyankomintsu/blob/4899de41ce46ff1149b945067eeb428960e155c2/scripts/term.py) | FontTools outlines, per-glyph definitions and fixed cells eliminate visitor-font drift. The original fetches several fallback fonts; this project vendors only its required font inputs. |
| [`scripts/cards.py`](https://github.com/Nyankomintsu/Nyankomintsu/blob/4899de41ce46ff1149b945067eeb428960e155c2/scripts/cards.py) | Shared width, window framing, spacing and animation timelines make independent pictures read as one composition. Static visibility is deliberately defined. |
| [`scripts/svgkit.py`](https://github.com/Nyankomintsu/Nyankomintsu/blob/4899de41ce46ff1149b945067eeb428960e155c2/scripts/svgkit.py) | Small document/definitions/CSS primitives keep scenes separate from SVG infrastructure. |
| [`scripts/ascii_art.py`](https://github.com/Nyankomintsu/Nyankomintsu/blob/4899de41ce46ff1149b945067eeb428960e155c2/scripts/ascii_art.py) | FIGlet gives coherent lettering; character-based scenes communicate personality without raster illustrations. The final Fiudeus design uses pyfiglet and no character mascot, per user feedback. |
| [`scripts/github_stats.py`](https://github.com/Nyankomintsu/Nyankomintsu/blob/4899de41ce46ff1149b945067eeb428960e155c2/scripts/github_stats.py) | API-derived figures are separate from composition. This implementation adds pagination, explicit public scope, null values and validated snapshots. |
| [`scripts/themes.py`](https://github.com/Nyankomintsu/Nyankomintsu/blob/4899de41ce46ff1149b945067eeb428960e155c2/scripts/themes.py) | Catppuccin light/dark semantic tokens preserve hierarchy. Fiudeus narrows the accent system to lavender and red. |
| [`config.toml`](https://github.com/Nyankomintsu/Nyankomintsu/blob/4899de41ce46ff1149b945067eeb428960e155c2/config.toml) | User-editable copy/commands and theme-independent scenes make maintenance practical. |
| [workflow](https://github.com/Nyankomintsu/Nyankomintsu/blob/4899de41ce46ff1149b945067eeb428960e155c2/.github/workflows/profile.yml) | Scheduled regeneration commits generated images. Fiudeus separates read-only artifact generation from explicitly enabled publishing. |

The visual lesson is consistent metrics and restrained hierarchy: a generous but repeated inset, one baseline rhythm, calm surfaces and a large legible banner. Following the user's visual review, the final profile uses compact centered title bars and standard window controls, with no bottom status bars. A solid ANSI foreground ramp makes the FIGlet banner more colorful, while shell tokens, technologies and numbers share lavender, pink and red accents. There are no falling particles, gradient surfaces, pets or duplicate calendars.

## Verified profile facts

The [original Fiudeus README](https://github.com/Fiudeus/Fiudeus/blob/655c0983d99305a5d26ddd092306eff90969b725/README.md) supplied Artem's name and declared technologies. The user supplied Applied AI at Kursk State University, Python, ML/data/desktop/Linux work, and current learning topics. All seven original categories and all original technologies are retained. The user subsequently selected the role `Data Scientist` and Languages order `Python, Java, C++, SQL, Bash`, adding Java for 27 technologies overall. Other category orders remain unchanged. The user also added Deep learning and Mathematics. It does not add employment, awards, model performance or claimed expertise levels.

## Projects

The following research was completed for the initial brief. The user later chose native GitHub pins, so the final README does not render a projects window or duplicate this list.

| Repository and inspected revision | Source checked | Presentation |
| --- | --- | --- |
| [samsung-LogiRisk](https://github.com/Fiudeus/samsung-LogiRisk/tree/3152f5482e0f4fae0318330a3450a7c3794cb20c) | README, `src/main_pipeline.py`, `src/spark_features.py`, requirements and repository tree | Fleet incident risk, Spark feature engineering, model ensemble; PySpark, Airflow, CatBoost/XGBoost and PostgreSQL. No unverifiable model scores or business outcomes. |
| [password-manager](https://github.com/Fiudeus/password-manager/tree/c68ae01988955e47608f4992051da88eb4d16088) | README, `main.py`, requirements, desktop/core/tests tree | Local password vault with PySide6 UI and CLI; SQLAlchemy/SQLite, Fernet and pytest. No security-audit claim. |
| [morsegram](https://github.com/Fiudeus/morsegram/tree/53b34005e2f77aaa99a8f97e5949a2fc120e5f5c) | Entire `morse_code.plugin`, README | exteraGram send hooks, Morse/NATO codecs, Latin/Cyrillic support and message-menu decoding. The source credits `@fiudeus, @ntfepsilon`, so it is explicitly co-authored. No project demo is rendered in the final profile. |
| [mutegram](https://github.com/Fiudeus/mutegram/tree/55aa12bcaafc4b18fe5a695458ff7830bff08d58) | Entire `mutegram.plugin`, README | Configurable vowel masking before send. The default English example `hello world` → `h*llo w*rld` follows the implementation. It is not an audio-muting application. |

LuminaRead is excluded from presentation and language/star aggregation as requested. No other project is promoted without source inspection.

## Upstream assets and platform references

- [JetBrains Mono v2.304, pinned source](https://github.com/JetBrains/JetBrainsMono/tree/cd5227bd1f61dff3bbd6c814ceaf7ffd95e947d9); unmodified font files, OFL and SHA-256 hashes are bundled.
- [pyfiglet](https://github.com/pwaller/pyfiglet): ready-made FIGlet lettering; `ansi_shadow` is selected in TOML. Its packaged font attribution is retained in the dependency.
- [GitHub's documented picture/theme pattern](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/quickstart-for-writing-on-github) supports README source selection with `prefers-color-scheme`.
- [Truststore documentation](https://truststore.readthedocs.io/en/latest/) describes explicit native SSL contexts. This project uses that API for verified Windows/Linux HTTPS, without global injection or verification bypass.
- [GitHub scheduled events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) document the default-branch and timing constraints.

The final logo sources are the user's original badge images, plus the existing Matplotlib SVG. See [the asset manifest](../assets/icons/manifest.json) and [source notes](../assets/icons/README.md). XGBoost's original badge has no icon; no substitute is shown.

## Second reference review and statistics audit

On 2026-11-14 the live profile, README, config, cards, statistics source and workflow were fetched again, and the current header/neofetch SVGs were rasterized and inspected in both themes. Header blobs: dark `3606039e4c805823f5bf51f6134ccb7f369f7ecc`, light `121cbe619997ed3b935f4f1646f3901052632fb7`; neofetch blobs: dark `c75e299cf0303b594d51b879371c6a8a53fe8c52`, light `9ba4c27a42a0a9357f131c52cc43cb885949c603`. The useful details remain the shared window metrics, restrained title bar, clear CLI field labels and data refresh separated from rendering.

The reference's `Last login` comes from `date.today()` in `cards.py`, not GitHub presence. Fiudeus instead acquires the general public-events feed and labels its latest valid event `Last public activity`. The workflow prepares automatic refresh on the default branch after approved deployment; the design branch cannot publish.

The palette review also found that original multicolor Matplotlib/CatBoost/Seaborn assets broke the foreground system. Their actual marks are retained and now render with terminal ink; Seaborn uses an SVG luminance mask over its unchanged PNG. The language chart was independently rechecked against every repository's `/languages` endpoint. See [the full byte breakdown and metric definitions](STATISTICS.md).
