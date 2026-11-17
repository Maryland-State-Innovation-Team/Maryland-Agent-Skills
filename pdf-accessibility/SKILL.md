---
name: pdf-accessibility
description: Use when auditing or remediating a PDF for accessibility, PDF/UA (ISO 14289-1), or WCAG conformance; when asked "is this PDF accessible?", "scan this PDF", "fix this PDF for screen readers", "add alt text / tags / metadata to a PDF"; repairing an already-tagged PDF (InDesign/Word export) whose headings, reading order, tables, or figures are wrong; or when deciding whether to retrofit a PDF, regenerate it from source, or publish an accessible HTML alternative. Self-contained open-source pipeline using opendataloader-pdf (auto-tagging untagged PDFs), pikepdf (metadata + structure-tree repair), veraPDF (validation), and vision subagents (alt text).
---

# PDF Accessibility Skill

An opinionated, OSS-first workflow for making PDFs pass PDF/UA-1 (ISO 14289-1) **and** actually read correctly in a screen reader. Two paths: auto-tag an untagged PDF (Path A), or repair the tree of an already-tagged one (Path B). It covers scanning, tagging or repair, metadata, alt text, structural cleanup, and verification, and includes the scripts for each step. It has been tested on InDesign-exported reports, a tagged InDesign playbook, and gallery-walk posters. All of them went from hundreds of failed checks to zero, with renders that stayed pixel-identical.

## When to use this skill

- The user asks whether a PDF is accessible, PDF/UA-compliant, or WCAG-compliant.
- The user asks you to scan, audit, remediate, or "fix accessibility" on a PDF.
- The user asks about adding alt text, document language, tags, or a title to a PDF.
- The user is publishing a PDF to a government or public-facing site and needs it to meet accessibility requirements.
- A designer's InDesign (or Word) export is "tagged" but reads wrong: no real headings, scrambled order, icons announced as images.

## The one rule that beats every other decision

**For text-heavy PDFs that are also publishable as HTML, the fastest and highest-quality accessibility fix is an HTML version at a stable URL.** Retrofitting tags into a 30-page report PDF is multi-day work; a styled HTML page with semantic headings, real alt text, and screen-reader transcripts is often faster to build and is strictly more accessible. Keep the PDF for print/offline, point the "accessible version" link at the HTML.

Use the pipeline below when: the PDF is the primary artifact (official form, signed document, print-destined report), **or** no source is available and no HTML alternative is viable, **or** you need to publish PDFs that already pass validation while a designer re-exports clean versions from the authoring tool.

## Choose your path first

```bash
pdfinfo input.pdf | grep Tagged
verapdf --flavour ua1 --format json input.pdf > input.ua1.json   # see step 1 for the summary
```

| What you see | Path |
|---|---|
| `Tagged: no`, or the baseline scan shows nearly all content failing 7.1-3 ("content not tagged") | **Path A: auto-tag** (the pipeline below) |
| `Tagged: yes` and a real tree: `outline_struct.py` shows lists, tables and paragraphs carrying the document's text | **Path B: repair the existing tree.** See [references/tagged-pdf-plans.md](references/tagged-pdf-plans.md) |

**Don't auto-tag a tagged PDF.** opendataloader-pdf rebuilds the tree from layout inference. That throws away the author's lists, tables and Articles-panel reading order, which are usually better than what inference produces. A tagged export typically "only" needs heading retagging, reading-order fixes, decorative figures turned into artifacts, alt text, table header scopes, and link `/Contents`. All of that is declarative edits, applied by `fix_tagged_pdf.py`.

### Path B at a glance

```
input.pdf (Tagged: yes)
  [1] verapdf --flavour ua1 ───────── baseline
  [2] outline_struct.py ──────────── dotted-path map of the tree + text
  [3] pdftocairo pages + extract_figure_images.py ── see layout and each figure
  [4] write plans/<doc>.json ──────── retag / reorder / artifact / alt / tables
  [5] fix_tagged_pdf.py plan in out ─ applies plan + always-on fixes
  [6] verapdf + verify_remediation.py ─ PASS, pixel-identical, 0 orphaned MCIDs
```

