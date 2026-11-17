#!/usr/bin/env python3
"""Print a PDF's structure tree as dotted paths, with each element's text.

This is the map you write a fix_tagged_pdf.py plan against. Paths count
structure-element children only (MCIDs and OBJRs are skipped), starting at
the StructTreeRoot's first kid as "0" — the same addressing the plan uses.

Each line:  <path> <tag>[→<role-mapped standard tag>] p<page> [Alt=…] | <text>

Leaf-level text containers (Span, Lbl, LBody) are folded into their parent
so the output stays readable; text is shown on the deepest element that
contains only those. ActualText, where present, replaces the content text.

Ends with an "ORPHANED CONTENT" list when some marked content belongs to
structure elements that are detached from the tree (screen readers never
reach it); re-attach those with the fix_tagged_pdf.py plan's "attach" key.

Usage: python3 outline_struct.py <input.pdf> [--width 90]   (--width 0 = no truncation)
Needs: pikepdf, pdfminer.six  (MCID → text via pdfminer's "tag" output)
"""
import html
import io
import re
import sys

import pikepdf
from pdfminer.high_level import extract_text_to_fp

FOLD = {"/Span", "/Lbl", "/LBody"}


def mcid_text_map(path):
    """{(page_index, mcid): text} from pdfminer's tagged-text output."""
    buf = io.BytesIO()
    with open(path, "rb") as fh:
        # BytesIO + codec: pdfminer's tag writer emits bytes, not str.
        extract_text_to_fp(fh, buf, output_type="tag", laparams=None, codec="utf-8")
    out = {}
    for m in re.finditer(r'<page id="(\d+)"(.*?)</page>', buf.getvalue().decode("utf-8"), re.S):
        for t in re.finditer(r'MCID="(\d+)"[^>]*>(.*?)</', m.group(2), re.S):
            out[(int(m.group(1)), int(t.group(1)))] = html.unescape(re.sub(r"<[^>]+>", "", t.group(2)))
    return out


def kids(n):
    k = n.get("/K")
    return [] if k is None else (list(k) if isinstance(k, pikepdf.Array) else [k])


def is_se(o):
    return isinstance(o, pikepdf.Dictionary) and "/S" in o


def main():
    args = sys.argv[1:]
    width = 90
    if "--width" in args:
        i = args.index("--width")
        width = int(args[i + 1]) or 10**9
        del args[i:i + 2]
    src = args[0]
    pdf = pikepdf.open(src)
    pages = {p.objgen: i for i, p in enumerate(pdf.pages)}
    txt = mcid_text_map(src)
    st = pdf.Root.StructTreeRoot
    rolemap = {str(k): str(v) for k, v in st.get("/RoleMap", {}).items()}

    def text(n, pg=None):
        if is_se(n):
            if "/ActualText" in n:
                return str(n.ActualText)
            pg = n.get("/Pg", pg)
            return "".join(text(c, pg) for c in kids(n))
        if isinstance(n, pikepdf.Dictionary):
            if n.get("/Type") == "/MCR":
                return txt.get((pages[n.Pg.objgen], int(n.MCID)), "")
            return ""  # OBJR
        if pg is None:
            return ""
        try:
            return txt.get((pages[pg.objgen], int(n)), "")
        except (TypeError, ValueError):
            return ""

    def first_page(n):
        if "/Pg" in n:
            return pages.get(n.Pg.objgen)
        for c in kids(n):
            if is_se(c):
                p = first_page(c)
                if p is not None:
                    return p
            elif isinstance(c, pikepdf.Dictionary) and "/Pg" in c:
                return pages.get(c.Pg.objgen)
        return None

    def walk(n, depth, path):
        s = str(n.S)
        if s in FOLD:
            return
        sub = [c for c in kids(n) if is_se(c)]
        leafish = all(str(c.S) in FOLD for c in sub)
        p = first_page(n)
        mapped = f"→{rolemap[s]}" if s in rolemap else ""
        alt = f" Alt={str(n.Alt)[:width]!r}" if "/Alt" in n else ""
        t = re.sub(r"\s+", " ", text(n)).strip()[:width] if leafish else ""
        print(f"{'  ' * depth}{path} {s}{mapped} p{p + 1 if p is not None else '?'}{alt} | {t}")
        if not leafish:
            for i, c in enumerate(sub):
                walk(c, depth + 1, f"{path}.{i}")

    tops = [c for c in kids(st) if is_se(c)]
    walk(tops[0], 0, "0")

    # Content whose structure element is not reachable from the tree is never
    # read by screen readers. List it so the plan can re-attach it ("attach").
    reach = set()

    def mark(n):
        reach.add(n.objgen)
        for c in kids(n):
            if is_se(c):
                mark(c)
    for t in tops:
        mark(t)
    nt = pikepdf.NumberTree(st.ParentTree)
    orphans = []
    for pi, page in enumerate(pdf.pages):
        sp = page.obj.get("/StructParents")
        arr = nt.get(int(sp)) if sp is not None else None
        if arr is None:
            continue
        for m, e in enumerate(arr):
            if is_se(e) and e.objgen not in reach:
                t = re.sub(r"\s+", " ", txt.get((pi, m), "")).strip()
                orphans.append((pi + 1, m, str(e.S), t))
    if orphans:
        print("\nORPHANED CONTENT (in the ParentTree but unreachable from the tree; "
              "screen readers skip it — re-attach with the plan's 'attach' key):")
        for pg, m, s_, t in orphans:
            print(f"  page {pg} MCID {m} {s_} | {t[:width]}")


if __name__ == "__main__":
    main()
