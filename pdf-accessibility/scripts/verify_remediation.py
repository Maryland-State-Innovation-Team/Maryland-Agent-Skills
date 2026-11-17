#!/usr/bin/env python3
"""Check what veraPDF can't: did remediation change how the PDF looks, or
leave tagged content stranded outside the structure tree?

Usage: python3 verify_remediation.py <original.pdf> <remediated.pdf> [--dpi 50]

Checks
------
1. Visual identity. Every page of both files is rendered (pdftocairo) and
   pixel-diffed. Structure edits, artifact marking, and metadata fixes
   should never change a pixel; any diff means a content-stream edit went
   wrong (e.g. a paint operator was dropped).
2. Orphaned MCIDs. Every marked-content ID on every page must map, via
   the ParentTree, to a structure element that is still reachable from
   StructTreeRoot. Content that fails this is invisible to screen readers
   even though veraPDF may still pass (it only sees what's in the tree).
3. Outline summary. Prints the heading sequence (with skipped levels
   flagged) and every Figure's /Alt so a human can eyeball both.

Exit code 0 if checks 1 and 2 pass, 1 otherwise.
Needs: pikepdf, Pillow, pdftocairo (poppler-utils).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import pikepdf
from PIL import Image, ImageChops


def render_all(pdf, outdir, stem, dpi):
    subprocess.run(["pdftocairo", "-png", "-r", str(dpi), str(pdf), str(outdir / stem)],
                   check=True, capture_output=True)
    return sorted(outdir.glob(f"{stem}-*.png"))


def kids(n):
    k = n.get("/K")
    return [] if k is None else (list(k) if isinstance(k, pikepdf.Array) else [k])


def is_se(o):
    return isinstance(o, pikepdf.Dictionary) and "/S" in o


def main():
    args = sys.argv[1:]
    dpi = 50
    if "--dpi" in args:
        i = args.index("--dpi")
        dpi = int(args[i + 1])
        del args[i:i + 2]
    orig, fixed = map(Path, args[:2])
    ok = True

    # 1. Visual identity
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        a = render_all(orig, td, "a", dpi)
        b = render_all(fixed, td, "b", dpi)
        if len(a) != len(b):
            print(f"FAIL page count differs: {len(a)} vs {len(b)}")
            ok = False
        diffs = []
        for i, (pa, pb) in enumerate(zip(a, b), 1):
            bbox = ImageChops.difference(Image.open(pa).convert("RGB"),
                                         Image.open(pb).convert("RGB")).getbbox()
            if bbox:
                diffs.append((i, bbox))
        if diffs:
            ok = False
            for i, bbox in diffs:
                print(f"FAIL page {i} renders differently (diff bbox {bbox} at {dpi} dpi)")
        else:
            print(f"PASS all {len(a)} pages render pixel-identical at {dpi} dpi")

    # 2. Orphaned MCIDs
    pdf = pikepdf.open(fixed)
    st = pdf.Root.get("/StructTreeRoot")
    if st is None:
        print("FAIL no StructTreeRoot")
        return 1
    reach = set()

    def walk(n):
        reach.add(n.objgen)
        for c in kids(n):
            if is_se(c):
                walk(c)
    for top in kids(st):
        if is_se(top):
            walk(top)
    nt = pikepdf.NumberTree(st.ParentTree)
    total = orphans = 0
    for pno, page in enumerate(pdf.pages, 1):
        sp = page.obj.get("/StructParents")
        arr = nt.get(int(sp)) if sp is not None else None
        props = page.Resources.get("/Properties", {})
        for operands, op in pikepdf.parse_content_stream(page):
            if str(op) != "BDC" or len(operands) != 2:
                continue
            d = operands[1]
            if isinstance(d, pikepdf.Name):
                d = props.get(str(d))
            if not isinstance(d, pikepdf.Dictionary) or d.get("/MCID") is None:
                continue
            total += 1
            m = int(d.MCID)
            e = arr[m] if arr is not None and m < len(arr) else None
            if not isinstance(e, pikepdf.Dictionary) or e.objgen not in reach:
                orphans += 1
                if orphans <= 20:
                    print(f"FAIL orphaned MCID {m} on page {pno} (tag {operands[0]})")
    if orphans:
        ok = False
        print(f"FAIL {orphans}/{total} MCIDs are not reachable from the structure tree")
    else:
        print(f"PASS all {total} page MCIDs reachable from the structure tree")

    # 3. Outline summary (informational)
    rolemap = {str(k): str(v) for k, v in st.get("/RoleMap", {}).items()}
    print("\nHeading sequence / figures (review by eye):")
    last = 0

    def outline(n):
        nonlocal last
        s = str(n.S)
        std = rolemap.get(s, s)
        if std in ("/H1", "/H2", "/H3", "/H4", "/H5", "/H6"):
            lvl = int(std[2])
            flag = "  <-- skips a level" if lvl > last + 1 else ""
            at = f' "{n.ActualText}"' if "/ActualText" in n else ""
            print(f"  {'  ' * (lvl - 1)}{std[1:]}{at}{flag}")
            last = lvl
        elif std == "/Figure":
            alt = str(n.get("/Alt", "")).strip()
            print(f"  [Figure] {alt[:100] if alt else '(NO ALT)'}")
        for c in kids(n):
            if is_se(c):
                outline(c)
    for top in kids(st):
        if is_se(top):
            outline(top)
    print("\n(For heading text, run outline_struct.py.)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