The plan format, a decision guide for headings, reading order and figures, and the usual InDesign export problems are all in [references/tagged-pdf-plans.md](references/tagged-pdf-plans.md). There's an annotated example in `scripts/tagged_pdf_plan.example.json`.

## Path A: the auto-tag pipeline at a glance

```
original.pdf
    │
    ▼
[1] opendataloader-pdf  ─────────── auto-tag structure tree
    │
    ▼ *_tagged.pdf
[2] fix_pdf_metadata.py ─────────── title, lang, PDF/UA ID, DisplayDocTitle, Tabs
    │
    ▼ *_fixed.pdf
[3] strip_cidset.py ─────────────── benign font warning
    │
    ▼ *_a11y.pdf
[4] extract_figure_images.py  ───── one PNG per /Figure element
    │
    ▼ figure-images/<pdf>/fig-NNN.png
[5] vision subagents ────────────── read PNGs, emit alts.json
    │
    ▼ figure-images/<pdf>/alts.json
[6] apply_alt_text.py ───────────── write /Alt onto each /Figure
    │
    ▼ *_a11y.pdf (with alts)
[7] fix_shared_form_xobjects.py ─── optional, for Form-XObject MCID failures
    │
    ▼ *_a11y.pdf (final)
[8] verapdf --flavour ua1 ────────── verify PASS
    + verify_remediation.py ──────── renders unchanged, no orphaned content
```

A single mid-sized PDF goes through this in about 2 minutes of wall-clock time. Four reports in parallel: 5–10 minutes. The scripts live in `scripts/` next to this file.

## Scripts

All of these are in `scripts/`, and each one documents its usage in its docstring.

| Script | Path | What it does |
|---|---|---|
| `install_verapdf_headless.py` | both | Install veraPDF without Docker or a GUI |
| `outline_struct.py` | both (mainly B) | Print the structure tree as dotted paths with tag, role-map target, page, Alt and text |
| `extract_figure_images.py` | both | One PNG per `/Figure`: raw image, or a removal-diff crop for vector/masked art |
| `fix_tagged_pdf.py` | B | Apply a JSON repair plan, plus always-on fixes (metadata, links, artifacts, CIDSet, Tabs) |
| `tagged_pdf_plan.example.json` | B | Annotated example plan |
| `fix_pdf_metadata.py` | A | Title, lang, DisplayDocTitle, PDF/UA ID, Tabs for auto-tagged output |
| `strip_cidset.py` | A | Remove incomplete `/CIDSet` (7.21.4.2) |
| `apply_alt_text.py` | A | Write `alts.json` onto `/Figure` elements in document order |
| `fix_shared_form_xobjects.py` | A | Fix 7.20.2 (shared Form XObject with MCIDs) |
| `verify_remediation.py` | both | Pixel-diff renders and find orphaned MCIDs; print heading/figure summary |

## Install the tools

### veraPDF (the validator)

OSS reference implementation of PDF/UA validation. **Pick one install path:**

**Docker (preferred when available):**
```bash
docker pull verapdf/cli:latest
alias verapdf='docker run --rm -v "$PWD:/data:ro" verapdf/cli:latest'
```

**Headless native install (Java 11+ required, no Docker):**
```bash
python3 scripts/install_verapdf_headless.py
# produces ~/.local/opt/verapdf/verapdf
```

**Why headless-install is in this skill:** veraPDF only ships an izpack GUI installer at `software.verapdf.org`. No fat JAR on Maven Central, no apt/brew/snap package. The izpack console mode is finicky; `install_verapdf_headless.py` drives it via a pty for reliability.

**Verify:**
```bash
verapdf --version   # should print "veraPDF 1.30.x" or newer
```

### opendataloader-pdf (the auto-tagger)

Apache-2.0 Java-based layout analyzer + auto-tagger. Install via pip:

```bash
python3 -m venv .venv
.venv/bin/pip install opendataloader-pdf pikepdf pillow pdfminer.six
```

`pdfminer.six` gives MCID → text (`outline_struct.py`, link labels). Pillow and `pdftocairo` (poppler-utils) handle figure crops and render diffs.

Deterministic mode (no API key, no AI call-outs) is what we use throughout. The `--hybrid` flag can route layout analysis through a docling/LLM backend for tougher documents, but the deterministic mode handles most real-world PDFs.

### Vision for alt text

