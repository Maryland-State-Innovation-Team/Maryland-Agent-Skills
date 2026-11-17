#!/usr/bin/env python3
"""Make a tagged PDF read correctly to *naive* accessibility scanners.

PDF/UA validators (veraPDF) and screen readers walk the structure tree from
StructTreeRoot /K and resolve the RoleMap. Many CMS/LMS upload scanners
(e.g. Drupal PDF-accessibility modules built on simple PHP PDF parsers) do
neither: they iterate every StructElem **in file object-number order** and
read the **raw tag name**. Against those, a PDF that passes veraPDF can
still report "first heading is H2", "heading levels skip from H2 to H4", or
"skip from H1 to H5" (an InDesign style named /H5_Overline mapped to /P).

This script removes both discrepancies without changing content or
rendering:

  1. Flatten the RoleMap — every custom tag is renamed to the standard tag
     it maps to (following chains) and /RoleMap is removed.
  2. Renumber structure elements into reading order — every element gets an
     /ID in tree pre-order and is listed in StructTreeRoot /IDTree. qpdf
     numbers objects breadth-first in sorted-key order, and /IDTree sorts
     before /K, so the elements are numbered exactly in reading order. The
     file is written without object streams (object streams regroup objects
     and undo the ordering; they also need PDF 1.5, so disabling them is
     the more compatible choice).
  3. Raise the PDF header version to at least 1.7 (some scanners reject
     < 1.4 as "too old for accessibility features").

Usage: python3 normalize_struct_order.py <input.pdf> <output.pdf>

fix_tagged_pdf.py applies the same steps at the end of every run; use this
script directly on Path A (auto-tagged) output or any already-final PDF.
Existing /ID values on elements are kept; only elements without an ID get
one, and the IDTree is rebuilt to list every element.
"""
import sys

import pikepdf
from pikepdf import Array, Dictionary, Name, String


def kids(n):
    k = n.get("/K")
    return [] if k is None else (list(k) if isinstance(k, Array) else [k])


def is_se(o):
    return isinstance(o, Dictionary) and "/S" in o


def preorder(st):
    out = []

    def walk(n):
        out.append(n)
        for c in kids(n):
            if is_se(c):
                walk(c)
    for t in kids(st):
        if is_se(t):
            walk(t)
    return out


def flatten_rolemap(pdf, st, elements):
    rolemap = {str(k): str(v) for k, v in st.get("/RoleMap", {}).items()}

    def resolve(s, seen=()):
        if s in rolemap and s not in seen:
            return resolve(rolemap[s], seen + (s,))
        return s
    renamed = 0
    # Rename every structure element in the file, not just the reachable
    # ones: once the RoleMap is gone, an unreachable custom tag would have no
    # mapping at all (and naive scanners read unreachable objects too).
    seen = {n.objgen for n in elements}
    extra = [o for o in pdf.objects
             if isinstance(o, Dictionary) and "/S" in o and "/P" in o
             and isinstance(o.S, Name) and o.objgen not in seen
             and o.get("/Type") in (None, Name("/StructElem"))]
    for n in list(elements) + extra:
        s = str(n.S)
        if s in rolemap:
            n.S = Name(resolve(s))
            renamed += 1
    if "/RoleMap" in st:
        del st["/RoleMap"]
    return renamed


def build_idtree(st, elements):
    used = {str(n.ID) for n in elements if "/ID" in n}
    pairs = []
    i = 0
    for n in elements:
        if "/ID" not in n:
            while f"se{i:05d}" in used:
                i += 1
            n.ID = String(f"se{i:05d}")
            used.add(f"se{i:05d}")
        pairs.append((str(n.ID), n))
    # Name-tree keys must be sorted. Generated IDs sort in pre-order; any
    # pre-existing author IDs are placed by sort order, which can only
    # perturb ordering for those few elements.
    names = Array()
    for key, n in sorted(pairs, key=lambda p: p[0]):
        names.append(String(key))
        names.append(n)
    st.IDTree = Dictionary(Names=names)


def normalize(pdf):
    st = pdf.Root.StructTreeRoot
    elements = preorder(st)
    renamed = flatten_rolemap(pdf, st, elements)
    build_idtree(st, elements)
    return len(elements), renamed


def save(pdf, dst):
    pdf.save(dst, object_stream_mode=pikepdf.ObjectStreamMode.disable,
             min_version="1.7")


def main():
    src, dst = sys.argv[1:3]
    pdf = pikepdf.open(src)
    n, renamed = normalize(pdf)
    save(pdf, dst)
    print(f"wrote {dst}: {n} structure elements renumbered in reading order, "
          f"{renamed} custom tags flattened")


if __name__ == "__main__":
    main()
