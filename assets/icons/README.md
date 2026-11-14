# Original logo sources

The manifest records all 26 original GitHub badge URLs. Twenty-four logo assets were extracted directly from those badges. Matplotlib uses the existing, unchanged `assets/matplotlib.svg` supplied in this repository. XGBoost's original badge has no logo, so its icon slot is empty.

The user subsequently added Java to Languages. Its coffee-cup mark is vendored from [Devicon v2.17.0](https://github.com/devicons/devicon/blob/v2.17.0/icons/java/java-plain.svg), with the upstream [MIT license](LICENSE-devicon.txt), source URL and local checksum. The final inventory has 27 technologies and 26 actual logo assets (25 SVGs and one PNG).

No function/scatter/cat/tree stand-ins or generic fallback logos are used. SVG geometry and internal transforms are preserved; all paints use the current terminal foreground. Matplotlib's plotting surface takes the cell background so its polar grid stays visible. Seaborn's PNG bytes are unchanged and embedded as a data URI; an SVG luminance mask renders its details in the cell foreground, with transparent white areas. This keeps the genuine marks inside the lavender/red palette in both themes, including ANSI-background badges. Every local source is checked against its SHA-256 in `manifest.json` before generation. No runtime network request is made.

Brand marks belong to their respective projects; original source URLs are retained in the manifest. These assets identify the technologies already declared by the user and do not imply sponsorship.