Any multimodal LLM that can read PNGs. For Claude, delegate to parallel subagents (one per PDF) with `Agent(subagent_type: "general-purpose")`. See the alt-text section below.

## Path A step-by-step

Steps 1, 5, 6 and 9 also apply to Path B.

### 1 — Scan the original to understand what's broken

```bash
mkdir -p pdf-accessibility-reports
verapdf --flavour ua1 --format json --maxfailuresdisplayed 3 input.pdf \
  > pdf-accessibility-reports/input.ua1.json
```

Summarize with jq:

```bash
jq -r '
  .report.jobs[0].validationResult[0].details |
  "Passed: \(.passedRules) | Failed rules: \(.failedRules) | Failed checks: \(.failedChecks)",
  (.ruleSummaries | map(select(.ruleStatus=="FAILED")) |
    map("  • \(.clause).\(.testNumber) [\(.tags|join(","))] ×\(.failedChecks) — \(.description[0:140])") |
    join("\n"))
' pdf-accessibility-reports/input.ua1.json
```

### 2 — Auto-tag with opendataloader-pdf

Deterministic layout analysis + structure tagging. Takes ~30–60 seconds per PDF.

```bash
mkdir -p remediated_pdfs/stage1-autotag
.venv/bin/opendataloader-pdf -q -f tagged-pdf \
  -o remediated_pdfs/stage1-autotag input.pdf
# → remediated_pdfs/stage1-autotag/input_tagged.pdf
```

For multiple PDFs, pass them all at once; the tool handles them sequentially.

Re-scan at this point to confirm the big structural failures (unmarked content, missing StructTreeRoot) have resolved. Typical delta: 90–99% reduction in failed checks.

### 3 — Fix the metadata gaps

The auto-tagger builds a tag tree but doesn't touch document-level metadata. Run `scripts/fix_pdf_metadata.py` with a config that supplies the real title + language for each PDF:

```bash
# scripts/pdf_metadata.json
{
  "input_dir": "remediated_pdfs/stage1-autotag",
  "output_dir": "remediated_pdfs/stage2-fixed",
  "files": [
    {
      "filename": "input_tagged.pdf",
      "title": "The Document Title That Screen Readers Should Say",
      "lang": "en-US"
    }
  ]
}
```

```bash
.venv/bin/python3 scripts/fix_pdf_metadata.py scripts/pdf_metadata.json
```

See `scripts/pdf_metadata.example.json` for the full shape.

What it fixes:
- `/Info /Title` + XMP `dc:title` (document title in metadata)
- `/Catalog /Lang` (document language)
- `/ViewerPreferences /DisplayDocTitle true` (so viewers show the title, not the filename)
- XMP `pdfuaid:part=1` (PDF/UA conformance identifier)
- `/Tabs /S` on every page (annotation reading order)

### 4 — Strip the CIDSet entry (optional, resolves benign font warnings)

Many PDF producers emit a slightly-incomplete `/CIDSet` in CID-font descriptors, which trips ISO 14289-1 clause 7.21.4.2. The entry is optional and has no screen-reader impact. Removing it is standard practice:

```bash
mkdir -p remediated_pdfs/final
.venv/bin/python3 scripts/strip_cidset.py \
  remediated_pdfs/stage2-fixed/input_fixed.pdf \
  remediated_pdfs/final/input_a11y.pdf
```

### 5 — Extract per-figure images for alt text

```bash
.venv/bin/python3 scripts/extract_figure_images.py \
  figure-images \
  remediated_pdfs/final/*_a11y.pdf
```

Produces `figure-images/<pdf-stem>/fig-NNN.png`, one per `/Figure` structure element in document order, plus a `manifest.json`.

**How each figure is captured** (recorded as `method` in the manifest):

- `image-xobject`: the raw embedded image, for a single unmasked raster.
- `removal-diff-crop`: for vector art, placed PDFs, and images with soft masks. The page is rendered with and without that figure's marked content, and the changed region is cropped. This gives one tight crop per figure, so the vision model can tell the four icons on a page apart.
  - Masked images take this route on purpose. Extracted raw, a logo whose white lettering lives in the mask comes out as just the seal.
- `full-page`: used only when the diff is empty, e.g. white-on-white art.

