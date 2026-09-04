# -*- coding: utf-8 -*-
"""Cut the generated parallax layers into looping, transparent tiles.

   Three layers, generated separately by tools/gen_bg.py so they can move at
   different speeds: hills, then the farm, then the fence you run past. Each is
   asked for on a flat magenta field instead of a painted sky -- magenta is in
   none of the palettes, so it keys out cleanly, and keying it is the whole
   point: the game draws ONE sky behind everything and no layer ever has to
   agree with another about what colour the sky is.

   Each layer also has to loop. A generator will not give you that, so the seam
   is searched for the same way tools/farm_seams.py searches: score the columns
   near the right-hand edge against the columns near the left, keep the pair
   that matches best, and crop between them. What is left tiles.

     python tools/bg_layers.py           # -> art/bg/far|mid|near.webp
"""
import os, sys
from PIL import Image

SRC = 'sheets/v3'
OUT = 'art/bg'
# (source file, layer name, how much of the left/right edge to search)
LAYERS = [
    ('2d-side-scrolling-mobile-game-background-art-b-1788517217695-1.png', 'far',  0.30),
    ('2d-side-scrolling-mobile-game-background-art-b-1788517257993-1.png', 'mid',  0.22),
    ('2d-side-scrolling-mobile-game-background-art-b-1788517312713-1.png', 'near', 0.26),
]
STEP = 2


def key_magenta(im):
    """Magenta out, and pull the fringe off whatever it touched."""
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()
    def magenta(c):
        return c[0] > 150 and c[2] > 150 and c[1] < 110 and (c[0]-c[1]) > 60 and (c[2]-c[1]) > 60
    for y in range(h):
        for x in range(w):
            if magenta(px[x, y]): px[x, y] = (0, 0, 0, 0)
    # the half-keyed pixels around an edge read as a purple rim over a blue sky
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if not c[3]: continue
            if c[0] > c[1] + 40 and c[2] > c[1] + 40:
                g = c[1]
                px[x, y] = (min(c[0], g + 40), g, min(c[2], g + 40), 190)
    return im


def loop_seam(im, window):
    """-> (x0, x1) to crop, so the left and right edges meet."""
    w, h = im.size
    px = im.load()
    rows = [y for y in range(0, h, 3)]
    def col(x):
        return [px[x, y] for y in rows]
    def diff(a, b):
        s = 0
        for ca, cb in zip(a, b):
            if ca[3] == 0 and cb[3] == 0: continue
            s += abs(ca[0]-cb[0]) + abs(ca[1]-cb[1]) + abs(ca[2]-cb[2]) + abs(ca[3]-cb[3])*2
        return s
    left = range(0, int(w*window), STEP)
    right = range(int(w*(1-window)), w, STEP)
    lc = {x: col(x) for x in left}
    rc = {x: col(x) for x in right}
    best = None
    for a in right:
        for b in left:
            if a - b < w*0.45: continue          # keep a decent length
            s = diff(rc[a], lc[b])
            if best is None or s < best[2]: best = (b, a, s)
    return best


def trim_baseline(im):
    """Drop the solid dark rule the generator paints along the ground line.

       It is a fine detail in a picture that stands on its own and a hard black
       rule straight across the farm once the buildings are standing in a field
       the game draws -- so the rows that are opaque all the way across AND dark
       all the way across come off the bottom."""
    w, h = im.size
    px = im.load()
    cut = h
    for y in range(h-1, int(h*0.85), -1):
        row = [px[x, y] for x in range(0, w, 5)]
        op = [c for c in row if c[3] > 120]
        if len(op) > len(row)*0.92 and all(max(c[:3]) < 90 for c in op):
            cut = y
        elif op:
            break
    return im.crop((0, 0, w, cut)) if cut < h else im


def content_rows(im):
    """Where the drawn part of the layer starts and ends, as fractions."""
    w, h = im.size
    px = im.load()
    top = bot = None
    for y in range(h):
        if any(px[x, y][3] > 40 for x in range(0, w, 5)):
            if top is None: top = y
            bot = y
    return top/float(h), (bot+1)/float(h)


def main():
    os.makedirs(OUT, exist_ok=True)
    for src, name, window in LAYERS:
        im = key_magenta(Image.open(os.path.join(SRC, src)))
        b, a, score = loop_seam(im, window)
        tile = im.crop((b, 0, a, im.height))
        if name == 'mid': tile = trim_baseline(tile)
        t, bt = content_rows(tile)
        # Trim the empty sky off the top. Transparent pixels are not free --
        # they are still blended, once per tile, every frame -- and these layers
        # were up to 62% empty. The game places each layer by its BOTTOM edge,
        # so trimming the top only changes the height it has to be drawn at.
        if t > 0.02:
            tile = tile.crop((0, int(t*tile.height), tile.width, tile.height))
            t, bt = content_rows(tile)
        path = os.path.join(OUT, name + '.webp')
        tile.save(path, 'WEBP', quality=92, method=6, exact=True)
        print('%-5s %4dx%-4d from %4d..%-4d (seam score %d)  content y %.3f..%.3f  %d KB'
              % (name, tile.width, tile.height, b, a, score//1000, t, bt,
                 os.path.getsize(path)//1024))
        # a preview that shows the loop, over a sky-ish blue
        two = Image.new('RGB', (tile.width*2, tile.height), (60, 150, 230))
        two.paste(tile, (0, 0), tile); two.paste(tile, (tile.width, 0), tile)
        two.resize((two.width//3, two.height//3), Image.LANCZOS).save('_bg_%s.png' % name)


if __name__ == '__main__':
    main()
