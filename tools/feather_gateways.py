# -*- coding: utf-8 -*-
"""Soften the vertical edges of the gateway sprites.

    python tools/feather_gateways.py            # report
    python tools/feather_gateways.py --write

A gateway stands on a zone boundary so the layer seam cuts behind something
solid. That works only while the sprite itself has no visible edge -- and the
lab door does: it was generated as a door SET INTO A WALL, so it comes with its
own rectangle of packed earth, and that rectangle's left and right borders are
two hard vertical lines sliding across a scene that does not match them.

Scaling it past the screen width hid the edges at the moment of crossing and
not on the approach, which is where the "background is not synced" came from.

So the sides are feathered: an alpha ramp over the outer `FEATHER` of the
width, leaving the middle untouched. The earth then dissolves into whatever
layer is behind it instead of ending. The TOP is left alone -- it is already
sky-side and reads as the top of a wall -- and so is the bottom, which sits
under the road.

The ant empire's gate is a root mound with an organic silhouette and no such
rectangle, so it is not in the list; feathering it would only eat its roots."""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'art', 'ant')
TARGETS = ['lab_door']
FEATHER = 0.16          # of the width, each side


def main():
    write = '--write' in sys.argv
    for name in TARGETS:
        p = os.path.join(ART, name + '.webp')
        if not os.path.exists(p):
            print('  %-10s missing' % name)
            continue
        im = Image.open(p).convert('RGBA')
        w, h = im.size
        a = im.split()[3]
        px = a.load()
        n = max(1, int(w*FEATHER))
        # how opaque the edges are now -- if they are already soft, say so
        edge = sum(px[0, y] for y in range(0, h, 7)) / max(1, len(range(0, h, 7)))
        print('  %-10s %dx%d  left-edge alpha %.0f -> feathering %d px each side'
              % (name, w, h, edge, n))
        if not write:
            continue
        for x in range(n):
            k = x/float(n)
            k = k*k*(3-2*k)                      # smoothstep, so the ramp has no corner
            for y in range(h):
                px[x, y] = int(px[x, y]*k)
                px[w-1-x, y] = int(px[w-1-x, y]*k)
        im.putalpha(a)
        im.save(p, 'WEBP', quality=92, method=6, exact=True)
        print('             written  %d KB' % (os.path.getsize(p)//1024))
    if not write:
        print('  dry run: pass --write')


if __name__ == '__main__':
    main()
