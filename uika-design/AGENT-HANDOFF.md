# Implement Uika's visual system

Use this as a design implementation brief within your own project's existing instructions. It supplies no agent permissions or estate governance.

## First actions

1. Run `node verify.mjs` in this directory with Node.js 22+ and inspect `preview.html`.
2. Read `PROVENANCE.json`: the canonical CSS owns token values. The starter styles are optional recipes.
3. Inspect your project's existing styles and components. Integrate into that stack without replacing project configuration or unrelated rules.
4. Copy these two CSS files into an ordinary project style directory, then import `uika-canonical.css` before `starter.css`. Do not replace your agent instruction files with this brief.

```html
<html lang="en" data-face="sumimi">
  <head>
    <link rel="stylesheet" href="styles/uika-canonical.css">
    <link rel="stylesheet" href="styles/starter.css">
  </head>
  <body class="uika-surface">
    <main class="uika-shell">
      <h1 class="uika-title">Your product name</h1>
      <section class="uika-panel">
        <h2>Your section</h2>
        <p>Your actual content.</p>
      </section>
    </main>
  </body>
</html>
```

## Theme contract

Set `data-face="sumimi"` on the document root for the warm light public surface; use `data-face="doloris"` for a dark workspace. With no attribute, the canonical CSS defaults to Doloris. A root attribute is the supported integration pattern. The canonical `:root` variables are global: use an iframe/shadow-specific adaptation if your host needs isolated themes, and validate that adaptation separately.

Public pages default to sumimi; interior workspaces default to Doloris. An optional explicit theme switch may change `document.documentElement.dataset.face`. Theme preference does not require network access, storage, or authentication.

Use variable names directly in CSS. For another UI toolkit, read `tokens.json`'s `themes.doloris.resolved` or `themes.sumimi.resolved`; keys retain the CSS `--` prefix and values retain units and font stacks. Both maps are complete. Do not use the override-only map as the whole light theme.

| Role | Token |
| --- | --- |
| Page depth / normal background | `--bg-deepest` / `--bg-ground` |
| Panels / hover layers / input | `--bg-panel` / `--bg-panel-2` / `--bg-input` |
| Borders | `--line-subtle`, `--line`, `--line-strong` |
| Primary accent | `--gold`, `--gold-bright`; dim/glow for decoration |
| Information | `--lavender` |
| Readable body / emphasis / secondary copy | `--text`, `--text-bright`, `--muted` |
| Warning or negative / success | `--lining` / `--sage` plus explicit text or icons |
| Special ornamental trim | `--marigold`; `--wine` for stage accents |
| Light-face secondary ornament | `--sumimi-lime`; restrict use to sumimi |

`--slate`, `--gold-dim`, wine, and lime are not automatically suitable for small text. Keep body text on the normal text tokens. Canonical accents do not guarantee accessible contrast for every foreground/background combination; the supplied starter uses readable text with accent borders for status labels.

## Type and component grammar

- Cinzel is the display face for restrained major headings; Outfit is brand/body type; JetBrains Mono is for code, coordinates, tabular data, and compact labels. Use the supplied serif/sans/monospace fallbacks until fonts are self-hosted.
- Canonical radii: 4px, 6px, 12px. Canonical motion: 150ms, 300ms, 500ms with `--ease-out`. Respect reduced motion.
- The existing grammar is editorial and ledger-like: thin borders, modest rounded panels, compact chips, pills, numbered steps, clear rows. Keep ornamental Latin, stars, or stage imagery optional; functional copy stays plain.
- `starter.css` adds **recipe values**, not new canon: spacing, readable heading sizes, manual-derived sheen/drop shadows, and responsive layout. It prefixes classes with `uika-`. Its recipe custom properties use `--uika-` to distinguish them from canonical tokens.
- Preserve existing product names, real status semantics, and navigation behavior. Avoid introducing estate names, personal workflows, artwork, or theatrical copy into your product without its owner's request.

## Acceptance criteria

Check both themes at 375px and 1440px widths. Confirm no page-level horizontal overflow; ledgers may scroll inside their container. Verify keyboard focus, semantic headings, labels, theme-button state, contrast for actual content, reduced motion, and touch target sizes. Do not rely on color alone for status.

Verify browser-computed variables match the JSON values; verify the exported canonical CSS hash still matches the provenance entry. Report separately what was tested in a browser, what was statically checked, and what remains untested in your application. Preview verification is not a full product accessibility audit.

No Uika CLI, MCP service, API key, media library, external font request, or agent-config installation is required.
