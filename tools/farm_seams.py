# -*- coding: utf-8 -*-
"""Find where the three farm panels should be cut so the field reads as one.

   The panels are three separate paintings of the same farm, so butting them at
   their own edges leaves the fence jogging and the horizon stepping. Nothing in
   the art says the edges are where the joins should be -- so this searches for
   them: for every pair of columns (one near the end of the left panel, one near
   the start of the right), it scores how well the two would meet, and keeps the
   pair that scores best.

   The score is a column difference weighted down the image: the sky and the
   grass matter, the flat dirt band at the bottom does not, and a column whose
   neighbours also agree is worth more than a lucky single match. Cutting inside
   a fence rail is what makes a join obvious, so a rail that continues at the
   same height across the cut wins by construction.

     python tools/farm_seams.py          # prints the cuts, writes a preview
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import SHEETS, REF, AUDIOSRC, ROOT as GAME, sheets, need
import io, json, sys
from PIL import Image

SRCS = [sheets('v2', 'farm_%s.webp' % k) for k in 'abc']
WINDOW = 0.26          # how far in from each edge to look, as a fraction of width
STEP = 2               # column stride while searching
NEI = 3                # columns either side that must also agree


def columns(im):
    """Every column as a list of RGB rows, weighted so the dirt does not vote."""
    w, h = im.size
    px = im.load()
    rows = [y for y in range(0, h, 3)]
    wts = []
    for y in rows:
        t = y/float(h)
        wts.append(0.15 if t > 0.86 else (1.0 if t > 0.30 else 0.65))
    cols = []
    for x in range(w):
        cols.append([px[x, y] for y in rows])
    return cols, wts


def score(ca, cb, wts):
    s = 0.0
    for i in range(len(wts)):
        a, b = ca[i], cb[i]
        d = abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2])
        s += d*wts[i]
    return s


def best_cut(left, right):
    """-> (cut in left, start in right, score). Content between them is dropped."""
    lc, wts = columns(left)
    rc, _ = columns(right)
    lw, rw = left.width, right.width
    lo = int(lw*(1-WINDOW))
    hi = int(rw*WINDOW)
    best = None
    for a in range(lo, lw-NEI, STEP):
        for b in range(NEI, hi, STEP):
            s = 0.0
            for k in range(-NEI, NEI+1):          # the neighbourhood must agree too
                s += score(lc[a+k], rc[b+k], wts)
            if best is None or s < best[2]: best = (a, b, s)
    return best


def build(preview='_farm_strip.png'):
    ims = [Image.open(s).convert('RGB') for s in SRCS]
    cuts = []
    for i in range(len(ims)):
        j = (i+1) % len(ims)
        a, b, s = best_cut(ims[i], ims[j])
        cuts.append((a, b, s))
        print('%s | %s   cut left at %d/%d, right resumes at %d   (score %.0f)'
              % (SRCS[i][-10:-5], SRCS[j][-10:-5], a, ims[i].width, b, s/1000))
    # each panel runs from where the previous seam resumed to where its own cuts
    spans = []
    for i in range(len(ims)):
        start = cuts[i-1][1]
        end = cuts[i][0]
        spans.append((start, end))
        print('panel %d keeps %d..%d  (%d px of %d)' % (i, start, end, end-start, ims[i].width))
    total = sum(e-s for s, e in spans)
    strip = Image.new('RGB', (total, ims[0].height))
    x = 0
    for im, (s, e) in zip(ims, spans):
        strip.paste(im.crop((s, 0, e, im.height)), (x, 0)); x += e-s
    # the preview shows the loop point too, so a bad wrap is visible
    two = Image.new('RGB', (int(total*1.5), strip.height))
    two.paste(strip, (0, 0)); two.paste(strip.crop((0, 0, total//2, strip.height)), (total, 0))
    two.resize((two.width//2, two.height//2), Image.LANCZOS).save(preview)
    print('strip %dx%d, preview %s' % (strip.size[0], strip.size[1], preview))
    return spans, strip


if __name__ == '__main__':
    spans, strip = build()
    print('SPANS = ' + json.dumps([[s, e] for s, e in spans]))
