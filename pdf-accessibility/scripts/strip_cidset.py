#!/usr/bin/env python3
"""Strip the /CIDSet entry from every CIDFont's /FontDescriptor.

ISO 14289-1 clause 7.21.4.2 says: *if* a CIDSet stream is present, it must
list every CID present in the embedded font subset. Many PDF producers emit
a slightly-incomplete CIDSet (missing a few glyphs that are present in the
font program), which trips the validator. The entry is optional and does
not affect screen-reader behavior. Removing it is the standard fix.

Usage: python3 strip_cidset.py input.pdf output.pdf
"""
import sys
from pathlib import Path

import pikepdf
from pikepdf import Name


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    removed = 0
    with pikepdf.open(src) as pdf:
        for obj in pdf.objects:
            if not isinstance(obj, pikepdf.Dictionary): continue
            if obj.get("/Type") != Name("/FontDescriptor"): continue
            if "/CIDSet" in obj:
                del obj["/CIDSet"]
                removed += 1
        print(f"Removed /CIDSet from {removed} FontDescriptor(s)")
        pdf.save(dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
