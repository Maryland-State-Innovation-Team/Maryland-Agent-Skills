#!/usr/bin/env python3
"""Remediate an already-tagged PDF (e.g. an InDesign export) in place.

Auto-tagging (opendataloader-pdf) throws away the author's structure tree.
When a PDF already has a reasonable tree — real lists, tables, and an
Articles-panel reading order — it is better to *fix* that tree. This script
applies a JSON plan of structure edits plus a set of always-on fixes.

Usage: python3 fix_tagged_pdf.py <plan.json> <input.pdf> <output.pdf>

Paths
-----
Structure elements are addressed by dotted child-index paths from the
StructTreeRoot's first kid, e.g. "0" is /Document, "0.0" its first child,
"0.0.26.0" the first child of that element's 27th child. Only structure
element children count (MCIDs / OBJRs are skipped when indexing). Print the
paths with `outline_struct.py` before writing a plan. All paths are resolved
against the ORIGINAL tree before any edit is applied, so the order of
operations in the plan does not change what a path means.

Plan keys (all optional except title/lang)
------------------------------------------
  title, lang               document title and /Lang
  retag      {path: "/H2"}  set the element's /S to a standard tag
  alt        {path: "text"} set /Alt on a Figure (replaces existing Alt)
  actual_text {path: "text"} set /ActualText (e.g. join a two-line heading
                            "Barrier 1" / "Unclear value" into one phrase)
  link_labels {uri_prefix: "label"}
                            override the auto-derived Link /Contents when the
                            tagged link text is truncated or unhelpful
  artifact   [path, ...]    decorative Figures: re-mark their content as
                            /Artifact and drop the structure element
  set_children {path: [path, ...]}
                            replace an element's structure kids with exactly
                            these elements, in this order (moves elements
                            between parents; anything not listed is dropped
                            from that parent — list everything you keep)
  tables     {path: {"header_row": true, "header_col": true}}
                            convert first-row / first-column cells to TH with
                            /Scope Column / Row
  layout_tables [path, ...] Table/TR/TH/TD used for layout -> Div

Always-on fixes
---------------
  * /Lang, title in Info + XMP, DisplayDocTitle, pdfuaid:part=1
  * /Tabs /S on every page with annotations
  * /Contents on Link annotations (from link text, else the URI)
  * /Scope Column on any TH still lacking a Scope
  * untagged paint operators on page content -> /Artifact BMC … EMC
  * remove structure elements left with no content
  * strip /CIDSet from font descriptors (clause 7.21.4.2)
"""
import json
import re
import sys

import pikepdf
from pikepdf import Array, Dictionary, Name, Operator, String

PATH_OPS = {"m", "l", "c", "v", "y", "h", "re"}
PATH_PAINT = {"S", "s", "f", "F", "f*", "B", "B*", "b", "b*", "n"}
TEXT_SHOW = {"Tj", "TJ", "'", '"'}
OTHER_PAINT = {"Do", "sh", "BI", "INLINE IMAGE"}


def is_se(o):
    return isinstance(o, Dictionary) and "/S" in o


def kids_list(n):
    k = n.get("/K")
    if k is None:
        return []
    return list(k) if isinstance(k, Array) else [k]


def struct_kids(n):
    return [c for c in kids_list(n) if is_se(c)]


def resolve(root, path):
    parts = [int(p) for p in path.split(".")]
    assert parts[0] == 0, path
    node = root
    for p in parts[1:]:
        node = struct_kids(node)[p]
    return node


def set_kids(n, kids):
    if not kids:
        if "/K" in n:
            del n["/K"]
    else:
        n.K = Array(kids)


# ---------------------------------------------------------------- text helpers
def page_index(pdf):
    return {p.objgen: i for i, p in enumerate(pdf.pages)}


def link_text(n, mcid_text, pidx, pg=None):
    pg = n.get("/Pg", pg)
    out = []
    for c in kids_list(n):
        if is_se(c):
            out.append(link_text(c, mcid_text, pidx, pg))
        elif isinstance(c, Dictionary) and c.get("/Type") == "/MCR":
            out.append(mcid_text.get((pidx[c.Pg.objgen], int(c.MCID)), ""))
        elif not isinstance(c, Dictionary) and pg is not None:
            out.append(mcid_text.get((pidx[pg.objgen], int(c)), ""))
    return "".join(out)


