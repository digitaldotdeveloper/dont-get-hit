# -*- coding: utf-8 -*-
"""Check every background picture in the game for the faults we have shipped.

    python tools/audit_map.py            # every panel and tile, worst first
    python tools/audit_map.py --all      # ...including the ones that pass

Eyeballing 54 pictures does not work -- half of what is wrong with a panel is
invisible until it is beside its neighbour, and by then it is in the game. Each
check below is a fault that actually reached a screenshot, written down so it
cannot reach one twice:

  CUTOUT EDGE   content touching the frame edge. A panel is placed BESIDE other
                panels, so anything running off its own edge butts into whatever
                the next one starts with -- half a barn door against half an egg
                shelf. (Tiles are exempt: they are MEANT to reach both edges.)
  GROUND RULE   the solid dark bar the generator paints under a row. In the game
                that bar is the edge of a rectangle and the panel reads as
                pasted on.
  HAZARD HUE    anything in the wire's own colour, 165-265 degrees at real
                saturation. Blue means the thing that kills you, everywhere.
  STACKED ROWS  two rows of buildings in a frame that holds one, which comes out
                at half scale with a row floating in the sky.
  THIN FLOOR    a `near` tile is scaled BY ITS HEIGHT, so height is resolution.
                Under ~140px it gets magnified into mush.
  OPEN SEAM     a tile is repeated against ITSELF, so its left and right edges
                have to meet. Scored by comparing the two edge columns.
  SQUAT / TALL  a panel far off the reference aspect is a panel at the wrong
                scale, because the slot places all of them with one number.

Nothing here is a judgement about whether a picture is GOOD. It catches the
mechanical faults; the ones about taste still need eyes."""
import colorsys
import glob
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_ASPECT = 830 / 240.0          # art/bg/mid.webp, which every panel is cut to


# WHAT COUNTS AS THE HAZARD HUE, and it is narrower than "blue-ish".
# The wire is #4CCFFF, hue 197. What competes with it is CYAN THROUGH BLUE,
# 170-250. Violet past that does not: the haze in the lab set is 255-263 dark
# purple-grey silhouettes, and the alien facility and space were given magenta
# accents ON PURPOSE precisely because magenta is nowhere near the wire. A test
# that flags those is a test that would strip the one cool accent the game is
# allowed to have.
def hazard_px(a):
    op = a[..., 3] > 40
    if not op.any():
        return 0
    rgb = a[op][..., :3] / 255.0
    n = 0
    for r, g, b in rgb[::7]:       # every 7th pixel: enough to catch a glow
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if 170 <= h * 360 <= 250 and s > 0.25 and v > 0.25:
            n += 1
    return n * 7


def edge_contact(a):
    """How much of the left and right edge columns has content on it."""
    h = a.shape[0]
    left = (a[:, 0, 3] > 24).sum() / float(h)
    right = (a[:, -1, 3] > 24).sum() / float(h)
    return max(left, right)


def hard_edge(a):
    """Does the picture END ON A STEP, or does it fade out?

       The first version of this asked how TALL the content was at the panel's
       ends, which flagged 22 pictures -- and it was asking the wrong question.
       A corridor has walls; a wall of cells reaches the edge because that is
       what a wall does. Re-rendering all of them would not have fixed
       anything.

       What actually reads as a cut is a hard ALPHA STEP: opaque wall, then
       nothing, in the space of a pixel or two. The cutter fades each panel's
       last 7% for exactly this reason, so the honest test is how far the edge
       takes to go from transparent to solid. A step is a fault; a ramp is the
       fix.

       Returns the fade width as a fraction of the picture's width -- small is
       bad."""
    al = a[..., 3]
    cols = (al > 24).any(axis=0)
    if not cols.any():
        return 1.0
    xs = cols.nonzero()[0]
    w = a.shape[1]
    worst = 1.0
    for x0, step in ((int(xs.min()), 1), (int(xs.max()), -1)):
        run = 0
        for k in range(0, int(w*0.20)):
            x = x0 + step*k
            if x < 0 or x >= w:
                break
            col = al[:, x]
            if col.max() >= 250:              # this column is fully solid
                break
            run += 1
        worst = min(worst, run/float(w))
    return worst


def ground_rule(a):
    """The darkest full-width row in the bottom third, relative to the picture."""
    h, w = a.shape[:2]
    lum, worst = [], 0.0
    for y in range(h):
        row = a[y, ::4]
        op = row[row[..., 3] > 120]
        lum.append(op[..., :3].mean() if len(op) else None)
    body = [l for l in lum if l is not None]
    if not body:
        return 0.0
    med = float(np.median(body))
    for y in range(int(h * 0.66), h):
        row = a[y, ::4]
        op = row[row[..., 3] > 120]
        if len(op) > len(row) * 0.9 and lum[y] is not None and lum[y] < med * 0.55:
            worst = max(worst, 1 - lum[y] / med)
    return worst


