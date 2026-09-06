# -*- coding: utf-8 -*-
"""Take unwanted things out of a parallax layer, by SPLICING not painting.

    python tools/strip_layer_bits.py            # report what it found
    python tools/strip_layer_bits.py --write

Two removals, both asked for and both for the same reason -- a background is
allowed to be interesting and is not allowed to look like gameplay:

  bales      the hay stacks along the farm fence (art/bg/near.webp)
  antholes   the round tunnel mouths in the earth bank (art/ant/near.webp),
             which sit at running height and read as something you can enter
             or crash into

NOTHING IS PAINTED OUT AND NOTHING IS BLURRED. Both layers are long strips of
repeating material, so a column band containing the unwanted thing is replaced
with a column band from somewhere else in the SAME strip that does not. Every
pixel afterwards is a pixel the artist drew, at its own scale, with its own
grain -- which is the difference between removing something and smudging it.
It is the same trick tools/thin_bales.py uses to space the bales out, turned up
to take them away entirely.

The strip has to keep looping, so the replacement is taken from the middle and
the two ends are never used as a source."""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imglib import label                                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JOBS = {
    'bales':    os.path.join(ROOT, 'art', 'bg', 'near.webp'),
    'antholes': os.path.join(ROOT, 'art', 'ant', 'near.webp'),
}
PAD = 6            # widen each find, so an edge never survives the splice


def runs(flags, gap=2):
    xs = np.nonzero(flags)[0]
    if not len(xs):
        return []
    out, s, p = [], xs[0], xs[0]
    for x in xs[1:]:
        if x - p > gap:
            out.append((int(s), int(p) + 1)); s = x
        p = x
    out.append((int(s), int(p) + 1))
    return out


def find(kind, a):
    """-> a boolean per column: does this column contain the thing?"""
    f = a.astype(int)
    r, g, b, al = f[..., 0], f[..., 1], f[..., 2], f[..., 3]
    h = a.shape[0]
    if kind == 'bales':
        # straw: bright, warm, and much yellower than it is blue
        m = (al > 60) & (r > 185) & (g > 145) & (g < 232) & (b < 160) & ((r - b) > 70)
        # ignore the thin scatter -- flowers and rail highlights are the same colour
        return m.sum(0) > h*0.06
    # ant holes
    # A threshold on darkness alone matched 114% of the width: every ink
    # outline in the bank is dark, and there are outlines everywhere. A hole is
    # not "dark", it is a dark BLOB -- so find connected dark regions and keep
    # the ones big enough and round enough to be a bore. That is the same
    # lesson the truck's wheels taught: label the shapes, do not threshold the
    # pixels.
    dark = (al > 60) & (r < 104) & (g < 80) & (b < 70)
    lab, n = label(dark)
    keep = np.zeros(a.shape[1], bool)
    for i in range(1, n + 1):
        m = lab == i
        px = int(m.sum())
        if px < 260:
            continue
        ys, xs = np.nonzero(m)
        bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        if bw < 14 or bh < 14:
            continue
        if bw > a.shape[1]*0.35 or bh > h*0.85:      # a long outline, not a hole
            continue
        if px < bw*bh*0.30:                          # too sparse to be a bore
            continue
        keep[xs.min():xs.max() + 1] = True
    return keep


def main():
    write = '--write' in sys.argv
    for kind, path in JOBS.items():
        if not os.path.exists(path):
            print('  %-9s missing: %s' % (kind, path)); continue
        im = Image.open(path).convert('RGBA')
        a = np.array(im)
        w = a.shape[1]
        cols = find(kind, a)
        bands = [(max(0, s - PAD), min(w, e + PAD)) for s, e in runs(cols)]
        clean = np.ones(w, bool)
        for s, e in bands:
            clean[s:e] = False
        total = sum(e - s for s, e in bands)
        print('  %-9s %4dpx wide, %d band(s) to remove covering %d px (%.0f%%)'
              % (kind, w, len(bands), total, 100.0*total/w))
        if not bands:
            continue
        # the widest clean stretch, kept away from the looping edges
        inner = clean.copy()
        inner[:int(w*0.06)] = False
        inner[int(w*0.94):] = False
        src = max(runs(inner), key=lambda p: p[1] - p[0], default=None)
        if not src or src[1] - src[0] < 24:
            print('             no clean stretch big enough to splice from -- skipped')
            continue
        print('             splicing from clean columns %d..%d' % src)
        if not write:
            continue
        out = a.copy()
        sw = src[1] - src[0]
        for s, e in bands:
            for i, x in enumerate(range(s, e)):
                out[:, x] = a[:, src[0] + (i % sw)]
        Image.fromarray(out, 'RGBA').save(path, 'WEBP', quality=92, method=6, exact=True)
        print('             written  %d KB' % (os.path.getsize(path)//1024))
    if not write:
        print('  dry run: pass --write')


if __name__ == '__main__':
    main()
