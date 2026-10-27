#!/usr/bin/env python3
"""Fix PDF/UA 7.20.2: shared Form XObjects that contain MCIDs.

The auto-tagger marks repeating page-header Form XObjects with MCIDs,
expecting them to be structural content. When the same Form XObject is
referenced from multiple pages, each MCID would need to have multiple
structural parents, which PDF/UA forbids.

For repeating page furniture (branding, header/footer text), the correct
PDF/UA pattern is to mark it as Artifact so screen readers skip it. This
script:

  1. Finds Form XObjects referenced from more than one page.
  2. For each, strips `/Tag <</MCID N>> BDC ... EMC` wrappers from its
     content stream (keeping the content inside) so there are no MCIDs
     left to require unique parents.
  3. Removes any structure-tree entries that referenced the stripped
     MCIDs via these Form XObjects.
  4. Wraps each invocation of these Form XObjects in each page's content
     stream with `/Artifact BDC ... EMC`.

This loses structural tagging on the branding text (which is appropriate
— repeating page furniture should be artifact), but keeps the visual
output identical.

Usage: python3 fix_shared_form_xobjects.py input.pdf output.pdf
"""
import re
import sys
from collections import defaultdict

import pikepdf
from pikepdf import Name


MCID_BDC_RE = re.compile(
    rb"/\w+\s*<<[^>]*?/MCID\s+(\d+)[^>]*?>>\s*BDC(.*?)EMC",
    re.DOTALL,
)
XOBJ_DO_RE = re.compile(rb"(/[A-Za-z0-9_.]+)\s+Do\b")


def strip_mcid_blocks(content: bytes) -> tuple[bytes, list[int]]:
    """Return (new_content, list_of_stripped_MCIDs)."""
    mcids: list[int] = []

    def repl(m: re.Match) -> bytes:
        mcids.append(int(m.group(1)))
        inner = m.group(2).strip()
        return inner

    new = MCID_BDC_RE.sub(repl, content)
    return new, mcids


def wrap_xobjects_as_artifact(content: bytes, names: set[str]) -> tuple[bytes, int]:
    """Wrap each matching /Name Do operator with /Artifact BDC ... EMC."""
    count = [0]

    def repl(m: re.Match) -> bytes:
        name = m.group(1).decode()
        if name not in names:
            return m.group(0)
        count[0] += 1
        return b"/Artifact BDC " + m.group(0) + b" EMC"

    new = XOBJ_DO_RE.sub(repl, content)
    return new, count[0]


def collect_mcrs_to_remove(node, target_streams, pages_of_target, out):
    """Walk structure tree collecting /K entries that are /MCR referencing stripped MCIDs."""
    if not isinstance(node, pikepdf.Dictionary):
        return
    k = node.get("/K")
    if k is None:
        return
    if isinstance(k, pikepdf.Array):
        # Collect indices to remove
        new_items = []
        for i, child in enumerate(k):
            if _is_targeted_mcr(child, target_streams, pages_of_target):
                out["removed"] += 1
                continue
            new_items.append(child)
            if isinstance(child, pikepdf.Dictionary):
                collect_mcrs_to_remove(child, target_streams, pages_of_target, out)
        if len(new_items) != len(k):
            # Rebuild /K as Array
            node["/K"] = pikepdf.Array(new_items)
    elif isinstance(k, pikepdf.Dictionary):
        if _is_targeted_mcr(k, target_streams, pages_of_target):
            out["removed"] += 1
            del node["/K"]
        else:
            collect_mcrs_to_remove(k, target_streams, pages_of_target, out)


def _is_targeted_mcr(obj, target_streams, pages_of_target) -> bool:
    if not isinstance(obj, pikepdf.Dictionary):
        return False
    if obj.get("/Type") != Name("/MCR"):
        return False
    stm = obj.get("/Stm")
    if stm is None:
        return False
    try:
        return stm.objgen in target_streams
    except AttributeError:
        return False


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2

    src, dst = sys.argv[1], sys.argv[2]

    with pikepdf.open(src) as pdf:
        # Map Form-XObject objgen -> list of (page_index, name_in_page_resources)
        form_refs = defaultdict(list)
        for i, page in enumerate(pdf.pages):
            res = page.obj.get("/Resources", {})
            xo = res.get("/XObject", {}) if res else {}
            for name, obj in (xo.items() if xo else []):
                if obj.get("/Subtype") == Name("/Form"):
                    form_refs[obj.objgen].append((i, str(name), obj))

        # Only shared ones that have MCIDs are the problem
        shared_with_mcids: dict[tuple, object] = {}
        for objgen, refs in form_refs.items():
            if len(refs) < 2:
                continue
            form_obj = refs[0][2]
            content = form_obj.read_bytes()
            if b"/MCID" not in content:
                continue
            shared_with_mcids[objgen] = form_obj

        print(f"Shared Form XObjects with MCIDs: {len(shared_with_mcids)}")

        total_mcids_stripped = 0
        for objgen, form_obj in shared_with_mcids.items():
            content = form_obj.read_bytes()
            new_content, mcids = strip_mcid_blocks(content)
            if mcids:
                form_obj.write(new_content)
                total_mcids_stripped += len(mcids)
                # Also clear the Form XObject's StructParents if present
                if "/StructParents" in form_obj:
                    del form_obj["/StructParents"]
                print(f"  obj {objgen}: stripped MCIDs {mcids}")

        # Wrap invocations as artifact — group invocations by page
        pages_touched = set()
        target_objgens = set(shared_with_mcids.keys())
        for objgen, refs in form_refs.items():
            if objgen not in target_objgens:
                continue
            for page_idx, name_in_page, _ in refs:
                pages_touched.add(page_idx)
        wrapped_total = 0
        for page_idx in pages_touched:
            page = pdf.pages[page_idx]
            # Collect the names on this page that reference target Form XObjects
            res = page.obj.get("/Resources", {})
            xo = res.get("/XObject", {}) if res else {}
            names_to_wrap = set()
            for name, obj in (xo.items() if xo else []):
                if obj.get("/Subtype") == Name("/Form") and obj.objgen in target_objgens:
                    names_to_wrap.add(str(name))
            if not names_to_wrap:
                continue
            content = page.obj.Contents.read_bytes()
            new_content, n = wrap_xobjects_as_artifact(content, names_to_wrap)
            if n:
                page.obj.Contents.write(new_content)
                wrapped_total += n
        print(f"Wrapped {wrapped_total} XObject invocations across {len(pages_touched)} pages")

        # Clean up structure tree /MCR entries that referenced the stripped MCIDs
        # (We can't easily find them by MCID number alone, since MCIDs are reused;
        # the /MCR entries have /Stm pointing at the Form XObject's stream.)
        root = pdf.Root.get("/StructTreeRoot")
        if root is not None:
            out = {"removed": 0}
            collect_mcrs_to_remove(root, target_objgens, {}, out)
            print(f"Removed {out['removed']} dangling /MCR entries from structure tree")

        pdf.save(dst, linearize=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
