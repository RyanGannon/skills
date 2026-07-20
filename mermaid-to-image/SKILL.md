---
name: mermaid-to-image
description: Render Mermaid diagrams from Markdown to PNG with mermaid-cli, and embed them where Mermaid is not supported — Confluence especially. Use when a document's diagrams show as raw source in the target system, when publishing Markdown containing ```mermaid blocks to Confluence, or when asked to render, export, or convert Mermaid to images.
---

# Mermaid → image

Renderers that do not speak Mermaid show the fence contents as text. Fix that at
publish time, not in the source: **the Markdown keeps its ` ```mermaid ` fences**
so the diagram stays diffable, reviewable and editable. Only the published copy
carries images.

That split is the whole point of this skill. Rewriting the source to reference a
PNG destroys the version-controlled diagram to satisfy one downstream renderer.

## Workflow

### 1. Render

```bash
python3 scripts/render_mermaid.py \
  --input REPORT.md --outdir ./diagrams \
  --theme dark --names blackbox-probe-flow,argocd-app-of-apps
```

Pass `--names` in document order. The defaults (`diagram-1`, `diagram-2`) survive
publishing but tell a later reader nothing, and attachment names are user-visible.

The script prints a manifest with each diagram's pixel size and the
`display_width` to embed at. Keep it — the next two steps consume it.

**Completion criterion:** one PNG per mermaid block in the source, and the script
exited zero.

### 2. Look at every image before publishing

Read each PNG. A render that succeeds can still be wrong, and Mermaid fails
quietly: `classDef` styling silently dropped, long labels overflowing their node,
subgraph titles colliding.

Check what the **surrounding prose claims**. Text like "dashed borders mark the
Applications with no syncPolicy" is a direct assertion about the image — if the
dashes did not survive, the published page now contradicts itself.

**Completion criterion:** every diagram viewed, and every visual distinction the
prose refers to confirmed present.

### 3. Embed

For Confluence, read [`references/confluence.md`](references/confluence.md) — storage-format
macros, the attach-then-update order, validation, and how to re-render a page
that is already published.

Elsewhere, reference the PNGs however the target expects.

## Theme

Rendered images are **baked**. One file is served no matter what theme the reader
is using, so a dark diagram sits on a light page unchanged. Adaptive rendering is
not available — pick the theme that matches how most readers view the target, and
say so rather than leaving it implicit.

Use `--theme dark` only with an opaque dark background; the script sets one. A
dark theme on `-b transparent` puts light text on a light page and disappears.

## Chrome

`mmdc` drives headless Chrome, which is where this fails in practice. The script
resolves a binary automatically, preferring `~/.cache/puppeteer` and **rejecting
snap-packaged browsers** — snap confinement blocks reads outside home, and mmdc
passes Chrome a temp file.

If it exits with no usable Chrome:

```bash
npx puppeteer browsers install chrome
```

npm's `allow-scripts` policy blocks puppeteer's postinstall, so
`npm install @mermaid-js/mermaid-cli` can land without ever fetching a browser.
The install above is the fix.

## Re-rendering later

Editing the Mermaid source does **not** update anything already published — the
image was rendered once. Re-run step 1, then re-attach. Say this out loud when
handing over a published page, or the next edit silently diverges from what
readers see.
