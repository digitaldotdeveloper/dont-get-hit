# -*- coding: utf-8 -*-
"""Cut the dynamite fireball into six registered frames.

   The strip came back the way the exhaust flame did -- one row, six boxes,
   green gaps between them -- which is what the "EXACTLY 6 SEPARATE PICTURES"
   wording is for. THE OTHER TWO TAKES CAME BACK AS TWO ROWS OF FIVE, which
   col_split cannot read and which is the whole reason three takes are asked
   for; the pick is recorded below rather than remembered.

   REGISTRATION FOR THIS CYCLE IS THE CENTRE OF THE BURST, and that is the one
   easy case in this project: an explosion is radially symmetric, so each
   frame's own bounding box IS centred on the blast. Every frame is pasted into
   a square the size of the biggest one, so the game can draw all six at one
   scale off one anchor and the fireball grows from a fixed point instead of
   swimming about. (Compare the crow, where the bbox is mostly wing and had to
   be thrown away in favour of the beak.)

     python tools/cut_boom.py --list   contact sheet of the takes
     python tools/cut_boom.py          cut the pick into art/fx/blast*.webp
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from paths import sheets, need
from imglib import key_green, col_split, bbox

SRC  = sheets('v6')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'art', 'fx')
N    = 6
SIZE = 256          # drawn at roughly 430 world units, so this is not oversampled

# The take that came back as ONE row. The other two split into two rows of
# five, which is not a cycle this or any cutter can read.
PICK = '1788975277137'


def takes():
    return sorted(f for f in os.listdir(SRC)
                  if f.startswith('2d-mobile-game-sprite-art') and f.endswith('.png'))


def main():
    hit = [f for f in takes() if PICK in f]
    if not hit:
        raise SystemExit('no take matching %s in %s' % (PICK, SRC))
    im = Image.open(os.path.join(SRC, hit[0])).convert('RGB')
    rgba = key_green(im)
    alpha = rgba[..., 3]
    runs = col_split(alpha, N, minrun=10)
    if len(runs) != N:
        raise SystemExit('found %d columns, wanted %d -- look at --list' % (len(runs), N))

    cuts = []
    for x0, x1 in runs:
        sub = rgba[:, x0:x1]
        b = bbox(sub[..., 3])
        if not b:
            raise SystemExit('empty frame in the strip')
        y0, y1 = b[1], b[3]
        cuts.append(Image.fromarray(sub[y0:y1], 'RGBA'))

    side = max(max(c.size) for c in cuts)
    os.makedirs(OUT, exist_ok=True)
    for i, c in enumerate(cuts):
        sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
        sq.paste(c, ((side - c.width)//2, (side - c.height)//2))
        sq = sq.resize((SIZE, SIZE), Image.LANCZOS)
        dst = os.path.join(OUT, 'blast%d.webp' % i)
        sq.save(dst, 'WEBP', lossless=True)
        print('blast%d  %-14s -> %s  %.1f KB'
              % (i, '%dx%d' % c.size, os.path.basename(dst),
                 os.path.getsize(dst)/1024))
    print('square: %d px, so all six share one anchor and one scale' % side)


def contact():
    from PIL import ImageDraw
    fs = takes()
    W = 1100
    sh = Image.new('RGB', (W, 210*len(fs)), (18, 10, 30))
    d = ImageDraw.Draw(sh)
    for i, f in enumerate(fs):
        p = Image.open(os.path.join(SRC, f)).convert('RGB')
        p.thumbnail((W, 200), Image.LANCZOS)
        sh.paste(p, (0, i*210))
        d.text((6, i*210+2), f[-18:-6], fill=(255, 213, 74))
    out = os.path.join(SRC, '_boom_takes.png')
    sh.save(out)
    print('contact sheet: %s' % out)


if __name__ == '__main__':
    need(SRC)
    contact() if '--list' in sys.argv else main()