Still dedup by sha1 before paying the vision cost. Gallery-walk posters can have several `/Figure` elements that cover the same pixels.

### 6 — Generate alt text with vision (parallel subagents)

Launch one subagent per PDF. Each gets a focused context: a figure folder, the PDF's domain/purpose, and dedup instructions. Example prompt skeleton:

```
You are generating alt text for the figures in <PDF-name>, which is <one-line
description of what the PDF is>.

Images: `figure-images/<pdf-stem>/fig-001.png` through `fig-NNN.png`.

Task:
  1. sha1 all N files to find unique content.
  2. Read each unique image.
  3. Write a one-sentence screen-reader alt text (10–30 words typical;
     longer for data charts).
  4. Duplicate-hash files get identical alt text.
  5. Write results to `figure-images/<pdf-stem>/alts.json`
     with shape {"fig-001.png": "...", ...} — all N entries.

Style:
  - No "image of" / "picture of" preambles.
  - Lead with the subject or the data.
  - Neutral they/them for people whose pronouns aren't visible.
  - For charts, give the headline + key numbers.
```

Parallelizing by PDF is the sweet spot: each subagent focuses on one document's visual vocabulary and keeps the vision context manageable (~5–30 unique images per subagent).

**Note on alt-text quality.** Vision-generated alt text is plausible but not perfect. Risks: team-member names/roles may be miscounted, chart numbers may be transcribed with minor errors, logo attribution may be off. A human spot-check before publishing is strongly recommended.

### 7 — Apply the alt text to the PDF

```bash
.venv/bin/python3 scripts/apply_alt_text.py \
  remediated_pdfs/final/input_a11y.pdf \
  figure-images/input/alts.json \
  remediated_pdfs/with-alt/input_a11y.pdf
```

The script walks the structure tree in document order, matching `fig-001.png` → first `/Figure`, `fig-002.png` → second `/Figure`, etc., and writes the `/Alt` attribute.

**Path B:** put alt text in the plan's `alt` key, keyed by structure path, and list decorative figures under `artifact`. Don't use `apply_alt_text.py` there. Its by-position matching breaks once some figures become artifacts.

### 8 — Fix shared Form XObject MCID failures (if present)

This is a specific failure mode from the auto-tagger: when a PDF uses a repeating page-header Form XObject (e.g., branding like "Impact Report 2025" drawn on every page), the auto-tagger marks that Form XObject's text with MCIDs. Because the Form XObject is referenced from N pages, each MCID would need N structural parents, which PDF/UA forbids. veraPDF flags this as **rule 7.20.2: "Form XObject contains MCIDs and is referenced more than once."**

The fix: treat the repeating Form XObject as decorative page furniture (which it is) by stripping its internal MCIDs and wrapping its invocation sites as `/Artifact`. This is the PDF/UA-correct pattern for page headers/footers.

```bash
.venv/bin/python3 scripts/fix_shared_form_xobjects.py \
  remediated_pdfs/with-alt/input_a11y.pdf \
  remediated_pdfs/with-alt/input_a11y-fx.pdf
```

Only run this if the scan after step 7 shows 7.20.2 failures. If the PDF doesn't use shared Form XObjects, this script is a no-op.

**Side effect to document:** this removes structural tagging from the repeating page header. Screen readers will no longer announce "Impact Report 2025" on every page. For a repeating page header, this is correct behavior — but if the author wants that header announced, they should re-author it in the design tool so each page gets its own tag (not a shared Form XObject).

### 9 — Final validation

```bash
verapdf --flavour ua1 --format text remediated_pdfs/with-alt/*.pdf
```

Target output:

```
PASS /path/to/input_a11y.pdf ua1
```

Then check what veraPDF can't:

```bash
.venv/bin/python3 scripts/verify_remediation.py input.pdf remediated_pdfs/with-alt/input_a11y.pdf
```

The script exits non-zero if any page renders differently from the original, or if any marked content (MCID) is no longer reachable from the structure tree. Content in either state is invisible to screen readers, and veraPDF can still pass. It also prints the heading sequence (flagging skipped levels) and every figure's alt text, for review by eye.

If any rules still fail, read the JSON report and consult the rule reference below.

## Common PDF/UA-1 rule reference

