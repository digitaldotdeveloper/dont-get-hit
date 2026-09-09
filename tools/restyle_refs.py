# -*- coding: utf-8 -*-
"""Re-capture the style-reference set from the CURRENT build.

    python tools/restyle_refs.py

The reference frames in Desktop/dont-get-hit-art/style-reference/ are real
captures, and they are OLD: they show the prison as four cell doors floating
with gaps of sky between them, and the ant empire's dirt-mound horizon standing
in behind six different zones. Both were fixed. Attaching those frames to a
generation request as "match this style" would teach the model the composition
that was just removed -- the whole point of attaching a reference is that the
model copies what is in it.

So the same metre marks are re-shot from the running build and written beside
the originals rather than over them, which also gives the before/after the brief
asks for at the end."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapshot import shoot, OUT                              # noqa: E402
from PIL import Image                                       # noqa: E402

DEST = r"C:\Users\it\Desktop\dont-get-hit-art\style-reference-current"
# metre -> zone id, taken from the original file names so the pairs line up
MARKS = [(0, 'farm'), (100, 'farm'), (200, 'farm'), (300, 'farm'),
         (500, 'terr'), (700, 'terr'), (988, 'terr'),
         (1100, 'empire'), (1200, 'empire'), (1300, 'empire'),
         (1500, 'prison'), (1600, 'prison'),
         (2000, 'cherno'), (2100, 'cherno'),
         (2488, 'cia'), (2600, 'cia'), (2700, 'cia'),
         (3000, 'area51'), (3500, 'alien'), (3600, 'alien'),
         (4000, 'space'), (4200, 'space')]


def main():
    os.makedirs(DEST, exist_ok=True)
    shoot([str(m) for m, _ in MARKS])
    for m, zone in MARKS:
        src = os.path.join(OUT, 'm%d.png' % m)
        if not os.path.exists(src):
            print('  %04dm missing' % m)
            continue
        im = Image.open(src).convert('RGB')
        im.thumbnail((1400, 1400), Image.LANCZOS)
        dst = os.path.join(DEST, '%04dm_%s.webp' % (m, zone))
        im.save(dst, 'WEBP', quality=90, method=6)
        print('  %04dm_%-7s %dx%d  %5.1f KB' % (m, zone, im.width, im.height,
                                                os.path.getsize(dst)/1024.0))


if __name__ == '__main__':
    main()
