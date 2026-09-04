# -*- coding: utf-8 -*-
"""Slice the golden egg's spin out of one painted sheet.

Two earlier versions of this got it wrong and both are worth remembering.

The first squashed a single hero egg horizontally per frame. That is what a
cheap game does: the silhouette narrows but the highlight stays welded to the
surface, so the eye reads a picture being scaled rather than an object turning.

The second tried to fix that honestly, by treating the painting as a texture
wrapped round a solid of revolution and re-projecting it per frame -- a pixel at
horizontal position u sits at surface angle asin(u), so after turning by t it is
seen at sin(asin(u) + t). That is the correct model, and it looked terrible: the
mapping compresses the whole texture into a few columns near the silhouette, so
a handful of source pixels smear across the edge and the egg comes out striped.
Fixing it properly needs real area sampling, and it is not worth it when an
artist can simply draw the seven views.

So the spin is PAINTED, one sheet, and this only cuts it up. What the sheet has
to contain, and what the prompt asks for in these words, is the part that makes
it read: square on, narrowing, a thin bright polished RIM at the edge, then the
far side coming round DARKER because it faces away from the light, widening and
brightening back. The rim and the dark reverse are the whole difference between
a spin and a squash.

    python cut_eggs.py          # sheets/v2/egg_spin.png -> anim/egg*.webp
"""
import os, sys, json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imglib import key_green, despill, bbox

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH   = os.path.join(ROOT, "sheets", "v2")
ANIM = os.path.join(ROOT, "anim")

TALL = 62        # frame height in sprite pixels


def main():
    rgba = despill(key_green(Image.open(os.path.join(SH, "egg_spin.png"))))
    al = rgba[..., 3]

    # Split on empty columns and keep runs BY POSITION, not by width: the
    # edge-on frame is a sliver, and "keep the widest N" throws away the one
    # frame that proves the egg is turning.
    cols = al.sum(0) > 0
    runs, s = [], None
    for x, v in enumerate(cols):
        if v and s is None: s = x
        elif not v and s is not None:
            runs.append((s, x)); s = None
    if s is not None: runs.append((s, len(cols)))
    runs = [r for r in runs if (r[1] - r[0]) >= 4]
    tallest = max((al[:, a:b] > 0).sum(0).max() for a, b in runs)
    runs = [r for r in runs if (al[:, r[0]:r[1]] > 0).sum(0).max() > tallest * 0.55]
    print("  %d frames on the sheet" % len(runs))

    # one scale for the whole sheet, off the tallest frame, so the egg does not
    # change size as it turns
    scale = TALL / float(tallest)
    meta = []
    for i, (x0, x1) in enumerate(runs):
        sub = rgba[:, x0:x1]
        bb = bbox(sub[..., 3])
        im = Image.fromarray(sub[bb[1]:bb[3], bb[0]:bb[2]], "RGBA")
        w = max(1, round(im.width * scale))
        h = max(1, round(im.height * scale))
        im = im.resize((w, h), Image.LANCZOS)
        f = "egg%d.webp" % i
        im.save(os.path.join(ANIM, f), "WEBP", quality=92, method=6)
        # eggs hang on their CENTRE, not their feet: they float, spin and fly to
        # the counter, and every one of those wants the middle of the sprite
        meta.append({"f": f, "w": w, "h": h, "ay": h / 2.0})
        print("   %s %dx%d" % (f, w, h))
    for old in range(len(runs), 16):                     # a shorter cycle than before
        p = os.path.join(ANIM, "egg%d.webp" % old)
        if os.path.exists(p): os.remove(p); print("   removed %s" % os.path.basename(p))
    print(json.dumps(meta, separators=(",", ":")))
    return meta


if __name__ == "__main__":
    main()
