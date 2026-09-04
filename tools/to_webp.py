# -*- coding: utf-8 -*-
"""Convert the shipped PNGs to LOSSLESS WebP, and prove nothing changed.

    python tools/to_webp.py            # report only
    python tools/to_webp.py --write    # convert, verify, delete the PNG

Lossless and not quality-90, because every one of these is cut-out art: flat
cel shading, hard ink outlines and an alpha edge. Lossy WebP puts ringing on
exactly those three things, and the alpha edge is the one place it shows on a
sprite that gets drawn over a bright sky.

Nothing is deleted until the WebP has been decoded back and compared to the
original pixel for pixel, alpha included. "Lossless" is a flag you pass, not a
thing you have proved.
"""
import os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Only what the game actually loads. sheets/ is source material and concept/,
# frames/ and ref/ never ship, so converting them would cost quality on the
# masters and save the player nothing.
DIRS = ["art", "art/bg", "art/farm", "anim"]


def identical(png, webp):
    """Alpha exact everywhere, colour exact everywhere you can SEE it.

    A PNG may store any RGB it likes underneath a fully transparent pixel and
    WebP normalises that away, so a naive array compare reports a 255-channel
    delta across thousands of pixels that do not exist. Comparing the whole
    RGBA buffer failed ten of these fourteen files on nothing at all."""
    a = np.array(Image.open(png).convert("RGBA")).astype(int)
    b = np.array(Image.open(webp).convert("RGBA")).astype(int)
    if a.shape != b.shape:
        return False, "size %s -> %s" % (a.shape, b.shape)
    if not np.array_equal(a[..., 3], b[..., 3]):
        d = np.abs(a[..., 3] - b[..., 3])
        return False, "ALPHA differs, max %d on %d px" % (d.max(), (d > 0).sum())
    vis = a[..., 3] > 0
    if not np.array_equal(a[..., :3][vis], b[..., :3][vis]):
        d = np.abs(a[..., :3][vis] - b[..., :3][vis])
        return False, "colour differs, max %d on %d px" % (d.max(), (d.any(1)).sum())
    hidden = int((~vis).sum())
    return True, "identical (%d transparent px normalised)" % hidden


def main():
    write = "--write" in sys.argv
    rows, saved, before, after = [], 0, 0, 0
    for d in DIRS:
        full = os.path.join(ROOT, d)
        if not os.path.isdir(full):
            continue
        for f in sorted(os.listdir(full)):
            if not f.lower().endswith(".png"):
                continue
            src = os.path.join(full, f)
            dst = os.path.splitext(src)[0] + ".webp"
            im = Image.open(src)
            if im.mode not in ("RGBA", "RGB"):
                im = im.convert("RGBA")
            im.save(dst, "WEBP", lossless=True, quality=100, method=6)
            ok, why = identical(src, dst)
            b, a = os.path.getsize(src), os.path.getsize(dst)
            before += b; after += a
            if ok and write:
                os.remove(src); saved += b - a
            elif not ok:
                os.remove(dst)
            rows.append((d + "/" + f, b, a, ok, why))
    for name, b, a, ok, why in rows:
        print("  %-26s %7.1f KB -> %7.1f KB  %+5.1f%%  %s" %
              (name, b/1024.0, a/1024.0, (a-b)*100.0/b, "OK" if ok else "FAIL " + why))
    if rows:
        print("  %-26s %7.1f KB -> %7.1f KB  %+5.1f%%" %
              ("TOTAL", before/1024.0, after/1024.0, (after-before)*100.0/before))
    print("  " + ("written, PNGs removed" if write else "dry run: --write to keep them"))


if __name__ == "__main__":
    main()