def bands(a, gap=14):
    rows = (a[..., 3] > 24).sum(axis=1)
    out, start, empty = [], None, 0
    for y, n in enumerate(rows):
        if n > 0:
            if start is None:
                start = y
            empty = 0
        else:
            if start is not None:
                empty += 1
                if empty >= gap:
                    out.append((start, y - empty)); start = None
    if start is not None:
        out.append((start, len(rows) - 1))
    return [b for b in out if b[1] - b[0] > max(8, a.shape[0] * 0.12)]


def seam(a):
    """RMSE between the first and last columns, on the opaque part."""
    l, r = a[:, 0, :], a[:, -1, :]
    op = (l[:, 3] > 24) | (r[:, 3] > 24)
    if not op.any():
        return 0.0
    return float(np.sqrt(((l[op][:, :3].astype(float) - r[op][:, :3]) ** 2).mean()))


def main():
    show_all = '--all' in sys.argv
    files = sorted(glob.glob(os.path.join(ROOT, 'art', 'bg', '*.webp')) +
                   glob.glob(os.path.join(ROOT, 'art', 'panels', '*', '*.webp')) +
                   [f for w in ('ant', 'deep', 'lab')
                    for f in glob.glob(os.path.join(ROOT, 'art', w, '*.webp'))
                    if os.path.basename(f).split('.')[0] in ('far', 'mid', 'near', 'hang')])
    rows = []
    for f in files:
        rel = os.path.relpath(f, ROOT).replace('\\', '/')
        name = os.path.basename(f).split('.')[0]
        # A TILE IS ANYTHING REPEATED AGAINST ITSELF, which is every slot of the
        # three original worlds plus every floor and ceiling -- those are MEANT
        # to reach both edges, and flagging them as cut-outs is the audit being
        # wrong rather than the art. Only the numbered panels are placed beside
        # a different picture.
        is_tile = (name in ('near', 'hang', 'far', 'mid')
                   or rel.startswith('art/ant/') or rel.startswith('art/deep/')
                   or rel.startswith('art/lab/'))
        a = np.asarray(Image.open(f).convert('RGBA'))
        faults = []

        if not is_tile and edge_contact(a) > 0.10:
            faults.append('CUTOUT EDGE %d%% of an edge column has content' % (edge_contact(a)*100))
        if not is_tile:
            e = hard_edge(a)
            if e < 0.02:
                faults.append('HARD EDGE the picture goes from nothing to solid in %.1f%% '
                              'of its width; it will butt its neighbour' % (e*100))
        # Only a PANEL can have a false ground rule. A floor tile's bottom IS
        # the ground line -- it sits on the road, which is drawn over it -- so a
        # dark horizontal band down there is the edge of the plating or the foot
        # of the bank, and flagging it is the audit not knowing what it is
        # looking at. Checked and confirmed on cia/near: a cable tray and a
        # floor plate, exactly as drawn.
        g = 0.0 if is_tile else ground_rule(a)
        if g > 0.30:
            faults.append('GROUND RULE a dark bar %d%% under the picture' % (g*100))
        hz = hazard_px(a)
        if hz > 40:
            faults.append('HAZARD HUE ~%d px in the wire colour' % hz)
        if not is_tile and len(bands(a)) > 1:
            faults.append('STACKED ROWS %d bands' % len(bands(a)))
        if name == 'near' and a.shape[0] < 140:
            faults.append('THIN FLOOR only %dpx tall; it gets magnified' % a.shape[0])
        if is_tile and name in ('near', 'hang'):
            sm = seam(a)
            if sm > 60:
                faults.append('OPEN SEAM edges differ by %.0f' % sm)
        if not is_tile:
            asp = a.shape[1] / float(a.shape[0])
            if abs(asp - REF_ASPECT) > 0.6:
                faults.append('ASPECT %.2f against the reference %.2f' % (asp, REF_ASPECT))
        rows.append((len(faults), rel, faults))

    rows.sort(key=lambda r: -r[0])
    bad = [r for r in rows if r[0]]
    for n, rel, faults in (rows if show_all else bad):
        print('%-34s %s' % (rel, '; '.join(faults) if faults else 'ok'))
    print('\n%d pictures checked, %d with something to answer for.' % (len(rows), len(bad)))


if __name__ == '__main__':
    main()
