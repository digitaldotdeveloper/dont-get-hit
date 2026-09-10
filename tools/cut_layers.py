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


# Where a world's tiles actually live. The six worlds past the empire keep their
# own folder; the farm and the ant empire predate that and their tiles sit in
# the directories the game has always loaded them from. `terr` runs on the
# farm's layer set, so it shares the farm's floor.
TILE_DIR = {'farm': ('art', 'bg'), 'terr': ('art', 'bg'), 'empire': ('art', 'ant')}


def cut(name, src):
    world, slot = name.split('_')
    im = BL.key_magenta(Image.open(src))

    # A PILLAR IS NOT A TILE. It is a single object, cut out and stamped onto the
    # ends of a world's panels by tools/connect.py so that any two of them meet
    # on a column instead of on a strip of blank wall. It never repeats, so it
    # gets no loop seam and no anchoring -- just the cut-out, trimmed to itself.
    if slot == 'pillar':
        box = content_box(im)
        if box:
            im = im.crop(box)
        out_dir = os.path.join(ROOT, 'tools', 'pillars')
        os.makedirs(out_dir, exist_ok=True)
        dst = os.path.join(out_dir, world + '.webp')
        im.save(dst, 'WEBP', lossless=True, quality=100, method=6)
        return dst, im.size, ''

    seam = BL.loop_seam(im, WINDOW)
    if seam:
        b, a, _score = seam
        im = im.crop((b, 0, a, im.height))

    if slot == 'upper':
        pass
    elif slot.startswith('near') or slot == 'far':
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
    if slot.startswith('near') and im.height < 140:
        warn = '   <-- ONLY %dpx TALL, it will be magnified; re-render it' % im.height

    out_dir = os.path.join(ROOT, *TILE_DIR.get(world, ('art', 'panels', world)))
    os.makedirs(out_dir, exist_ok=True)

    # A VARIANT MUST BE THE EXACT SIZE OF THE TILE IT STANDS IN FOR. The game
    # computes the whole slot's geometry from ONE image -- bgGeom reads
    # L.img.naturalWidth/Height and every tile in that slot is drawn at the
    # size it produces. A variant cut half a pixel wider is not drawn wider, it
    # is drawn STRETCHED, and its ground line lands somewhere else. The loop
    # seam search crops to wherever the join happens to be, so this is not a
    # rare case; it is every time.
    base = os.path.join(out_dir, 'near.webp') if slot.startswith('near') else None
    if base and slot != 'near' and os.path.exists(base):
        bw, bh = Image.open(base).size
        if im.size != (bw, bh):
            im = im.resize((bw, bh), Image.LANCZOS)
            warn += '   (fitted to %dx%d, the size of near.webp)' % (bw, bh)

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
