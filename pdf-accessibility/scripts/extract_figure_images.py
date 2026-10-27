#!/usr/bin/env python3
"""Extract one PNG per /Figure structure element.

Walks the structure tree, correlates each /Figure with its MCID / Image
XObject, and saves the rendered image to disk. Falls back to rendering the
figure's bounding region from a page raster when the figure doesn't resolve
to a single Image XObject (e.g. vector drawings).

Output: <out_dir>/<pdf-name>/fig-NNN.png and a manifest.json.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pikepdf
from pikepdf import Name


def walk_figures(node, path="", pageref=None):
    """Yield (figure_dict, mcid_or_None, page_ref_or_None, path) in document order."""
    if not isinstance(node, pikepdf.Dictionary):
        return
    s = node.get("/S")
    pg = node.get("/Pg", pageref)
    if s is not None and str(s) == "/Figure":
        mcid = None
        k = node.get("/K")
        if isinstance(k, int) or (hasattr(k, "__int__") and not isinstance(k, pikepdf.Dictionary)):
            try: mcid = int(k)
            except: mcid = None
        elif isinstance(k, pikepdf.Dictionary):
            if k.get("/Type") == Name("/MCR"):
                mcid = int(k.get("/MCID", -1))
                pg = k.get("/Pg", pg)
        elif isinstance(k, pikepdf.Array) and len(k) > 0:
            first = k[0]
            if isinstance(first, int) or (hasattr(first, "__int__") and not isinstance(first, pikepdf.Dictionary)):
                try: mcid = int(first)
                except: mcid = None
            elif isinstance(first, pikepdf.Dictionary) and first.get("/Type") == Name("/MCR"):
                mcid = int(first.get("/MCID", -1))
                pg = first.get("/Pg", pg)
        yield node, mcid, pg, path
        return
    k = node.get("/K")
    if k is None:
        return
    if isinstance(k, pikepdf.Array):
        for i, child in enumerate(k):
            yield from walk_figures(child, f"{path}/{i}", pg)
    else:
        yield from walk_figures(k, f"{path}/0", pg)


MCID_BEGIN_RE = re.compile(rb"/\w+\s*<<[^>]*?/MCID\s+(\d+)[^>]*?>>\s*BDC\b")


def extract_image_near_mcid(page_obj, mcid):
    """Scan page content stream for the given MCID, return the next /Do image name."""
    try:
        contents = page_obj.Contents.read_bytes()
    except Exception:
        return None
    for m in MCID_BEGIN_RE.finditer(contents):
        if int(m.group(1)) == mcid:
            tail = contents[m.end():]
            emc = tail.find(b"EMC")
            if emc < 0: continue
            block = tail[:emc]
            # Look for /Name Do
            do_m = re.search(rb"/([A-Za-z0-9_.]+)\s+Do\b", block)
            if do_m:
                return "/" + do_m.group(1).decode()
            return None
    return None


def pil_from_image_xobj(xobj):
    """Return a PIL.Image from a pikepdf image XObject, or None."""
    try:
        img = pikepdf.PdfImage(xobj)
        return img.as_pil_image()
    except Exception:
        return None


def render_page_region(pdf_path, page_index, out_png, resolution=120):
    """Render whole page as PNG as fallback for vector figures."""
    subprocess.run(
        ["pdftocairo", "-png", "-r", str(resolution),
         "-f", str(page_index + 1), "-l", str(page_index + 1),
         "-singlefile", str(pdf_path), str(out_png.with_suffix(""))],
        check=True, capture_output=True
    )


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    out_root = Path(sys.argv[1])
    out_root.mkdir(parents=True, exist_ok=True)
    manifest = {}

    for pdf_path_s in sys.argv[2:]:
        pdf_path = Path(pdf_path_s)
        name = pdf_path.stem
        out_dir = out_root / name
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest[name] = []

        with pikepdf.open(pdf_path) as pdf:
            # Build page index
            page_index_of = {}
            for i, p in enumerate(pdf.pages):
                page_index_of[p.obj.objgen] = i

            root = pdf.Root.get("/StructTreeRoot")
            if root is None: continue
            figs = list(walk_figures(root))
            for i, (fig, mcid, pg, path) in enumerate(figs):
                fig_num = f"{i+1:03d}"
                out_png = out_dir / f"fig-{fig_num}.png"
                page_idx = page_index_of.get(pg.objgen) if pg is not None else None
                image_name = None
                saved = False
                if mcid is not None and pg is not None:
                    image_name = extract_image_near_mcid(pg, mcid)
                    if image_name is not None:
                        res = pg.get("/Resources", {})
                        xo = res.get("/XObject", {}) if res else {}
                        xobj = xo.get(image_name) if xo else None
                        if xobj is not None and xobj.get("/Subtype") == Name("/Image"):
                            pil = pil_from_image_xobj(xobj)
                            if pil is not None:
                                try:
                                    pil.save(out_png)
                                    saved = True
                                except Exception:
                                    pass
                if not saved and page_idx is not None:
                    render_page_region(pdf_path, page_idx, out_png)
                    saved = out_png.exists()
                manifest[name].append({
                    "index": i,
                    "path": str(path),
                    "page": page_idx + 1 if page_idx is not None else None,
                    "mcid": mcid,
                    "image_name": image_name,
                    "file": out_png.name if saved else None,
                    "current_alt": str(fig.get("/Alt", "")) if "/Alt" in fig else None,
                })
        print(f"{name}: extracted {sum(1 for e in manifest[name] if e['file'])}/{len(manifest[name])} figures")

    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