def collect_mcid_text(pdf):
    """Best-effort MCID -> text using pdfminer if available (for link labels)."""
    try:
        from pdfminer.high_level import extract_text_to_fp
        from pdfminer.layout import LAParams
        import io
    except ImportError:
        return {}
    buf = io.BytesIO()
    with open(pdf.filename, "rb") as fh:
        extract_text_to_fp(fh, buf, output_type="tag", laparams=None, codec="utf-8")
    import html
    out = {}
    for m in re.finditer(r'<page id="(\d+)"(.*?)</page>', buf.getvalue().decode("utf-8"), re.S):
        for t in re.finditer(r'MCID="(\d+)"[^>]*>(.*?)</', m.group(2), re.S):
            out[(int(m.group(1)), int(t.group(1)))] = html.unescape(
                re.sub(r"<[^>]+>", "", t.group(2)))
    return out


# ---------------------------------------------------------------- content ops
def artifact_mcids(page, mcids):
    """Re-mark the given MCID sequences on a page as /Artifact."""
    ops = pikepdf.parse_content_stream(page)
    changed = 0
    new = []
    for operands, op in ops:
        if str(op) == "BDC" and len(operands) == 2:
            props = operands[1]
            if isinstance(props, Name):
                props = page.Resources.get("/Properties", {}).get(str(props))
            if isinstance(props, Dictionary) and props.get("/MCID") is not None \
                    and int(props.MCID) in mcids:
                new.append(([Name("/Artifact")], Operator("BMC")))
                changed += 1
                continue
        new.append((operands, op))
    page.obj.Contents = PDF.make_stream(pikepdf.unparse_content_stream(new))
    return changed


def wrap_untagged(page):
    """Wrap every paint operator that sits outside any marked content in
    /Artifact BMC … EMC. Paths are wrapped from their first construction op
    through the painting op; text-show and Do/sh ops are wrapped singly."""
    ops = pikepdf.parse_content_stream(page)
    new, depth, open_path, wrapped = [], 0, None, 0
    for operands, op in ops:
        o = str(op)
        if o in ("BDC", "BMC"):
            depth += 1
        elif o == "EMC":
            depth -= 1
        if depth == 0 and o not in ("BDC", "BMC", "EMC"):
            if o in PATH_OPS:
                if open_path is None:
                    open_path = len(new)
                new.append((operands, op))
                continue
            if o in PATH_PAINT and open_path is not None:
                if o == "n":  # clipping path only; nothing painted
                    open_path = None
                    new.append((operands, op))
                    continue
                new.insert(open_path, ([Name("/Artifact")], Operator("BMC")))
                new.append((operands, op))
                new.append(([], Operator("EMC")))
                open_path = None
                wrapped += 1
                continue
            if o in TEXT_SHOW or o in OTHER_PAINT:
                new.append(([Name("/Artifact")], Operator("BMC")))
                new.append((operands, op))
                new.append(([], Operator("EMC")))
                wrapped += 1
                continue
            if o in ("W", "W*") and open_path is not None:
                new.append((operands, op))
                continue
        new.append((operands, op))
    if wrapped:
        page.obj.Contents = PDF.make_stream(pikepdf.unparse_content_stream(new))
    return wrapped


