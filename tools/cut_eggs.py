# -*- coding: utf-8 -*-
"""Assemble the golden egg's spin from a painted turnaround sheet.

Three approaches were tried and the first two are written up here because both
are tempting and both are wrong:

  1. Squash one hero egg horizontally per frame. The silhouette narrows but the
     highlight stays welded to the surface, so the eye reads a picture being
     scaled rather than an object turning. This is what "cheap" looks like.
  2. Wrap the painting round a solid of revolution and re-project it -- a pixel
     at horizontal position u sits at surface angle asin(u), so after turning by
     t it is seen at sin(asin(u) + t). The model is correct and the output was
     striped: the mapping crushes the whole texture into a few columns at the
     silhouette, so a handful of source pixels smear across the edge. Doing it
     properly wants real area sampling.

So the SHADING is painted, per angle, and only the WIDTH is set here. That
split is the point: the thing that has to be hand-drawn is the thing a program
cannot fake -- bands that curve round the form like lines of longitude, a warm
bounce light hugging the dark limb, a bright polished rim at the edge -- and the
thing a program should own is the one number the artist cannot hold steady
across ten drawings, the silhouette width.

The sheet comes back in whatever order the model felt like, so frames are picked
by MEASUREMENT: width says how far round it is, mean brightness says whether it
is the lit face or the reverse. `CYCLE` then lays them out on a cosine, and the
second half of the turn reuses the first half's art MIRRORED, which is what a
symmetric object actually does and stops the loop reading as a repeat.

    python cut_eggs.py          # sheets/v2/egg_spin.png -> anim/egg*.webp
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import SHEETS, REF, AUDIOSRC, ROOT as GAME, sheets, need
import os, sys, json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imglib import key_green, despill, bbox, label

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH   = sheets("v2")
ANIM = os.path.join(ROOT, "anim")

TALL = 62        # frame height in sprite pixels
# TWELVE, not ten. At 36 degrees a step no frame lands on 90, so there is no
# true edge-on view and the nearest two are a third of full width -- which put
# FOUR of ten frames into a sliver and turned a run of eggs into a row of
# splinters. At 30 degrees a step the edge is hit exactly, twice, and only twice.
N    = 12
# And the width is eased. A raw |cos t| crowds the cycle toward the edge; the
# exponent fattens the middle so the egg reads as a solid object turning, with
# one quick flick through the edge, which is what the hand-made set did.
EASE = 0.70
MINW = 0.22      # the edge-on frame keeps this much width; 0 would vanish
MAXF = 16        # tidy up frames left by a longer previous cycle
# The painted reverse is genuinely dark, which is right for a lit object and
# wrong for a pickup: half a cycle of dark brown reads as the egg flickering out
# of existence rather than turning. Lifted to about four fifths of the lit face,
# which keeps it obviously the shadow side while keeping it obviously gold.
LIFT = 1.34


def read_sheet(path):
    """Every egg on the sheet, with the two measurements that place it."""
    rgba = despill(key_green(Image.open(path)))
    lab, n = label(rgba[..., 3] > 0)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        if int(m.sum()) < 2500: continue
        bb = bbox(m)
        sub = rgba[bb[1]:bb[3], bb[0]:bb[2]].copy()
        sub[..., 3] = np.where(m[bb[1]:bb[3], bb[0]:bb[2]], sub[..., 3], 0)
        px = sub[..., :3][sub[..., 3] > 60]
        out.append({"img": sub, "w": bb[2] - bb[0], "lum": float(px.mean())})
    return out


def main():
    fr = read_sheet(os.path.join(SH, "egg_spin.png"))
    wide = max(f["w"] for f in fr)
    # EDGES FIRST, then lit vs reverse. Splitting the whole sheet on median
    # brightness put the edge-on views -- which are mid-toned by nature, being
    # mostly rim -- into the reverse pool, where LIFT then brightened them into
    # pale slivers. Width says which frames are edges; only the WIDE ones get
    # sorted by brightness, and the split is taken at their biggest GAP rather
    # than at a median, because a median splits a group in half whether or not
    # there are two groups to split.
    edges = [f for f in fr if f["w"] < wide * 0.60]
    body  = sorted([f for f in fr if f["w"] >= wide * 0.60], key=lambda f: f["lum"])
    gaps  = [(body[i+1]["lum"] - body[i]["lum"], i) for i in range(len(body)-1)]
    cut   = max(gaps)[1] if gaps else 0
    back  = sorted(body[:cut+1], key=lambda f: -f["w"])
    front = sorted(body[cut+1:], key=lambda f: -f["w"])
    if not front: front, back = back, front
    if not back: back = front[-2:]
    if not edges: edges = front[-1:]
    print("  %d on the sheet: %d lit, %d reverse, %d edge"
          % (len(fr), len(front), len(back), len(edges)))

    def pick(pool, frac):
        """the drawing whose own width is closest to the angle we want"""
        return min(pool, key=lambda f: abs(f["w"]/wide - frac))

    meta = []
    for i in range(N):
        t = i * 2 * np.pi / N
        c = np.cos(t)
        frac = max(MINW, abs(c) ** EASE)
        edge = abs(c) < 0.2
        src = pick(edges if edge else (front if c >= 0 else back), frac)
        art = src["img"]
        if c < 0 and not edge:
            art = art.copy()
            art[..., :3] = np.clip(art[..., :3].astype(np.float32) * LIFT, 0, 255).astype(np.uint8)
        im = Image.fromarray(art, "RGBA")
        # the back half of the turn is the front half seen from the other side
        if i > N // 2: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        h = TALL
        w = max(1, round(wide * frac * (TALL / im.height)))
        im = im.resize((w, h), Image.LANCZOS)
        f = "egg%d.webp" % i
        im.save(os.path.join(ANIM, f), "WEBP", quality=92, method=6)
        # eggs hang on their CENTRE, not their feet: they float, spin and fly to
        # the counter, and every one of those wants the middle of the sprite
        meta.append({"f": f, "w": w, "h": h, "ay": h / 2.0})
        print("   %s %2dx%d  %s" % (f, w, h, "edge" if edge else ("lit" if c >= 0 else "reverse")))
    for old in range(N, MAXF):
        p = os.path.join(ANIM, "egg%d.webp" % old)
        if os.path.exists(p): os.remove(p); print("   removed %s" % os.path.basename(p))
    print(json.dumps(meta, separators=(",", ":")))
    return meta


if __name__ == "__main__":
    main()
