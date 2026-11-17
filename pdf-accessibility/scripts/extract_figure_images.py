#!/usr/bin/env python3
"""Extract one PNG per /Figure structure element.

Walks the structure tree, correlates each /Figure with its MCID / Image
XObject, and saves the image to disk.

When a figure doesn't resolve to a single Image XObject (vector icons, placed
PDFs, logos with masks), it is located by *removal diff*: the page is
rendered once as-is and once with that figure's marked content suppressed,
and the changed region is cropped from the original render (with a little
padding). This gives one tight, distinct crop per figure instead of N copies
of the whole page. Only if the diff is empty (e.g. white-on-white) does it
fall back to a full-page render.

Usage: python3 extract_figure_images.py <out_dir> <file.pdf> [more.pdf ...]
Output: <out_dir>/<pdf-name>/fig-NNN.png and <out_dir>/manifest.json
        (manifest records page, MCIDs, method, bbox and any existing /Alt).
Needs: pikepdf, Pillow, pdftocairo (poppler-utils).
"""
import tempfile
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
        node_mcids = all_mcids(node)
        yield node, (node_mcids or ([mcid] if mcid is not None else [])), pg, path
        return
    k = node.get("/K")
    if k is None:
        return
    if isinstance(k, pikepdf.Array):
        for i, child in enumerate(k):
            yield from walk_figures(child, f"{path}/{i}", pg)
    else:
        yield from walk_figures(k, f"{path}/0", pg)


def all_mcids(node):
    """Every MCID directly or indirectly owned by a structure element."""
    out = []
    k = node.get("/K")
    for c in (list(k) if isinstance(k, pikepdf.Array) else ([] if k is None else [k])):
        if isinstance(c, pikepdf.Dictionary):
            if c.get("/Type") == Name("/MCR"):
                out.append(int(c.MCID))
            elif "/S" in c:
                out.extend(all_mcids(c))
        else:
            try:
                out.append(int(c))
            except Exception:
                pass
    return out


PAINT_OPS = {"S", "s", "f", "F", "f*", "B", "B*", "b", "b*",
             "Tj", "TJ", "'", '"', "Do", "sh", "INLINE IMAGE"}


def _render(pdf_path, page_index, stem, resolution):
    subprocess.run(
        ["pdftocairo", "-png", "-r", str(resolution), "-singlefile",
         "-f", str(page_index + 1), "-l", str(page_index + 1),
         str(pdf_path), str(stem)],
        check=True, capture_output=True)
    return Path(str(stem) + ".png")


def crop_by_removal(pdf_path, page_index, mcids, out_png, cache, resolution=120, pad=12):
    """Crop the region drawn by the given MCIDs. Returns bbox (px) or None."""
    from PIL import Image, ImageChops
    tmp = cache.setdefault("_tmp", Path(tempfile.mkdtemp()))
    key = (str(pdf_path), page_index)
    if key not in cache:
        cache[key] = Image.open(_render(pdf_path, page_index, tmp / f"orig-{page_index}", resolution)).convert("RGB")
    orig = cache[key]
    with pikepdf.open(pdf_path) as pdf:
        page = pdf.pages[page_index]
        props = page.Resources.get("/Properties", {})
        new, stack = [], []
        for operands, op in pikepdf.parse_content_stream(page):
            o = str(op)
            if o in ("BDC", "BMC"):
                hit = False
                if o == "BDC" and len(operands) == 2:
                    d = operands[1]
                    if isinstance(d, Name):
                        d = props.get(str(d))
                    hit = isinstance(d, pikepdf.Dictionary) and d.get("/MCID") is not None \
                        and int(d.MCID) in mcids
                stack.append(hit or (bool(stack) and stack[-1]))
            elif o == "EMC" and stack:
                stack.pop()
            if stack and stack[-1] and o in PAINT_OPS:
                if o in ("S", "s", "f", "F", "f*", "B", "B*", "b", "b*"):
                    new.append(([], pikepdf.Operator("n")))  # end path, paint nothing
                continue
            new.append((operands, op))
        page.obj.Contents = pdf.make_stream(pikepdf.unparse_content_stream(new))
        masked_pdf = tmp / "masked.pdf"
        pdf.save(masked_pdf)
    masked = Image.open(_render(masked_pdf, page_index, tmp / "masked", resolution)).convert("RGB")
    bbox = ImageChops.difference(orig, masked).getbbox()
    if not bbox:
        return None
    x0, y0, x1, y1 = bbox
    bbox = (max(0, x0 - pad), max(0, y0 - pad), min(orig.width, x1 + pad), min(orig.height, y1 + pad))
    orig.crop(bbox).save(out_png)
    return bbox


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
            cache = {}
            for i, (fig, mcids, pg, path) in enumerate(figs):
                mcid = mcids[0] if mcids else None
                method, bbox = None, None
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
                        # Masked images (SMask / Mask) look wrong extracted raw —
                        # e.g. a logo whose white lettering lives in the mask.
                        # Let those fall through to the rendered crop.
                        if xobj is not None and xobj.get("/Subtype") == Name("/Image") \
                                and "/SMask" not in xobj and "/Mask" not in xobj:
                            pil = pil_from_image_xobj(xobj)
                            if pil is not None:
                                try:
                                    pil.save(out_png)
                                    saved = True
                                    method = "image-xobject"
                                except Exception:
                                    pass
                if not saved and page_idx is not None and mcids:
                    bbox = crop_by_removal(pdf_path, page_idx, set(mcids), out_png, cache)
                    if bbox:
                        saved, method = True, "removal-diff-crop"
                if not saved and page_idx is not None:
                    render_page_region(pdf_path, page_idx, out_png)
                    saved = out_png.exists()
                    method = "full-page"
                manifest[name].append({
                    "index": i,
                    "path": str(path),
                    "page": page_idx + 1 if page_idx is not None else None,
                    "mcid": mcid,
                    "mcids": mcids,
                    "method": method,
                    "bbox_px_at_120dpi": list(bbox) if bbox else None,
                    "image_name": image_name,
                    "file": out_png.name if saved else None,
                    "current_alt": str(fig.get("/Alt", "")) if "/Alt" in fig else None,
                })
        print(f"{name}: extracted {sum(1 for e in manifest[name] if e['file'])}/{len(manifest[name])} figures")

    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
