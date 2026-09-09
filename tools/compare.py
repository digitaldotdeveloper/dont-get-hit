# -*- coding: utf-8 -*-
"""Butt a world's panels together at each STAGE of a change, on one page.

    python tools/compare.py prison cia > page.html

joins.py answers "where are the joins"; this answers "did the change work",
which is a different question and needs the strips one above the other at the
same scale. Anything else -- two screenshots taken twenty minutes apart, a link
to the live game -- makes the reader hold one image in their head while they
look at the other, and that is how a change that did nothing gets approved.

A stage is just a directory of panel files kept before a re-render:

    tools/_before/<world>/   what it looked like as rows of props
    tools/_step1/            continuous walls, before the palettes were named
    art/panels/<world>/      what is in the game now

A missing stage is SAID so, never quietly skipped: one strip shown alone reads
as both."""
import base64
import io
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from joins import SKY, rgb, panels_for, ROOT          # noqa: E402

STAGES = [
    ('Before', 'rows of props on a ground line, gaps of sky between them',
     lambda w: _dir(os.path.join(ROOT, 'tools', '_before', w))),
    ('Continuous', 'one unbroken wall, things set into it, but no shared palette',
     lambda w: _dir(os.path.join(ROOT, 'tools', '_step1'), pre=w)),
    ('Now', 'continuous, and the four panels painted from one palette',
     lambda w: panels_for(w)),
]
PRE = {'prison': 'p', 'cia': 'b', 'empire': 'e', 'cherno': 'c',
       'area51': 'a', 'alien': 'x', 'space': 's'}


def _dir(d, pre=None):
    if not os.path.isdir(d):
        return []
    keep = PRE.get(pre) if pre else None
    return sorted(os.path.join(d, f) for f in os.listdir(d)
                  if f.endswith('.webp') and f not in ('near.webp', 'hang.webp')
                  and (keep is None or f.startswith(keep)))


def strip(files, sky):
    ims = [Image.open(f).convert('RGBA') for f in files]
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (sum(i.width for i in ims), h), rgb(sky) + (255,))
    x = 0
    for im in ims:
        out.alpha_composite(im, (x, h - im.height))
        x += im.width
    b = io.BytesIO()
    out.convert('RGB').save(b, 'WEBP', quality=88, method=6)
    return ('data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(),
            out.width, out.height, len(ims))


def main():
    worlds = [a for a in sys.argv[1:] if not a.startswith('-')] or list(SKY)
    for w in worlds:
        print('<section id="%s"><h2>%s</h2>' % (w, w))
        for label, note, get in STAGES:
            fs = get(w)
            if not fs:
                continue
            src, W, H, n = strip(fs, SKY[w])
            print('<figure><figcaption><b>%s</b> &middot; %s</figcaption>'
                  '<div class="scroll"><img src="%s" width="%d" height="%d" alt="%s %s">'
                  '</div></figure>' % (label, note, src, W, H, w, label))
        print('</section>')


if __name__ == '__main__':
    main()
