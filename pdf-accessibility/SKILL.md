---
name: pdf-accessibility
description: Use when auditing or remediating a PDF for accessibility, PDF/UA (ISO 14289-1), or WCAG conformance; when asked "is this PDF accessible?", "scan this PDF", "fix this PDF for screen readers", "add alt text / tags / metadata to a PDF"; or when deciding whether to retrofit a PDF, regenerate it from source, or publish an accessible HTML alternative. Self-contained open-source pipeline using opendataloader-pdf (auto-tagging), pikepdf (metadata + structure edits), veraPDF (validation), and vision subagents (alt text).
---

# PDF Accessibility Skill

An opinionated, OSS-first workflow for making PDFs pass PDF/UA-1 (ISO 14289-1). Documents the full pipeline — scan, auto-tag, metadata fix, alt text, structural cleanup, re-scan — along with the scripts that implement each step. Battle-tested on a mix of InDesign-exported reports and gallery-walk posters, taking all of them from "fail with hundreds of checks" to "pass with zero fails."

## When to use this skill

- The user asks whether a PDF is accessible, PDF/UA-compliant, or WCAG-compliant.
- The user asks you to scan, audit, remediate, or "fix accessibility" on a PDF.
- The user asks about adding alt text, document language, tags, or a title to a PDF.
- The user is publishing a PDF to a government or public-facing site and needs it to meet accessibility requirements.

## The one rule that beats every other decision

**For text-heavy PDFs that are also publishable as HTML, the fastest and highest-quality accessibility fix is an HTML version at a stable URL.** Retrofitting tags into a 30-page report PDF is multi-day work; a styled HTML page with semantic headings, real alt text, and screen-reader transcripts is often faster to build and is strictly more accessible. Keep the PDF for print/offline, point the "accessible version" link at the HTML.

Use the pipeline below when: the PDF is the primary artifact (official form, signed document, print-destined report), **or** no source is available and no HTML alternative is viable, **or** you need to publish PDFs that already pass validation while a designer re-exports clean versions from the authoring tool.

## The pipeline at a glance

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
```

A single mid-sized PDF goes through this in about 2 minutes of wall-clock time. Four reports in parallel: 5–10 minutes. The scripts live in `scripts/` next to this file.

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
.venv/bin/pip install opendataloader-pdf pikepdf
```

Deterministic mode (no API key, no AI call-outs) is what we use throughout. The `--hybrid` flag can route layout analysis through a docling/LLM backend for tougher documents, but the deterministic mode handles most real-world PDFs.

### Vision for alt text

Any multimodal LLM that can read PNGs. For Claude, delegate to parallel subagents (one per PDF) with `Agent(subagent_type: "general-purpose")`. See the alt-text section below.

## Step-by-step pipeline

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

**Expect duplicates.** When the auto-tagger creates multiple `/Figure` elements per page (common for gallery-walk / poster-style layouts), the extraction's MCID → image-XObject correlation often falls back to rendering the whole page. The result: N `/Figure` elements on the same page produce N copies of the same page render. Dedup by sha1 before paying the vision cost.

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

If any rules still fail, read the JSON report and consult the rule reference below.

## Common PDF/UA-1 rule reference

| Rule | Clause | Meaning | Which step fixes it |
|---|---|---|---|
| 5.1 | PDF/UA ID | XMP must declare `pdfuaid:part=1` | step 3 (metadata) |
| 6.2.1 | MarkInfo | `/MarkInfo /Marked true` required | step 2 (auto-tag) |
| 7.1.2 | Artifact | Tagged content inside Artifact-marked block | manual review / step 8 |
| 7.1.3 | Artifact | Content tagged or marked `/Artifact` | step 2 (auto-tag) |
| 7.1.7 | Role map | Standard tags must not be remapped | source re-export |
| 7.1.8 | Metadata stream | Catalog `/Metadata` present | step 3 (metadata) |
| 7.1.9 | Title | `dc:title` present in XMP | step 3 (metadata) |
| 7.1.10 | DisplayDocTitle | `/ViewerPreferences /DisplayDocTitle true` | step 3 (metadata) |
| 7.1.11 | StructTreeRoot | Catalog has `/StructTreeRoot` | step 2 (auto-tag) |
| 7.2.* | Language | Document `/Lang`; language on alt text | step 3 (metadata) |
| 7.3 | Graphics | `/Figure` has `/Alt` or `/ActualText` | steps 5–7 (alt text) |
| 7.4 | Headings | Logical heading hierarchy, H1 first | source re-export |
| 7.5 | Lists | `/L`, `/LI`, `/Lbl`, `/LBody` used correctly | step 2 (auto-tag) |
| 7.6 | Tables | `/Table`, `/TR`, `/TH`, `/TD` with `/Scope` | source re-export |
| 7.17.3 | Fonts | All fonts embedded | source re-export |
| 7.18.* | Annotations/Links | `/Contents` or enclosing `/Alt`; page `/Tabs /S` | step 3 (metadata, Tabs) |
| 7.20.2 | Form XObjects | Content incorporated into structure | step 8 (Form XObject fix) |
| 7.21.4.2 | CIDSet | CID fonts: CIDSet lists all glyphs | step 4 (strip CIDSet) |

Authoritative spec: ISO 14289-1:2014. Rule-by-rule plain-language guidance: PDF Association's Matterhorn Protocol (31 checkpoints, 136 failure conditions).

## Lessons from real runs

- **Three stages do 95% of the work.** Auto-tag + metadata + CIDSet strip takes a worst-case 300+ failed-check PDF down to 0–12 failed checks. Everything after that is targeted cleanup.
- **Alt text quality is the long pole.** Automated tagging + metadata fixes are fast and safe. Alt text is slow (vision-model) and imperfect (needs human review). Plan proportional time.
- **Expect duplicate /Figure elements per page.** Gallery-walk / poster-style PDFs frequently have 5–11 `/Figure` structure elements on a single composed page. The extraction falls back to full-page renders for each. Dedup by sha1 before running vision; apply the same alt to all duplicates.
- **Shared Form XObjects are a specific trap.** Branded page headers rendered as shared Form XObjects fail PDF/UA when auto-tagged with MCIDs. The fix is to treat them as artifact, not to try to make them structurally unique. The right long-term fix is in the authoring tool.
- **If the PDF has a sibling HTML version, that's the accessible version.** Script-fix the PDF's metadata so viewers announce the title; point users at the HTML for the real reading experience.
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
5. **Never remove tags as a "fix."** Fix the tag or mark the region as artifact; don't silently drop structural information.
6. **For repeating page headers/footers, Artifact is the right pattern.** PDF/UA treats this as decorative content that screen readers skip.
7. **Prefer HTML alternatives for text-heavy public-facing documents.** Link PDF for print; link HTML for screen readers and the "read it online" case, which is most people.
