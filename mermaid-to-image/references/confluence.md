# Publishing rendered diagrams to Confluence

Confluence Cloud has no Mermaid renderer. A ` ```mermaid ` block posted as a code
macro shows raw source. Replace each block with an attached PNG.

## Storage format

An attached image is referenced by filename, not URL:

```xml
<ac:image ac:align="center" ac:width="420">
  <ri:attachment ri:filename="blackbox-probe-flow.png" />
</ac:image>
```

`ac:width` is the **display** width. Use `display_width` from the render
manifest — the render is 2× so the image stays crisp on high-DPI screens while
displaying at its true size.

## Converting the Markdown

Map mermaid fences to image placeholders while stashing every other fenced block
for the code macro. Stash before the Markdown→HTML pass so raw code reaches CDATA
unescaped:

```python
MERMAID_IMAGES = ["blackbox-probe-flow.png", "argocd-app-of-apps.png"]
MERMAID_WIDTHS = [420, 760]

code_blocks = []
mermaid_seen = 0

def _stash(mo):
    global mermaid_seen
    lang = (mo.group(1) or "").strip()
    if lang == "mermaid":
        idx = mermaid_seen
        mermaid_seen += 1
        return f"\n@@IMG{idx}@@\n"
    code_blocks.append((lang, mo.group(2)))
    return f"\n@@CODE{len(code_blocks) - 1}@@\n"

text = re.sub(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", _stash, text, flags=re.S)
assert mermaid_seen == len(MERMAID_IMAGES), (
    f"found {mermaid_seen} mermaid blocks but have {len(MERMAID_IMAGES)} images"
)
```

That assertion is the guardrail: adding a third diagram fails loudly instead of
publishing a broken image reference.

After the HTML pass, substitute both `<p>`-wrapped and bare placeholders — the
Markdown library wraps some and inlines others depending on surrounding blank lines:

```python
def _img(mo):
    i = int(mo.group(1))
    return (f'<ac:image ac:align="center" ac:width="{MERMAID_WIDTHS[i]}">'
            f'<ri:attachment ri:filename="{MERMAID_IMAGES[i]}" /></ac:image>')

body = re.sub(r"<p>@@IMG(\d+)@@</p>", _img, body)
body = re.sub(r"@@IMG(\d+)@@", _img, body)
```

## Validate before posting

Parse under the declared namespaces — storage format is XHTML, and a malformed
body is accepted by the API then renders as an error card:

```python
wrapped = ('<root xmlns:ac="http://atlassian.com/content" '
           'xmlns:ri="http://atlassian.com/resource/identifier">' + body + "</root>")
ET.fromstring(wrapped)

refs = set(re.findall(r'ri:filename="([^"]+)"', body))
assert refs == set(MERMAID_IMAGES), f"attachment mismatch: {refs}"
```

## Attach, then update

Attachments must exist before the body referencing them renders:

```python
for name in MERMAID_IMAGES:
    conf.attach_file(str(outdir / name), name=name, content_type="image/png",
                     page_id=PAGE_ID, comment="Rendered from mermaid source")

conf.update_page(page_id=PAGE_ID, title=TITLE, body=body,
                 representation="storage", minor_edit=False)
```

## Re-rendering an already-published page

Uploading the **same filename** creates a new attachment version, and Confluence
serves the latest. The body still points at that filename, so it needs no edit and
the page version does not change. Re-render, re-attach, done.

## Verify the round-trip

```python
p = conf.get_page_by_id(PAGE_ID, expand="body.storage,version")
b = p["body"]["storage"]["value"]
assert b.count("<ac:image") == len(MERMAID_IMAGES)
assert "flowchart" not in b, "mermaid source leaked into the page"
assert not re.findall(r"@@[A-Z]+[^@]*@@", b), "unconverted placeholder"
```

Attachment versions need an explicit expand — `get_attachments_from_content`
omits the `version` key, and reading it raises `KeyError`:

```python
r = conf.get(f"rest/api/content/{PAGE_ID}/child/attachment", params={"expand": "version"})
```
