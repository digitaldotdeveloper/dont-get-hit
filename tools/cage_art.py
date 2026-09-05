# -*- coding: utf-8 -*-
"""Cut the intro barn and its cage door, and measure what the game asks of them.

   The old barn was painted in a different, softer style from the map and it
   carried its own farm behind it -- a windmill, a fence and a line of hills
   baked into the picture -- which is why it needed a fade down its right edge
   to hand over to the background, and why that hand-over ghosted. This one is
   the barn ALONE on a magenta field, so the parallax layers simply show behind
   it and there is nothing to blend.

   `CAGE` in index.html is a set of fractions measured off the art rather than
   guessed -- that is what puts the chicken's feet on the straw instead of near
   it -- so this prints them rather than leaving anyone to eyeball:

     dx0 dx1 dy0 dy1   the doorway, found as the dark opening in the wall
     floorFrac         the barn's own ground line
     roof              the apex, where the neighbours perch

     python tools/cage_art.py        # -> sheets/v2/cage_scene.webp, art/cage_door.webp
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import SHEETS, REF, AUDIOSRC, ROOT as GAME, sheets, need
import os
from PIL import Image

SRC = sheets('v3')
BARN = 'match-the-attached-image-s-art-style-exactly-2-1788525495009-1.png'
DOOR = 'match-the-attached-image-s-art-style-exactly-2-1788523499125-1.png'


def key_magenta(im):
    im = im.convert('RGBA')
    px = im.load()
    w, h = im.size
    def magenta(c):
        return (c[0] > 140 and c[2] > 140 and c[1] < 120
                and (c[0]-c[1]) > 55 and (c[2]-c[1]) > 55)
    for y in range(h):
        for x in range(w):
            if magenta(px[x, y]): px[x, y] = (0, 0, 0, 0)
    for y in range(h):                       # the half-keyed rim reads purple
        for x in range(w):
            c = px[x, y]
            if c[3] and c[0] > c[1] + 45 and c[2] > c[1] + 45:
                g = c[1]
                px[x, y] = (min(c[0], g+35), g, min(c[2], g+35), 200)
    return im


def doorway(im):
    """The dark opening in the wall, as fractions of the image.

       Found by the longest RUN of dark pixels in each row, not by counting
       them: the barn is drawn with a black outline, so every row of it has
       plenty of dark pixels and a count says the doorway is the whole picture.
       A run says otherwise -- only the rows that cross the opening have a
       third of the width in one unbroken stretch."""
    w, h = im.size
    px = im.load()
    def dark(c):
        return c[3] > 200 and max(c[:3]) < 110
    best = []
    for y in range(h):
        run = lo = 0; bestrun = (0, 0)
        for x in range(w):
            if dark(px[x, y]):
                if run == 0: lo = x
                run += 1
                if run > bestrun[0]: bestrun = (run, lo)
            else: run = 0
        best.append(bestrun)
    thr = w*0.18
    ys = [y for y, (r, _) in enumerate(best) if r > thr]
    if not ys: raise SystemExit('no doorway found')
    y0, y1 = min(ys), max(ys)
    x0 = min(best[y][1] for y in ys)
    x1 = max(best[y][1] + best[y][0] for y in ys)
    return x0/w, x1/w, y0/h, y1/h


def main():
    barn = key_magenta(Image.open(os.path.join(SRC, BARN)))
    b = barn.getbbox(); barn = barn.crop(b)
    w, h = barn.size
    px = barn.load()
    # the apex: the topmost row that has any barn in it, and where its middle is
    top = next(y for y in range(h) if any(px[x, y][3] > 80 for x in range(0, w, 3)))
    xs = [x for x in range(w) if px[x, top+2][3] > 80] or [w//2]
    barn.save(os.path.join(GAME, 'art', 'cage_scene.webp'), 'WEBP', quality=92, method=6, exact=True)
    dx0, dx1, dy0, dy1 = doorway(barn)
    print('cage_scene.webp  %dx%d  %d KB' % (w, h, os.path.getsize(os.path.join(GAME, 'art', 'cage_scene.webp'))//1024))
    print('  dx0:%.4f, dx1:%.4f,' % (dx0, dx1))
    print('  dy0:%.4f, dy1:%.4f,' % (dy0, dy1))
    print('  floorFrac:%.4f,   // the art is trimmed to the barn, so its base IS the ground'
          % 1.0)
    print('  roof:[%.4f, %.4f],' % ((sum(xs)/len(xs))/w, top/float(h)))

    door = key_magenta(Image.open(os.path.join(SRC, DOOR)))
    d = door.getbbox(); door = door.crop(d)
    door.save('art/cage_door.webp', 'WEBP', quality=92, method=6, exact=True)
    print('cage_door.webp   %dx%d  %d KB' % (door.width, door.height,
          os.path.getsize('art/cage_door.webp')//1024))

    # a preview with the measured doorway drawn on, over a sky-ish blue
    from PIL import ImageDraw
    pv = Image.new('RGB', barn.size, (86, 168, 232))
    pv.paste(barn, (0, 0), barn)
    dr = ImageDraw.Draw(pv)
    dr.rectangle([dx0*w, dy0*h, dx1*w, dy1*h], outline=(255, 0, 170), width=4)
    pv.save('_cage_measured.png')


if __name__ == '__main__':
    main()
