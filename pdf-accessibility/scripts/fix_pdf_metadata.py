#!/usr/bin/env python3
"""Script-fix the PDF/UA metadata gaps that auto-tagging leaves behind.

For each input PDF, this sets:
  - Document title (/Info /Title and XMP dc:title)
  - Document language (/Catalog /Lang)
  - DisplayDocTitle flag in /ViewerPreferences
  - PDF/UA conformance identifier in XMP (pdfuaid:part=1)
  - /Tabs /S on every page (so annotation reading order is Structure)

Usage: python3 fix_pdf_metadata.py <config.json>

The config maps each input filename (basename) to its {title, lang}.
"""
import json
import sys
from pathlib import Path

import pikepdf
from pikepdf import Dictionary, Name


def fix_pdf(src: Path, dst: Path, title: str, lang: str) -> None:
    with pikepdf.open(src) as pdf:
        root = pdf.Root

        root.Lang = pikepdf.String(lang)

        if "/ViewerPreferences" not in root:
            root.ViewerPreferences = pdf.make_indirect(Dictionary())
        root.ViewerPreferences.DisplayDocTitle = True

        for page in pdf.pages:
            page.obj.Tabs = Name("/S")

        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta["dc:title"] = title
            meta["pdfuaid:part"] = "1"

        if pdf.docinfo is None:
            pdf.docinfo = pdf.make_indirect(Dictionary())
        pdf.docinfo[Name("/Title")] = title

        pdf.save(dst, linearize=False)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    cfg = json.loads(Path(sys.argv[1]).read_text())
    in_dir = Path(cfg["input_dir"])
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    for entry in cfg["files"]:
        src = in_dir / entry["filename"]
        dst = out_dir / entry["filename"].replace("_tagged.pdf", "_fixed.pdf")
        print(f"→ {src.name}")
        print(f"    title: {entry['title']!r}")
        print(f"    lang:  {entry['lang']!r}")
        fix_pdf(src, dst, entry["title"], entry["lang"])
        print(f"    wrote {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