# ---------------------------------------------------------------- main
def main():
    plan_path, src, dst = sys.argv[1:4]
    plan = json.load(open(plan_path))
    global PDF
    pdf = PDF = pikepdf.open(src)
    pidx = page_index(pdf)
    st = pdf.Root.StructTreeRoot
    top = st.K if is_se(st.K) else st.K[0]

    # Resolve every path against the original tree first.
    R = lambda p: resolve(top, p)
    retag = [(R(p), s) for p, s in plan.get("retag", {}).items()]
    alts = [(R(p), a) for p, a in plan.get("alt", {}).items()]
    actual = [(R(p), a) for p, a in plan.get("actual_text", {}).items()]
    arts = [R(p) for p in plan.get("artifact", [])]
    children = [(R(p), [R(c) for c in cs]) for p, cs in plan.get("set_children", {}).items()]
    tables = [(R(p), o) for p, o in plan.get("tables", {}).items()]
    layout = [R(p) for p in plan.get("layout_tables", [])]

    mcid_text = collect_mcid_text(pdf)

    for n, s in retag:
        n.S = Name(s)
    for n, a in alts:
        n.Alt = String(a)
    for n, a in actual:
        n.ActualText = String(a)

    # Decorative figures -> artifacts.
    parent_tree = pikepdf.NumberTree(st.ParentTree)
    for n in arts:
        pg = n.get("/Pg")
        mcids = [int(c) for c in kids_list(n) if not isinstance(c, Dictionary)]
        mcids += [int(c.MCID) for c in kids_list(n)
                  if isinstance(c, Dictionary) and c.get("/Type") == "/MCR"]
        page = pikepdf.Page(pg)
        artifact_mcids(page, set(mcids))
        sp = pg.get("/StructParents")
        if sp is not None:
            arr = parent_tree.get(int(sp))
            for m in mcids:
                if arr is not None and m < len(arr):
                    arr[m] = None
        parent = n.P
        set_kids(parent, [c for c in kids_list(parent)
                          if not (is_se(c) and c.objgen == n.objgen)])

    for parent, kids in children:
        keep_nonse = [c for c in kids_list(parent) if not is_se(c)]
        for c in kids:
            c.P = parent
        set_kids(parent, kids + keep_nonse)

    for t, opts in tables:
        rows = [r for r in struct_kids(t) if str(r.S) == "/TR"]
        for ri, r in enumerate(rows):
            for ci, cell in enumerate(struct_kids(r)):
                if opts.get("header_row") and ri == 0:
                    cell.S = Name("/TH")
                    cell.A = Dictionary(O=Name("/Table"), Scope=Name("/Column"))
                elif opts.get("header_col") and ci == 0:
                    cell.S = Name("/TH")
                    cell.A = Dictionary(O=Name("/Table"), Scope=Name("/Row"))

    def to_div(n):
        if str(n.S) in ("/Table", "/TR", "/TH", "/TD", "/THead", "/TBody", "/TFoot"):
            n.S = Name("/Div")
            if "/A" in n:
                del n["/A"]
            for c in struct_kids(n):
                to_div(c)
    for t in layout:
        to_div(t)

    # Any TH still missing a scope -> Column.
    def walk(n):
        yield n
        for c in struct_kids(n):
            yield from walk(c)
    for n in walk(top):
        if str(n.S) == "/TH":
            a = n.get("/A")
            if not (isinstance(a, Dictionary) and "/Scope" in a):
                n.A = Dictionary(O=Name("/Table"), Scope=Name("/Column"))

    # Remove structure elements with no content (repeat until stable).
    def prune(n):
        kept = []
        for c in kids_list(n):
            if is_se(c):
                prune(c)
                if not kids_list(c) and "/Alt" not in c and "/ActualText" not in c \
                        and str(c.S) not in ("/TD", "/TH"):  # keep grid shape
                    continue
            kept.append(c)
        set_kids(n, kept)
    prune(top)

    # Links: /Contents from the enclosing Link element's text, else URI.
    link_label = {}
    for n in walk(top):
        if str(n.S) == "/Link":
            label = re.sub(r"\s+", " ", link_text(n, mcid_text, pidx)).strip()
            for c in kids_list(n):
                if isinstance(c, Dictionary) and c.get("/Type") == "/OBJR":
                    link_label[c.Obj.objgen] = label
    for page in pdf.pages:
        annots = page.obj.get("/Annots")
        if annots is None:
            continue
        page.obj.Tabs = Name("/S")
        for a in annots:
            if a.get("/Subtype") == "/Link" and not str(a.get("/Contents", "")).strip():
                uri = str(a.get("/A", {}).get("/URI", ""))
                label = link_label.get(a.objgen) or uri
                for prefix, override in plan.get("link_labels", {}).items():
                    if uri.startswith(prefix):
                        label = override
                if uri and label != uri and not label.startswith("http"):
                    label = f"{label} ({uri})"
                a.Contents = String(label or "Link")

    for page in pdf.pages:
        wrap_untagged(page)

    for obj in pdf.objects:
        if isinstance(obj, Dictionary) and obj.get("/Type") == Name("/FontDescriptor") \
                and "/CIDSet" in obj:
            del obj["/CIDSet"]

    pdf.Root.Lang = String(plan["lang"])
    vp = pdf.Root.get("/ViewerPreferences")
    if vp is None:
        pdf.Root.ViewerPreferences = vp = pdf.make_indirect(Dictionary())
    vp.DisplayDocTitle = True
    pdf.docinfo["/Title"] = String(plan["title"])
    with pdf.open_metadata() as meta:
        meta["dc:title"] = plan["title"]
        meta["pdfuaid:part"] = "1"
    pdf.Root.MarkInfo = Dictionary(Marked=True)

    pdf.save(dst)
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
