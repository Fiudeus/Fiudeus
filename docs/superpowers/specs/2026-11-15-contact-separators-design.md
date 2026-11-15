# Contact and ANSI separators

The user approved two small separators for the three existing terminal windows:
contacts after home, then a palette after fastfetch. They supplied
Telegram, VK and Discord accounts and requested Nyankomintsu's badges as the main
visual reference. This is an addition to the existing approved composition.

## Approach

Use three separate local SVG badges, following the reference's 28px height,
7px corners, colored leading segment and 13px bold JetBrains Mono outlines.
Each has its authentic service logo and the service name; account names appear
in accessible descriptions/link titles. The Discord ID is only in its URL.
The badges form one centered, wrapping HTML paragraph between home and fastfetch.
This preserves independent clickable links in GitHub's image-safe README.

The second separator is a centered 250 × 28 SVG with eight separated terminal
block samples. Its colors come directly from each theme's existing `banner`
array: the exact lavender/pink/red inks in the large FIUDEUS lettering. It has
no window chrome or caption. After seeing the first local preview, the user
rejected the generic two-row ANSI sample and the VK pink; the final palette uses
only actual profile colors. Contact caps use three separate theme tokens to form
a cool progression: Telegram lavender, Discord violet, VK blue. Discord and VK
remain visually distinct in both themes.

Alternatives discussed were plain terminal links, informational badges repeating
the fastfetch content, and additional profile decorations. The user chose contact
badges and a palette to give the three windows different visual pauses.

## Constraints

- Keep all existing scenes, stack, statistics, animation and wide README selection.
- Support both color schemes; the new separators are static.
- Reuse the local typography/SVG infrastructure; no CDN or new dependencies.
- Vendor Simple Icons' actual marks, CC0 license and immutable source/checksums.
- Add generated assets to the exact workflow artifact allowlist.
- Work only on `design/profile-terminal-2026`; no main, merge, PR or settings changes.

## Verification

Generate every asset; validate XML, resource resolution and file budgets; check
offline reproduction and workflow safety. Render and inspect both themes and
check the complete README at desktop, scaled and phone viewport widths, including
contact targets and the existing animation/reduced-motion regressions.
