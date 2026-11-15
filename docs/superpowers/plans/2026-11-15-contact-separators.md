# Contact Separators Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement the tasks inline. The user has approved the design and requested implementation.

**Goal:** Add clickable contact badges and an ANSI palette between the existing three windows.

**Architecture:** A small `scripts/badges.py` module builds eight extra SVGs using Canvas/Grid and locally vendored service marks. The generator, README, preview, rendering and workflow include those assets without changing the terminal scenes.

**Tech Stack:** Existing Python, fontTools, SVG, GitHub Actions; optional sharp/Playwright QA.

**Spec:** `docs/superpowers/specs/2026-11-15-contact-separators-design.md`

## Global Constraints

- 28px separator height; 13px outlined JetBrains Mono labels; both themes.
- Telegram: `https://t.me/fiudeus`; VK: `https://vk.ru/businessqoose`.
- Discord: `https://discord.com/users/735903901622206575`; show only the service name.
- Retain the 900px README composition and all current content/motion behavior.
- No main changes, merges, PRs or repository settings changes.

## Review Focus

- Click targets belong to the supplied accounts, including the numeric Discord URL.
- Both themes select local assets; contact badges retain their natural size.
- Narrow viewports wrap contacts and never overflow or select compact scenes.
- Publishing accepts all new generated assets and still rejects unrelated files.
- The renderer and local viewer show the same scene/separator order as README.

## Task 1: Local badge assets and generation

Files: `config.toml`, new `scripts/badges.py`, new `assets/contacts/`,
`scripts/generate.py`, `scripts/validate.py`, `tests/test_generation.py`.

- [x] Add a generation integration regression for themed resources, supplied click targets and separator order; run it and observe the missing separators.
- [x] Vendor the three genuine logos/license with source SHA and checksums.
- [x] Add contact settings and reuse each theme's eight `banner` colors; implement `contact_badge(config, service, theme)` and `ansi_palette(config, theme)` returning Canvas. The user rejected the first generic ANSI palette and chose a cool VK accent after the first preview.
- [x] Generate eight assets; embed linked pictures in centered paragraphs; update validation to 24 profile + 12 comparison SVGs and 16 README references.
- [x] Run the Python suite and generator/validator.

## Task 2: Preview, workflow and browser integration

Files: `scripts/generate.py`, `scripts/render.mjs`, `scripts/browser-qa.mjs`,
`.github/workflows/profile.yml`, `docs/DEVELOPMENT.md`.

- [x] Insert the separators into the preview and PNG composition at native size.
- [x] Extend README browser checks to verify the real contact anchors, theme sources, native badge sizes, wide scenes and no overflow at all existing viewport/DPR cases.
- [x] Add the eight SVGs to the workflow's exact 43-file allowlist; run actionlint and actual staging safety tests.

## Task 3: Visual verification and delivery

Files: generated `profile/`, README, preview HTML; `docs/VALIDATION.md`, `docs/CHANGED_FILES.md`.

- [x] Render and visually inspect full dark/light compositions and separator crops; refine if needed.
- [x] Run browser QA, full Python suite, XML validation, static generation and byte-for-byte reproduction.
- [x] Update documentation/inventory and inspect the final diff; obtain an independent review.
- [x] Report previews, checks and branch status. The user reviewed the final local previews and authorized commit/push to the existing design branch. Preserve the prohibition on main changes.
