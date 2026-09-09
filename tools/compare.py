# -*- coding: utf-8 -*-
"""Butt a world's panels together BEFORE and AFTER a re-render, on one page.

    python tools/compare.py prison cia > out.html

joins.py answers "where are the joins"; this answers "did the change work",
which is a different question and needs the two strips one above the other at
the same scale. Anything else -- two screenshots taken minutes apart, a link to
the live game -- makes the reader hold one image in their head while they look
at the other, and that is exactly how a change that did nothing gets approved.

The `before` copies live in tools/_before/<world>/, put there by hand before a
re-render. No copy, no comparison: the page says so rather than showing one
strip and letting it read as both."""
import base64
import io
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from joins import SKY, rgb, panels_for, ROOT          # noqa: E402

BEFORE = os.path.join(ROOT, 'tools', '_before')


def strip(files, sky):
    ims = [Image.open(f).convert('RGBA') for f in files]
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (sum(i.width for i in ims), h), rgb(sky) + (255,))
    x = 0
    for im in ims:
        out.alpha_composite(im, (x, h - im.height))
        x += im.width
    b = io.BytesIO()
    out.convert('RGB').save(b, 'WEBP', quality=90, method=6)
    return ('data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(),
            out.width, out.height, len(ims))


def before_files(world):
    d = os.path.join(BEFORE, world)
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d)
                  if f.endswith('.webp') and f not in ('near.webp', 'hang.webp'))


def main():
    worlds = [a for a in sys.argv[1:] if not a.startswith('-')] or list(SKY)
    print('<title>Panel Joins, Before and After</title>')
    print(open(os.path.join(os.path.dirname(__file__), 'compare.css')).read()
          if os.path.exists(os.path.join(os.path.dirname(__file__), 'compare.css')) else '')
    for w in worlds:
        after = panels_for(w)
        if not after:
            continue
        print('<section><h2>%s</h2>' % w)
        bf = before_files(w)
        for label, fs in (('before', bf), ('after', after)):
            if not fs:
                print('<p class="none">no <b>%s</b> copies kept for this world</p>' % label)
                continue
            src, W, H, n = strip(fs, SKY[w])
            print('<figure><figcaption>%s &middot; %d panels butted as the game '
                  'tiles them</figcaption><img src="%s" width="%d" height="%d" '
                  'alt="%s %s"></figure>' % (label, n, src, W, H, w, label))
        print('</section>')


if __name__ == '__main__':
    main()
