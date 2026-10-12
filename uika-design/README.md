# Uika design handoff

Prepared 2026-10-11 for the owner's friend and their coding agent.

Start with **AGENT-HANDOFF.md**. Open **preview.html** directly in a browser for a working local example; it has no external requests. With Node.js 22 or newer, run `node verify.mjs` from this directory to verify the package.

| File | Purpose |
| --- | --- |
| uika-canonical.css | Exact source token snapshot: dark Doloris defaults and light sumimi overrides |
| tokens.json | Every token, original aliases, and fully resolved values for both themes; plain JSON, not a DTCG interchange schema |
| starter.css | Namespaced, optional component recipes adapted from Uika's manual |
| preview.html | Responsive example, theme switch, panels, chips, status labels, input, and ledger |
| AGENT-HANDOFF.md | Integration instructions and acceptance criteria for the receiving agent |
| PROVENANCE.json | Source-relative paths, hashes, authority, and export scope |
| MANIFEST.sha256 | SHA-256 checksums for every other file in this package |
| verify.mjs | Read-only verifier; uses only Node built-ins |

The export includes the core web design system. Uika also has figure, explainer, PC-98, and keynote tooling; those separate toolkits and reference collections are outside this package. There are no artwork, portrait, voice, music, font binaries, persona records, private estate settings, or agent configuration files here.

The owner's request authorizes this particular handoff. It does not promote the upstream supply catalog asset or provide rights to third-party character art, branding, or media. The visual inspiration is Misumi Uika's dual public/stage identity; the package delivers color/type conventions and implementation recipes, with neutral product copy. No general third-party rights clearance is claimed.

This is a snapshot. To refresh, obtain a new verified export from the owner. Do not merge unrelated estate files into it. Keep source tokens intact and place project-specific overrides after them.

Fonts are referenced by family name only: Cinzel, Outfit, JetBrains Mono. The preview works offline with system fallbacks. For closer fidelity, separately obtain appropriately licensed font files and self-host them in the receiving project; this package does not download them.
