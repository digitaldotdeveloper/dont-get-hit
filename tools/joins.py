# -*- coding: utf-8 -*-
"""Show every panel JOIN in the map, so cut-outs are found here and not in play.

    python tools/joins.py           # one strip per world into tools/_joins/

A cut-out is almost never visible in the panel on its own -- it is visible where
that panel MEETS the next one. Screenshotting the running game finds those one
at a time and only where the player happened to be standing, which is a slow
way to audit 42 pictures. This butts each world's panels together exactly as
the game tiles them, on that world's own sky colour, so every join in the map
is on one page.

The sky colours are lifted from ZONES in index.html: a join that looks fine on
white can be glaring against the wash it actually sits on.

WHAT THIS MEASURES IS THE FILES, AND THE GAME NO LONGER DRAWS THEM THIS WAY.
Panels now OVERLAP by MID_OVERLAP (7%) with a ramp down each left edge, so a
join on screen is a dissolve and not a butt. The numbers below are therefore a
WORST CASE -- the step that would show if the panels were laid end to end -- and
they stay useful for exactly that: they rank which pairs disagree most, which is
what tells you a panel is from a different building. Do not read a colour of 60
as something a player can see; read it as sixty more than the pair below it."""
import glob
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tools', '_joins')

# world -> (panel files in the order the game cycles them, sky colour behind)
SKY = {
    'farm':   '#E4AC3C', 'terr':   '#C48A30', 'empire': '#56382A',
    'prison': '#3A3A32', 'cherno': '#333C24', 'cia':    '#34322A',
    'area51': '#3E2A22', 'alien':  '#3C2440', 'space':  '#170E1C',
}


def rgb(h):
    return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))


def panels_for(world):
    if world == 'farm':
        fs = [os.path.join(ROOT, 'art', 'bg', 'mid.webp')]
        fs += sorted(glob.glob(os.path.join(ROOT, 'art', 'bg', 'mid[0-9].webp')))
        return fs
    if world == 'terr':
        return sorted(glob.glob(os.path.join(ROOT, 'art', 'bg', 'tr[0-9].webp')))
    d = os.path.join(ROOT, 'art', 'panels', world)
    TILES = ('near', 'near2', 'near3', 'hang', 'far', 'mid', 'upper')
    return sorted(f for f in glob.glob(os.path.join(d, '*.webp'))
                  if os.path.basename(f).split('.')[0] not in TILES)


def join_step(a, b):
    """How badly panel A's right edge disagrees with panel B's left edge.

       The strips show whether a join reads as continuous; this says so as a
       number, which is the only way to tell a real improvement from a hopeful
       one. Both columns are compared over the rows where EITHER has content,
       on colour and on coverage:

         colour   RMSE between the two edge columns. A wall continuing into the
                  next picture matches; a different room does not.
         profile  how differently the two columns are filled. A wall that stops
                  at two thirds height beside one that reaches the top is a step
                  even when the colours agree.

       Panels are placed in a ring -- the last one is followed by the first
       again -- so the wrap join is measured too. It is the one nobody ever
       looks at and it is on screen as often as the others."""
    import numpy as np
    l = np.asarray(a)[:, -1, :].astype(float)
    r = np.asarray(b)[:, 0, :].astype(float)
    on = (l[:, 3] > 24) | (r[:, 3] > 24)
    if not on.any():
        return 0.0, 0.0
    col = float(np.sqrt(((l[on][:, :3] - r[on][:, :3]) ** 2).mean()))
    prof = float(np.abs((l[:, 3] > 24).astype(float) - (r[:, 3] > 24)).mean() * 100)
    return col, prof


def main():
    os.makedirs(OUT, exist_ok=True)
    for world, sky in SKY.items():
        fs = panels_for(world)
        if not fs:
            continue
        ims = [Image.open(f).convert('RGBA') for f in fs]
        h = max(i.height for i in ims)
        w = sum(i.width for i in ims)
        strip = Image.new('RGBA', (w, h + 30), rgb(sky) + (255,))
        x = 0
        for f, im in zip(fs, ims):
            strip.alpha_composite(im, (x, h - im.height))
            x += im.width
        # mark where each join falls, under the strip, so they are easy to find
        from PIL import ImageDraw
        d = ImageDraw.Draw(strip)
        x = 0
        for im in ims[:-1]:
            x += im.width
            d.line([(x, h), (x, h + 26)], fill=(255, 64, 64, 255), width=3)
        p = os.path.join(OUT, '%s.png' % world)
        strip.convert('RGB').save(p)
        steps = []
        for i in range(len(ims)):
            c, pr = join_step(ims[i], ims[(i + 1) % len(ims)])
            steps.append((c, pr, os.path.basename(fs[i]).split('.')[0],
                          os.path.basename(fs[(i + 1) % len(ims)]).split('.')[0]))
        worst = max(steps)
        print('  %-7s %d panels  worst join %s|%s  colour %5.1f  profile %4.1f%%  -> %s'
              % (world, len(ims), worst[2], worst[3], worst[0], worst[1],
                 os.path.relpath(p, ROOT)))
        if '-v' in sys.argv:
            for c, pr, x, y in steps:
                print('        %-4s|%-4s colour %5.1f  profile %4.1f%%' % (x, y, c, pr))


if __name__ == '__main__':
    main()
