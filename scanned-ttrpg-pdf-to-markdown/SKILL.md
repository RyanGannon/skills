---
name: scanned-ttrpg-pdf-to-markdown
description: Converts a scanned, image-only PDF (tabletop RPG modules, rulebooks, adventures, or similar reference documents with two-column layouts, stat blocks, and illustrations) into (1) a searchable PDF with an invisible OCR text layer, and (2) a heavily restructured Markdown version with headers, bullet lists, and tables in place of dense prose — designed for readers who find "wall of text" two-column PDFs hard to parse (e.g. ADHD/autistic readers, or anyone who just wants a scannable reference doc). Use this skill whenever the user uploads a scanned PDF and asks for OCR, wants it made searchable, or asks to reformat/restructure a dense document into Markdown, bullet points, or a more readable format — even if they don't use the word "OCR" explicitly. Also trigger if the user mentions buying/owning another module, sourcebook, or scanned reference PDF and wants the same treatment repeated.
---

# Scanned TTRPG PDF → Searchable PDF + Accessible Markdown

Two-stage pipeline. Stage 1 (mechanical, scripted) produces a searchable PDF.
Stage 2 (judgment-driven, done by Claude directly) produces a restructured Markdown
version. Always offer/do both unless the user asks for only one.

## Before starting

Confirm the input is actually a scanned/image-only PDF (no existing text layer).
`pdftotext file.pdf - | head -c 200` — if it returns nothing or garbage, it's image-only
and needs OCR. If it already returns clean text, skip straight to Stage 2 (Markdown
restructuring) using that extracted text.

Check whether these are already installed before assuming you need to install anything:
`tesseract`, and the Python packages `pytesseract`, `pdf2image`, `pypdf`. `pdftoppm` comes
from `poppler-utils`, usually already present. Network access is often unavailable in this
environment, so don't count on `pip install` — check first with e.g.
`python3 -c "import pytesseract"` and adapt if something is missing.

## Stage 1: Searchable PDF (OCR)

Use `scripts/ocr_pdf.py`. Do **not** try to OCR all pages in a single call — for
anything beyond ~10 pages this reliably exceeds the bash tool's runtime limit. Always
batch it:

```bash
python3 scripts/ocr_pdf.py setup /path/to/input.pdf /home/claude/ocr_work
# then in batches of ~6 pages (adjust down if calls are timing out, up if they finish fast):
python3 scripts/ocr_pdf.py ocr /home/claude/ocr_work 1 6
python3 scripts/ocr_pdf.py ocr /home/claude/ocr_work 7 12
# ...continue until status shows no missing pages...
python3 scripts/ocr_pdf.py status /home/claude/ocr_work
python3 scripts/ocr_pdf.py merge /home/claude/ocr_work /mnt/user-data/outputs/<name>_searchable.pdf
```

Key implementation details baked into the script (don't deviate — these were tuned
from experience):
- **JPEG at quality 85, not PNG.** PNG page images at 300 DPI produce enormous
  bloated output PDFs (200MB+ for a 36-page doc). JPEG at this quality is visually
  indistinguishable but shrinks output by ~85%.
- **300 DPI.** Good balance of OCR accuracy vs. file size for a typical letter-page
  scan.
- **`pytesseract.image_to_pdf_or_hocr(..., extension='pdf')`** per page — this embeds
  the original page image with an invisible OCR text layer on top, so the visual
  output is untouched (illustrations, layout, everything) while becoming searchable/
  copyable.
- **`--psm 3`** (automatic page segmentation) handles two-column layouts correctly in
  practice — verified it preserves proper reading order (full left column, then full
  right column) rather than interleaving lines across columns.

After merging, spot-check: `pdftotext -f <page> -l <page> output.pdf -` on a
two-column page, and confirm the text reads in correct column order, not
line-interleaved. Also sanity check file size — if it's ballooned, something reverted
to PNG or too high a DPI.

## Stage 2: Restructured Markdown

This part is **not scriptable** — it requires reading the content and making editorial
judgment calls about structure. Don't just dump extracted text into a .md file; that
defeats the purpose. Use `pdftotext -layout` on the searchable PDF from Stage 1 as your
source text (or the original page-by-page text if it was already provided/extracted),
then rewrite following these principles:

1. **Headers for every structural unit.** Section headings, sub-sections, and — for
   dungeon/adventure modules specifically — a header per numbered room/area/encounter.
   This is what lets a reader jump straight to a specific part instead of reading
   linearly.
2. **Bullet lists for anything enumerable.** Original prose that's secretly a list
   (design guidelines, room contents, trap steps, numbered features) should become an
   actual Markdown list, even if the source rendered it as a paragraph.
3. **Tables for stat blocks and reference data.** This is the highest-value
   transformation for TTRPG content specifically: monster stat lines (HP/attacks/
   damage/AC/special), treasure/item lists, random tables (dN roll → result), and
   character ability score arrays all become Markdown tables. These are the sections
   that read worst as prose and best as tables.
4. **Bold key terms.** Spell names, magic item names, and monster/NPC names in body
   text — enough to let the eye catch them while skimming, not so much that it's
   noisy.
5. **Preserve all content.** This is a reformatting pass, not a summary. Don't drop
   room descriptions, trap mechanics, or treasure details for brevity — restructure
   them, don't cut them. If a passage is asking to be condensed, that's a signal to
   convert it into a table or bullet list, not to shorten it.
6. **Keep the original section order** unless the user asks for reorganization —
   don't reorganize thematically by default, since that breaks the reader's ability to
   cross-reference against the physical/PDF original (e.g. "room XII" should still be
   findable in the same relative position).
7. **Callouts for spoilers/traps/warnings** in the original (e.g. "stop reading if
   you're a player") can become a blockquote or a bolded inline warning — small
   touches like this help a scanning reader triage what needs careful attention.

Long documents (30+ pages) should be written directly to the output `.md` file in one
or a few `create_file`/`str_replace` passes covering logical chunks (e.g. front matter,
then upper level, then lower level, then appendix tables) rather than page-by-page,
since page boundaries rarely align with content structure.

## Output

Deliver both files via `present_files`:
- `<name>_searchable.pdf`
- `<name>.md`

Briefly summarize what structural changes were made (e.g. "converted N stat blocks and
the treasure list into tables, added a header per room") so the user can spot-check
anything that matters most to them.

## Scope note

This skill is for personal-use accessibility reformatting of documents the user
already owns (uploaded PDFs, personalized purchase copies, etc.) — not for reproducing
or redistributing copyrighted text sourced from the web. If the input isn't a file the
user has directly provided, stop and reconsider before applying this workflow.