| Rule | Clause | Meaning | Which step fixes it |
|---|---|---|---|
| 5.1 | PDF/UA ID | XMP must declare `pdfuaid:part=1` | step 3 (metadata) |
| 6.2.1 | MarkInfo | `/MarkInfo /Marked true` required | step 2 (auto-tag) |
| 7.1.2 | Artifact | Tagged content inside Artifact-marked block | manual review / step 8 |
| 7.1.3 | Artifact | Content tagged or marked `/Artifact` | A: step 2 (auto-tag) · B: `fix_tagged_pdf.py` wraps untagged rules, fills and borders as artifacts |
| 7.1.7 | Role map | Standard tags must not be remapped | source re-export |
| 7.1.8 | Metadata stream | Catalog `/Metadata` present | step 3 (metadata) |
| 7.1.9 | Title | `dc:title` present in XMP | step 3 (metadata) |
| 7.1.10 | DisplayDocTitle | `/ViewerPreferences /DisplayDocTitle true` | step 3 (metadata) |
| 7.1.11 | StructTreeRoot | Catalog has `/StructTreeRoot` | step 2 (auto-tag) |
| 7.2.* | Text / structure | Document `/Lang`; language on alt text; 7.2-42: every table row spans the same number of columns | step 3 (metadata) · don't prune empty `TD`/`TH` cells |
| 7.3 | Graphics | `/Figure` has `/Alt` or `/ActualText` | steps 5–7 (alt text) · decorative figures: re-mark as artifact instead (B: `artifact`) |
| 7.4.2 | Headings | H1 first, no skipped levels | B: `retag` (fixable in place; source re-export is better long term) |
| 7.5 | Tables | `TH` needs `/Scope` (or Headers/IDs); every `TD` must have a determinable header | B: `tables` (header_row / header_col) |
| 7.6 | Lists | `/L`, `/LI`, `/Lbl`, `/LBody` used correctly | A: step 2 (auto-tag) |
| 7.17.3 | Fonts | All fonts embedded | source re-export |
| 7.18.1 / 7.18.5 | Links | Each Link annotation needs `/Contents` (or an `/Alt` on the enclosing element) | `fix_tagged_pdf.py` (always on). Note: `fix_pdf_metadata.py` does **not** add these |
| 7.18.3 | Annotations | Pages with annotations need `/Tabs /S` | step 3 (metadata) |
| 7.20.2 | Form XObjects | Content incorporated into structure | step 8 (Form XObject fix) |
| 7.21.4.2 | CIDSet | CID fonts: CIDSet lists all glyphs | step 4 (strip CIDSet) |

Authoritative spec: ISO 14289-1:2014. Rule-by-rule plain-language guidance: PDF Association's Matterhorn Protocol (31 checkpoints, 136 failure conditions).

## Lessons from real runs

- **Three stages do 95% of the work.** Auto-tag + metadata + CIDSet strip takes a worst-case 300+ failed-check PDF down to 0–12 failed checks. Everything after that is targeted cleanup.
- **Alt text quality is the long pole.** Automated tagging + metadata fixes are fast and safe. Alt text is slow (vision-model) and imperfect (needs human review). Plan proportional time.
- **Expect duplicate /Figure elements per page.** Gallery-walk / poster-style PDFs frequently have 5–11 `/Figure` structure elements on a single composed page. The extraction falls back to full-page renders for each. Dedup by sha1 before running vision; apply the same alt to all duplicates.
- **Shared Form XObjects are a specific trap.** Branded page headers rendered as shared Form XObjects fail PDF/UA when auto-tagged with MCIDs. The fix is to treat them as artifact, not to try to make them structurally unique. The right long-term fix is in the authoring tool.
- **If the PDF has a sibling HTML version, that's the accessible version.** Script-fix the PDF's metadata so viewers announce the title; point users at the HTML for the real reading experience.
- **Passing veraPDF is far from accessible.** On the tagged InDesign playbook, veraPDF's 11 failed rules missed the worst problems:
  - every heading was tagged as a paragraph (the validator flagged only one skipped level);
  - the footnotes were tagged as headings;
  - cards read 1, 4, 2, 3 and barriers read 2, 3, 1, 4, 5;
  - one page read all five lesson titles, then all five bodies;
  - a card-grid layout was tagged as a data table;
  - eleven decorative icons were tagged as figures.

  veraPDF checks none of these. Always review the outline (`outline_struct.py`) against the rendered pages.
