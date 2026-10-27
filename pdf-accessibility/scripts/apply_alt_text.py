#!/usr/bin/env python3
"""Write /Alt attributes onto every /Figure structure element.

Reads a per-PDF alts.json mapping (filename → alt text) and applies alt
text to /Figure elements in document order, matching fig-NNN.png →
Nth /Figure element.

Usage: python3 apply_alt_text.py <input.pdf> <alts.json> <output.pdf>
"""
import json
import sys
from pathlib import Path

import pikepdf
from pikepdf import String


def walk_figures(node, path=""):
    if not isinstance(node, pikepdf.Dictionary):
        return
    s = node.get("/S")
    if s is not None and str(s) == "/Figure":
        yield node, path
        return
    k = node.get("/K")
    if k is None:
        return
    if isinstance(k, pikepdf.Array):
        for i, child in enumerate(k):
            yield from walk_figures(child, f"{path}/{i}")
    else:
        yield from walk_figures(k, f"{path}/0")


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    src, alts_path, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    alts = json.loads(Path(alts_path).read_text())

    with pikepdf.open(src) as pdf:
        root = pdf.Root.get("/StructTreeRoot")
        if root is None:
            print("No structure tree", file=sys.stderr)
            return 3
        figures = list(walk_figures(root))

        applied = 0
        for i, (fig, path) in enumerate(figures):
            fname = f"fig-{i+1:03d}.png"
            alt = alts.get(fname)
            if alt is None:
                continue
            fig["/Alt"] = String(alt)
            applied += 1
        print(f"Applied /Alt to {applied}/{len(figures)} /Figure elements")
        pdf.save(dst, linearize=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
