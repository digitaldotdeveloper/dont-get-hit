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
white can be glaring against the wash it actually sits on."""
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
    return sorted(f for f in glob.glob(os.path.join(d, '*.webp'))
                  if os.path.basename(f) not in ('near.webp', 'hang.webp'))


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
        print('  %-7s %d panels, %d joins  -> %s' % (world, len(ims), len(ims) - 1,
                                                     os.path.relpath(p, ROOT)))


if __name__ == '__main__':
    main()
