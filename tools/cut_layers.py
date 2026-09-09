# -*- coding: utf-8 -*-
"""Cut a world's FLOOR and CEILING tiles, and make them loop.

    python tools/cut_layers.py --list
    python tools/cut_layers.py                 # every tile that has a render
    python tools/cut_layers.py prison_near     # just one

A PANEL AND A TILE ARE CUT DIFFERENTLY, and the difference is the whole reason
this is a separate file from cut_mid_panels.py.

A panel is placed BESIDE other panels, so it wants empty margins and its own
frame. A tile is repeated against ITSELF forever, so what it wants is a SEAM:
a left edge and a right edge that meet. The generator will not give you that
however politely you ask -- it is asked anyway, because asking gets it close --
so the seam is SEARCHED FOR the way tools/bg_layers.py has always done it:
score columns near the right-hand edge against columns near the left, keep the
pair that matches best, and crop between them. What is left tiles.

The two slots are then trimmed differently, because they hang from opposite
edges of the world:

    near   stands on the ground, so its BOTTOM is the ground line and the
           painted rule under it (if the generator drew one) comes off.
    hang   drops from the ceiling, so its TOP is the anchor and the empty air
           beneath it is content -- cropping that away would pull the roots up
           out of frame.

Sizes are taken from the world they are joining rather than invented: the ant
set's own near and hang are the reference, so a new world's floor sits at the
same height as the floor it replaces."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bg_layers as BL                                       # noqa: E402
from gen_mid_panels import LAYERS                            # noqa: E402
from cut_mid_panels import candidates_for, strip_baseline     # noqa: E402
from PIL import Image                                        # noqa: E402
import numpy as np                                           # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# how much of each edge to search for the seam; a busy tile needs a wider net
WINDOW = 0.26


def content_box(im):
    al = np.array(im)[..., 3] > 24
    if not al.any():
        return None
    ys, xs = np.where(al)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def cut(name, src):
    world, slot = name.split('_')
    im = BL.key_magenta(Image.open(src))

    seam = BL.loop_seam(im, WINDOW)
    if seam:
        b, a, _score = seam
        im = im.crop((b, 0, a, im.height))

    if slot in ('near', 'far'):
        im = strip_baseline(im)
        box = content_box(im)
        if box:                       # keep the full width, trim only the air above
            im = im.crop((0, box[1], im.width, im.height))
    else:
        box = content_box(im)
        if box:                       # keep the top edge; the air below is the point
            im = im.crop((0, 0, im.width, box[3]))

    # THE TILE IS SCALED BY ITS HEIGHT, so height is resolution here. The floor
    # is drawn about 190 world units tall whatever the source is: a 33px band
    # gets magnified twelvefold and turns to mush, and no later stage can undo
    # that. The reference floors are 172-242px, so anything under 140 is called
    # out rather than quietly shipped.
    warn = ''
    if slot == 'near' and im.height < 140:
        warn = '   <-- ONLY %dpx TALL, it will be magnified; re-render it' % im.height

    out_dir = os.path.join(ROOT, 'art', 'panels', world)
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, slot + '.webp')
    im.save(dst, 'WEBP', lossless=True, quality=100, method=6)
    return dst, im.size, warn


def main():
    want = [a for a in sys.argv[1:] if not a.startswith('--')] or list(LAYERS)
    cands = candidates_for(LAYERS)
    if '--list' in sys.argv:
        for n in LAYERS:
            v = cands.get(n, [])
            print('  %-13s %d take(s)%s' % (n, len(v), '' if v else '   <-- nothing back'))
        return
    for name in want:
        src = (cands.get(name) or [None])[0]
        if not src:
            print('  %-13s no render yet -- skipped' % name)
            continue
        dst, size, warn = cut(name, src)
        print('  %-13s %4dx%-4d  %5.1f KB  -> %s%s'
              % (name, size[0], size[1], os.path.getsize(dst)/1024.0,
                 os.path.relpath(dst, ROOT), warn))


if __name__ == '__main__':
    main()
