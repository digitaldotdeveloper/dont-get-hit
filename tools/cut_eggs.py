# -*- coding: utf-8 -*-
"""Build the golden egg's ten-frame spin from ONE painted egg.

Generating ten frames of a spin and slicing them was how the old set was made,
and it drifts: every frame is a separate drawing, so the silhouette wobbles and
the highlight jumps. Here the spin is DERIVED. One hero egg is painted, and the
frames are that egg turned on its vertical axis -- width scaled by |cos t|, the
far half drawn mirrored and knocked back a little so it reads as the reverse
face. The loop is then exact by construction and the egg cannot wobble.

    python cut_eggs.py          # sheets/v2/egg_hero.png -> anim/egg0..9.webp
"""
import os, sys, json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imglib import key_green, despill, bbox

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH   = os.path.join(ROOT, "sheets", "v2")
ANIM = os.path.join(ROOT, "anim")

TALL = 58               # frame height in sprite pixels, unchanged from the old set
BACK = 0.86             # the reverse face is knocked back to this much

# Width per frame, as a fraction of the widest. This is NOT |cos t|: a true
# cosine spends a third of the cycle edge-on, and an egg you cannot see is a
# pickup the player cannot read. These are the proportions the hand-made set
# used -- mostly facing you, with one quick flick through the edge -- measured
# off it and kept.
SPIN = [1.00, .96, .91, .83, .47, .32, .83, .87, .89, .91]
FRONT = 5               # the first five face you; the rest are the reverse


def main():
    rgba = despill(key_green(Image.open(os.path.join(SH, "egg_hero.png"))))
    bb = bbox(rgba[..., 3] > 0)
    hero = Image.fromarray(rgba[bb[1]:bb[3], bb[0]:bb[2]], "RGBA")
    hero = hero.resize((max(1, round(TALL * hero.width / hero.height)), TALL), Image.LANCZOS)

    back = Image.fromarray(np.dstack([
        np.clip(np.asarray(hero)[..., :3] * BACK, 0, 255).astype(np.uint8),
        np.asarray(hero)[..., 3]]), "RGBA").transpose(Image.FLIP_LEFT_RIGHT)

    meta = []
    for i, f_w in enumerate(SPIN):
        front = i < FRONT
        src = hero if front else back
        w = max(1, round(hero.width * f_w))
        im = src.resize((w, TALL), Image.LANCZOS)
        f = "egg%d.webp" % i
        im.save(os.path.join(ANIM, f), "WEBP", quality=90, method=6)
        # eggs hang on their CENTRE, not their feet: they float, spin and fly to
        # the counter, and every one of those wants the middle of the sprite
        meta.append({"f": f, "w": w, "h": TALL, "ay": TALL / 2.0})
        print("  %s %dx%d  %s" % (f, w, TALL, "front" if front else "back"))
    print(json.dumps(meta, separators=(",", ":")))
    return meta


if __name__ == "__main__":
    main()
