# Fixing an already-tagged PDF (Path B)

Use this when the PDF already has a structure tree (`pdfinfo` shows `Tagged: yes` and veraPDF does **not** report thousands of 7.1-3 "content not tagged" failures). These are usually exports from InDesign, Word, or Google Docs with tagging on. The author's tree is imperfect, but it carries real lists, real tables, and a reading order taken from the authoring tool. Re-auto-tagging throws all of that away and replaces it with layout inference. So repair the tree rather than replace it.

## Workflow

```bash
# 0. Baseline
verapdf --flavour ua1 --format json input.pdf > reports/input.ua1.json

# 1. Map the tree: every structure element, its dotted path, page and text
.venv/bin/python scripts/outline_struct.py input.pdf > reports/input.outline.txt

# 2. Look at the pages: you can't judge reading order or decorative-vs-informative
#    without seeing them
pdftocairo -png -r 50 input.pdf /tmp/pages/pg

# 3. Get one crop per figure (removal-diff crops; see SKILL.md step 5)
.venv/bin/python scripts/extract_figure_images.py figure-images input.pdf

# 4. Write plans/input.json (format below) and apply it
.venv/bin/python scripts/fix_tagged_pdf.py plans/input.json input.pdf out.pdf

# 5. Verify: validator, visual identity, orphaned content, outline by eye
verapdf --flavour ua1 out.pdf
.venv/bin/python scripts/verify_remediation.py input.pdf out.pdf
.venv/bin/python scripts/outline_struct.py out.pdf | grep -E ' /(H[1-6]|Figure|Table|L) '
```

Iterate on the plan. It is a declarative, reviewable record of every structural decision. Keep it next to the PDF, so that when the designer sends the next revision you can diff the outline and re-apply most of it.

## How to read the outline

```
0.0.26 /Story→/Sect p6 |
  0.0.26.0 /h3-solution→/P p6 |
    0.0.26.0.0 /Story→/Sect p6 |
      0.0.26.0.0.0 /h4→/P p6 | Barrier 2
  0.0.26.1 /body→/P p6 | Employers assume employees would not participate…
```

- **Paths** count structure-element children only. `0` is the first kid of StructTreeRoot (usually `/Document`).
- **`/h4→/P`**: a custom tag (the InDesign paragraph style name) followed by the standard tag it is role-mapped to. Screen readers only see the mapped tag, so here a heading reads as a paragraph.
- **Text** is shown on the deepest element that holds only Spans, Lbl or LBody. An empty `| ` on a leaf usually means an empty paragraph, a Figure, or vector-only content.

## Plan format

All paths are resolved against the **original** tree before any edit is applied, so the order of keys doesn't matter. Write every path from the *input* outline.

| Key | Shape | Use it for |
|---|---|---|
| `title`, `lang` | string | Required. The document title that screen readers announce, and `/Lang`. |
| `retag` | `{path: "/H2"}` | Fix the semantics. Set the element's `/S` to a **standard** tag. Don't edit the RoleMap: it's per style, and the same InDesign style is often used both for real headings and for footnotes. |
| `alt` | `{path: "text"}` | Figures that carry meaning. This replaces any existing `/Alt`, including Adobe's auto-alt. |
| `actual_text` | `{path: "text"}` | Headings or phrases that break across lines or spans and would otherwise run together ("Barrier 1" + "Unclear value" → "Barrier 1: Unclear value"). Also works for drop caps and decorative letter-spacing. |
| `artifact` | `[path, …]` | Decorative figures: the icon above a text heading, background patterns, divider art. Their content is re-marked as `/Artifact`, their ParentTree slot is nulled, and the element is removed. |
| `set_children` | `{path: [path, …]}` | Reading order. Replaces the element's structure kids with exactly this list, in this order. A listed element may come from a different parent (it gets moved), and anything not listed is dropped from that parent, so list everything you keep. Use it to reorder siblings, interleave two stories (titles + bodies → title, body, title, body…), or move a paragraph past a table. |
| `tables` | `{path: {"header_row": true, "header_col": true}}` | Real data tables. Turns the first-row cells into `TH` with Scope Column and the first-column cells into `TH` with Scope Row. |
| `layout_tables` | `[path, …]` | Tables used for page layout (card grids, two-column callouts). Table, TR, TH and TD become `/Div`. |
| `link_labels` | `{uri_prefix: "label"}` | Override a link's auto-derived `/Contents` when the tagged link text is truncated or unhelpful. |

