# -*- coding: utf-8 -*-
"""Shop thumbnails for the four hats.

   THE EXCEPTION TO paths.py, AND WHY. Every other cut_*.py reads a raw Gemini
   sheet out of the archive; there is no sheet for these. The four hats were
   generated as opaque reference *renders* -- a whole chicken wearing the hat,
   on flat green, 512x280 RGB -- and `chickens.html` shows them as picture
   cards, keying the green in the browser. So the shipped file IS the source,
   and this script reads art/ rather than dgh/sheets.

   The APPEARANCE tab needs something else: a hat-shaped icon 54px across. A
   whole chicken at that size is a beige smudge, so each render is keyed, its
   largest blob taken, and the top 44% cropped -- which is the head and the hat
   and nothing else. 44% was measured, not guessed: below that the beak goes,
   above it the wing comes in.

   Writes art/shop/hat_*.webp, lossless, at 3x the drawn size. Rerun after any
   change to art/<hat>.webp.
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART  = os.path.join(ROOT, 'art')
OUT  = os.path.join(ART, 'shop')

HATS = ['snapback', 'bucket', 'fedora', 'beanie']
HEAD = 0.44          # the share of the keyed figure that is head + hat
SIZE = 162           # 54 css px at 3x


def key_green(im):
    """The same green key the rest of the pipeline uses, as a mask.

       Keyed on the two differences rather than on absolute green, because the
       render is lit and the backdrop is not one flat value by the time it has
       been through a lossy generator and a resize."""
    a = np.asarray(im.convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = (g > 90) & (g - r > 40) & (g - b > 40)
    return a.astype('uint8'), np.where(green, 0, 255).astype('uint8')


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in HATS:
        src = os.path.join(ART, name + '.webp')
        if not os.path.exists(src):
            raise SystemExit('missing source: %s' % src)
        rgb, alpha = key_green(Image.open(src))
        fig = Image.fromarray(np.dstack([rgb, alpha]), 'RGBA')
        fig = fig.crop(Image.fromarray(alpha).getbbox())      # the chicken

        w, h = fig.size
        head = fig.crop((0, 0, w, int(h * HEAD)))
        head = head.crop(head.getbbox())                      # trim the new edges
        head.thumbnail((SIZE, SIZE), Image.LANCZOS)

        dst = os.path.join(OUT, 'hat_%s.webp' % name)
        head.save(dst, 'WEBP', lossless=True)
        print('%-10s %s -> %s  %dx%d  %.1f KB'
              % (name, fig.size, head.size, head.size[0], head.size[1],
                 os.path.getsize(dst) / 1024))


if __name__ == '__main__':
    main()
