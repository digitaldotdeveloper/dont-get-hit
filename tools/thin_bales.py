# -*- coding: utf-8 -*-
"""Space the hay bales out in the near background layer.

The layer is one tile that loops, so however many stacks are painted on it is
how many the player sees for the whole run. Two per 923px meant a stack every
half screen forever, and the field read as a hay depot.

NOTHING IS DELETED. Bale-free stretches are spliced in instead, which makes the
tile longer and the bales rarer and needs no inpainting at all, because every
pixel is already the right pixel. The splice is invisible because everything
crossing it -- the grass line, the fence rails -- is horizontal, so any x works
as long as the cut misses the posts and the bales.

Deleting a stack was the first instinct and it is a trap. A fence post stands
behind the stack, so the hole needs a donor slab carrying its own post at
exactly the right offset, and on a tile this short no such donor exists. Every
attempt left either a sliver of hay or a hole in the fence.

Finding the bales is the other half, and colour alone will not do it:

  * Bales are found as BLOBS and then filtered BY HEIGHT. The grass is full of
    little yellow buttercups that pass any straw colour test, and the fence
    rail has a straw-coloured highlight running its whole length. Height
    separates them in one number -- a stack is a hundred pixels tall, a
    buttercup is twenty.
  * The blobs are then DILATED before their extent is taken. The colour test
    finds the lit face of a bale and misses its ink outline and the loose straw
    round its foot, so the raw extent is ~40px too narrow at each end, and a
    chunk cut against it contains a sliver of the very thing it is meant to
    avoid.
  * Fence posts are found by OPACITY, not colour: the sky is keyed out of this
    layer, so a post is simply a column opaque all the way up.

    python thin_bales.py            # edits art/bg/near.webp in place
"""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imglib import label

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEAR = os.path.join(ROOT, "art", "bg", "near.webp")

COPIES = 3        # clean stretches to splice in
TALLB  = 18       # a straw blob shorter than this is a flower or a rail highlight
GROW   = 8        # dilate the bales by this before measuring their extent
CLEAR  = 10       # keep cuts this far from a bale or a post


def runs(flags, gap=1):
    xs = np.nonzero(flags)[0]
    if not len(xs): return []
    out, s, p = [], xs[0], xs[0]
    for x in xs[1:]:
        if x - p > gap: out.append((int(s), int(p) + 1)); s = x
        p = x
    out.append((int(s), int(p) + 1))
    return out


def dilate(m, k):
    o = m.copy()
    for _ in range(k):
        s = o.copy()
        s[:, 1:] |= o[:, :-1]; s[:, :-1] |= o[:, 1:]
        s[1:, :] |= o[:-1, :]; s[:-1, :] |= o[1:, :]
        o = s
    return o


def survey(a):
    h, w = a.shape[:2]
    f = a.astype(int)
    r, g, b, al = f[..., 0], f[..., 1], f[..., 2], f[..., 3]
    straw = (al > 60) & (r > 190) & (g > 150) & (g < 228) & (b < 155) & ((r - b) > 70)
    lab, n = label(straw)
    tall = np.zeros_like(straw)
    for i in range(1, n + 1):
        m = lab == i
        if int(m.sum()) < 200: continue
        ys = np.nonzero(m.any(1))[0]
        if ys.max() - ys.min() + 1 > TALLB: tall |= m
    bales = runs(dilate(tall, GROW).any(0), gap=24)
    posts = [p for p in runs((al[:int(h * 0.30)] > 60).mean(0) > 0.8, gap=4)
             if 6 <= p[1] - p[0] <= 44]
    return bales, posts


def main():
    a = np.asarray(Image.open(NEAR).convert("RGBA")).astype(np.uint8).copy()
    h, w = a.shape[:2]
    bales, posts = survey(a)
    print("  %dx%d  bales %s  posts %s" % (w, h, bales, posts))

    free = np.ones(w, bool)
    for c0, c1 in bales: free[max(0, c0 - CLEAR):min(w, c1 + CLEAR)] = False
    cutok = free.copy()
    for p0, p1 in posts: cutok[max(0, p0 - CLEAR):min(w, p1 + CLEAR)] = False

    # the longest run that is bale-free AND can be cut at both ends
    spans = [r for r in runs(free & cutok) if r[1] - r[0] >= 60]
    if not spans:
        print("  nowhere safe to cut"); return
    spans.sort(key=lambda r: r[1] - r[0], reverse=True)
    s0, s1 = spans[0]
    width = s1 - s0
    print("  clean stretch %d..%d (%d px)" % (s0, s1, width))

    # Take the copies at DIFFERENT offsets inside that stretch rather than the
    # same slab N times: three identical slabs of grass in a row reads as a
    # repeat, and overlapping cuts cost nothing because the content is grass.
    picks = []
    for k in range(COPIES):
        off = s0 + int(k * (width * 0.34) / max(1, COPIES - 1)) if COPIES > 1 else s0
        off = min(off, s1 - int(width * 0.66))
        picks.append((off, off + int(width * 0.66)))
    parts = [a[:, :s1]]
    for p0, p1 in picks: parts.append(a[:, p0:p1])
    parts.append(a[:, s1:])
    out = np.concatenate(parts, axis=1)

    Image.fromarray(out, "RGBA").save(NEAR, "WEBP", quality=90, method=6)
    b2, _ = survey(out)
    print("  spliced %s" % (picks,))
    print("  wrote %s: %dx%d, %d stacks, one every %d px (was %d)"
          % (os.path.basename(NEAR), out.shape[1], h, len(b2),
             out.shape[1] // max(1, len(b2)), w // max(1, len(bales))))


if __name__ == "__main__":
    main()