- **Check `Tagged:` before choosing a path.** An InDesign or Word export with tags on is a repair job (Path B), not an auto-tag job.
- **Decorative images become artifacts, not alt text.** An icon above a text heading that says the same thing, a background pattern, or a mood photo adds noise if it's announced. Re-mark its content as `/Artifact`, null its ParentTree slot, and drop the element (`fix_tagged_pdf.py` `artifact`). Reserve alt text for logos, charts, and images that carry information.
- **Replace Adobe's auto-alt.** InDesign and Acrobat auto-generated alt text arrives ending in the literal string "AI generated content".
- **Don't fix headings through the RoleMap.** InDesign paragraph styles are reused for unrelated content (the "H2 – No Rule" style also did the footnotes). Retag individual elements.
- **Use ActualText for headings that span lines or spans.** Otherwise "Barrier 1" and "Unclear program value" can be read as "Barrier 1Unclear program value".
- **Ligatures can truncate link text.** A Link element can end mid-word at a ﬁ ligature ("Building fi…"). Check link labels, and override them with `link_labels`.
- **Prune empty elements, but not table cells.** Removing an empty header `TD` makes rows span different column counts (7.2-42).
- **Map MCIDs to text with pdfminer.** `pdf2txt.py -t tag file.pdf` emits every marked-content sequence with its MCID. Through the API, pass a `BytesIO` with `codec="utf-8"`, because the tag writer emits bytes.
- **Content-stream edits must be pixel-neutral.** Every structural fix here (retag, reorder, artifact wrapping) should leave the renders identical. Diff them (`verify_remediation.py`). A changed pixel means a paint operator was dropped or reordered.
- **Verify PDF/UA, test with a real screen reader.** The validator confirms every `/Figure` has `/Alt` but not that the `/Alt` says anything useful. NVDA (Windows) or VoiceOver (macOS) sanity-check in <5 minutes.

## HTML alternative pattern

When a PDF is really a long-form document, publish an HTML version alongside the PDF. Minimum shape:

- Semantic headings (`<h1>` → `<h6>`, exactly one `<h1>`, no skipped levels).
- Every image has `alt` text; decorative images get `alt=""` plus `role="presentation"`.
- For text-heavy chart or infographic images, pair the image with a visually-hidden transcript (`.sr-only` block) that reads every category, label, and value.
- Tables use `<th scope="col|row">`.
- External links announce behavior to screen readers: `target="_blank" rel="noopener noreferrer"` plus a visually-hidden " (opens in a new tab)" suffix.
- Contrast meets WCAG AA (4.5:1 text; 3:1 large text/UI).
- Primary CTA points at the HTML version ("Read online"); PDF stays available as a secondary download.

This is strictly better than a tagged PDF for most readers (searchable, responsive, deep-linkable, no download required) and is faster to build than retrofitting tags.

## Behavioral rules

1. **Scan before advising.** Never guess at PDF issues from a filename or thumbnail — run veraPDF first.
2. **Report rule IDs with every finding** so the user can look them up or re-check after a fix.
3. **Distinguish machine findings from human judgment.** Alt-text *presence* is machine-checkable; alt-text *quality* needs a human.
4. **For untagged PDFs, recommend rebuilding from source first.** Retrofitting tags is slower and lower-quality than a clean re-export from InDesign / Word / LibreOffice with "Create Tagged PDF" on.
5. **Never remove tags to make the validator pass.** Fix the tag, or re-mark the content as an artifact. Removing an element is only correct when its content is re-marked as `/Artifact` in the same edit (decorative figures, or empty wrappers left behind), so that no real content ends up untagged or orphaned.
6. **Repair, don't replace, an existing tag tree.** If the PDF is tagged, use Path B.
7. **A validator pass is necessary, not sufficient.** Before calling a PDF done, review the heading outline and reading order against the rendered pages, and confirm `verify_remediation.py` passes.
8. **For repeating page headers/footers, Artifact is the right pattern.** PDF/UA treats this as decorative content that screen readers skip.
9. **Prefer HTML alternatives for text-heavy public-facing documents.** Link PDF for print; link HTML for screen readers and the "read it online" case, which is most people.
