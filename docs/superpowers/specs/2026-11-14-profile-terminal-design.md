# Fiudeus terminal profile: final design

## Authority and intent

Prepare a complete English GitHub profile in `design/profile-terminal-2026`. After reviewing the local result, the user authorized commit and push of that branch; merge, PR, main changes and settings updates remain out of scope. Preserve the original assets. The profile should resemble an expressive real terminal, with lavender/red accents and maintainable Python/SVG/Actions architecture.

User follow-ups override the initial sketch: use existing FIGlet lettering; no pet, logout screen, tmux footer, custom calendar or projects window. Use native pins and contribution graph. Keep fastfetch statistics. Center the window titles, use compact standard controls, add richer foreground colors and shorten the greeting to one line.

## Research and composition

Read the requested Nyankomintsu source/config/workflow before implementing; inspect rendered dark/light output. Write independent implementation. Preserve project-source research in RESEARCH.md even though the user later removed project presentation.

Three windows:
- Home: actual last public-event timestamp, existing pyfiglet ANSI Shadow, wider desktop spacing, solid lavender/pink/red foreground ramp, single Hello/Artem line and typed command.
- Fastfetch: identity, Python role, study/campus/focus and real public GitHub metrics/language bytes. Explain stars plainly; label the language scope/bytes, show tenths and `other`, and remove the redundant snapshot footer.
- Toolbox: all seven original categories and technologies, plus the user's Java addition. Latest Languages order: Python, Java, C++, SQL, Bash (27 technologies overall). Role: Data Scientist. Other category orders are unchanged. The chosen design is Unicode outline panels. Preserve tree and ANSI-background badge alternatives in local comparison previews. Original learning topics plus user-requested Deep learning and Mathematics.

Desktop is 900px/92 cells, compact 540px/54 cells. Shared title bars and baseline metrics; no lower status strips. All layout is cell-based, including two-cell logo slots.

## Rendering

Vendor JetBrains Mono Regular/Bold v2.304 with OFL/checksums. Outline only used text glyphs and reuse definitions. Use connected cell geometry for blocks/lines and ANSI-style background cells. Reject controls, unsupported glyphs and overflow; handle NFC and combining accents.

Copy authentic logo assets from the user's original badges, plus the existing local Matplotlib SVG. Keep source URLs/hashes. No generic substitutes; XGBoost has no icon. Embed local SVG symbols and the unchanged Seaborn PNG. All marks use terminal ink; Matplotlib keeps a background-colored plotting surface and Seaborn uses an SVG luminance mask. No external font/icon dependency. Text fallback omits icon markers while retaining names and alignment.

Motion is one-shot typing/output reveal and discrete cursors. Complete defaults remain visible with reduced motion and static rendering. Four dedicated still home variants are selected by README picture media and the local viewer, in addition to the SVG CSS fallback. No animated metrics.

## Data and automation

TOML owns copy, full stack, learning, palette and selected toolbox style. A validated schema-2 real snapshot allows deterministic offline generation; refresh is explicit, bounded and atomic with verified TLS. Public scoping, per-repository language byte provenance, pagination and unavailable values are explicit. Verified optional GraphQL supplies commit counts; no fabricated numbers. Last public activity comes from all public-event types, filtered by actor and valid timestamp. No build date is passed off as last login or presence.

Read-only CI validates and checks reproducibility. Schedule/manual runs upload temporary artifacts. After approved deployment to the default branch, its separate publishing job refreshes generated data/images automatically with the built-in token. The design branch is explicitly forbidden from publishing. Deployment to the default branch, manual hosted dispatch and settings changes require separate authorization.

## Acceptance

Generate 16 main SVGs (including four still home variants) and 12 comparison SVGs in both palettes/widths; validate XML/references and resources; inspect PNGs; exercise real browser frames/reduced motion, pixel-identical still images and selector behavior; test the user-requested stack, logo integrity, Unicode/bounds and real-data errors. Deliver source, previews, run instructions, architecture, animations, evidence, limits and a complete file inventory.