### Always applied (no plan key)

- **Metadata:** `/Lang`, title in Info and XMP, `DisplayDocTitle`, `pdfuaid:part=1`, `MarkInfo`.
- **Pages with annotations:** `/Tabs /S`.
- **Link `/Contents`:** the Link element's text plus its URI, or just the URI when the text *is* the URL (fixes 7.18.1 and 7.18.5).
- **Table headers:** any `TH` still missing a Scope gets `/Scope /Column`.
- **Untagged paint operators:** at the top level of each page's content (rules, table borders, background fills, the page-header Form XObject) they are wrapped in `/Artifact BMC … EMC` (fixes 7.1-3). Paths are wrapped from the first construction operator through the paint operator. Clipping-only paths (`W n`) are left alone.
- **Pruning:** elements left with no content are removed (empty paragraphs, the Sect that used to hold an artifacted icon). Empty `TD` and `TH` cells are kept, because removing them breaks the column count (rule 7.2-42).
- **CIDSet:** `/CIDSet` is stripped (7.21.4.2).

## Deciding what each element should be

**Headings.** Build one outline for the whole document:

- `H1` is the document title, which usually sits on the cover.
- `H2` is each section or page title.
- `H3` and below are the subsections, cards and case studies. No level may be skipped.

Check this against the rendered pages, not the style names. Style names lie: in the playbook, footnotes used the "H2 – No Rule" style, and the table's row letters used "H2 – Rule".

**Reading order.** Put the pages side by side with the outline and fix the order wherever they disagree. These patterns come up often:

| Pattern | Typical cause | Fix |
|---|---|---|
| Cards in a row read 1, 4, 2, 3 | Frames were threaded or created out of order | `set_children` on the parent |
| All the titles, then all the bodies | Titles and bodies sit in two separate threaded stories | Interleave them with `set_children` |
| A sidebar or callout read before the main text | Its frame was created first | Move it |
| Table caption or closing note read before the table | The note is in the same story as the intro | Move the paragraph after the table |
| Cover metadata ("Prepared by…") read before the title | Frame order | Move the title story first |

**Figures.** Ask: "If this image disappeared, would a sighted reader lose information?"

- **No, so artifact it.** Typical cases are icons that illustrate a heading right next to them, background patterns, and stock photos that only set a mood. Alt text is fine for a stock photo if it adds context.
- **Yes, so give it alt text.** Typical cases are logos (say the organization), charts (give the headline and key numbers), and photos of specific people or places.

**Tables.** A grid with column headers that a reader would navigate cell by cell is a data table: use `tables`. A grid used to place cards or a two-column callout is a layout table: use `layout_tables`. InDesign exports both kinds as `/Table`.

## InDesign export patterns

These come up repeatedly in InDesign exports. Include them in any designer handoff:

- **Every paragraph style maps to `/P`** unless *Export Tagging* is set per style (Paragraph Style Options → Export Tagging → PDF tag). The result is a document with almost no headings. veraPDF may only complain about a stray H3 or H4 that skips a level.
- **Reading order follows the Articles panel**, or frame creation order if there are no Articles, not the visual layout.
- **Icons and decorative art export as `/Figure`** unless the designer sets Object Export Options → Alt Text → Source: Decorative / Artifact.
- **Adobe's auto-generated alt text** comes through ending in the literal string "AI generated content". Always replace it.
- **Rules, table borders and background fills are left untagged** (hundreds of 7.1-3 failures on table-heavy pages). Wrap them as artifacts.
- **The running header** (rule plus page number) is often a shared Form XObject invoked at the top level of each page. Wrapping the `Do` as an artifact covers it. If the auto-tagger is ever run on such a PDF, see the 7.20.2 fix in SKILL.md.
- **Link annotations are structurally correct** (Link element plus OBJR) but have no `/Contents`. Ligatures (ﬁ, ﬂ) inside link text can leave the Link element wrapping only part of the text, so override those with `link_labels`.

## Verification beyond veraPDF

veraPDF passing means the *format* is right. It does not check reading order, whether headings are real, or whether alt text is meaningful. After every run:

1. `verify_remediation.py original.pdf fixed.pdf` must show **pixel-identical renders** and **0 orphaned MCIDs**.
2. Read the heading sequence it prints. It should look like a table of contents.
3. Spot-check the reading order with `outline_struct.py fixed.pdf`, or with NVDA or VoiceOver if available.
4. Have a human review every `alt` and `actual_text` string.
