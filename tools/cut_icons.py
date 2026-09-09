# -*- coding: utf-8 -*-
"""Cut the death card's icons out of the raw renders.

   Three takes came back per prompt and the choosing is done HERE, by name, so
   the pick is recorded rather than remembered. What the takes cost:

     tnt1  three good singles; the chosen one has the spark clear of the stick
           instead of overlapping it, which is the only one of the three that
           still reads at 26px
     tnt2  the chosen one has a black strap and two obviously separate sticks;
           another take drew the pair too small in the frame
     tnt3  one take came back in somebody else's game -- blue and gold, glowing,
           on a dark starfield -- which is the style drift PIPELINE.md warns
           about and the reason three takes are asked for
     heart all three were usable; the chosen one has the cleanest highlight and
           sits closest to the game's own --danger

   THE LARGEST BLOB IS THE POINT, not a detail. Gemini leaves a small sparkle
   mark low-right on these, and keeping only the biggest connected component
   drops it without anybody having to notice it was there.

     python tools/cut_icons.py --list    contact sheet of everything available
     python tools/cut_icons.py           cut the four picks into art/shop/
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from paths import sheets, need
from imglib import key_green, label

SRC  = sheets('v6')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'art', 'shop')
SIZE = 168          # ~2.5x the 60-odd px it is drawn at on the card

# stem -> file. Timestamps, because that is what the Studio names them.
PICK = {
    'tnt1':  '1788971894617',
    'tnt2':  '1788971979866',
    'tnt3':  '1788972816853',
    'heart': '1788972948715',
}


def raw():
    return sorted(f for f in os.listdir(SRC)
                  if f.startswith('2d-mobile-game-sprite-art') and f.endswith('.png'))


def biggest(alpha):
    """The one blob that is the object, and nothing that is a watermark."""
    lab, n = label(alpha > 128)
    if n <= 1:
        return alpha
    best, area = 0, 0
    for i in range(1, n + 1):
        a = int((lab == i).sum())
        if a > area:
            best, area = i, a
    return np.where(lab == best, alpha, 0).astype('uint8')


def cut(name, stamp):
    hit = [f for f in raw() if stamp in f]
    if not hit:
        raise SystemExit('no render matching %s for %s in %s' % (stamp, name, SRC))
    im = Image.open(os.path.join(SRC, hit[0])).convert('RGB')
    rgba = key_green(im)
    a = np.array(rgba)
    a[..., 3] = biggest(a[..., 3])
    out = Image.fromarray(a, 'RGBA')
    out = out.crop(out.getbbox())
    out.thumbnail((SIZE, SIZE), Image.LANCZOS)
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, name + '.webp')
    out.save(dst, 'WEBP', lossless=True)
    print('%-6s %-46s -> %s  %dx%d  %.1f KB'
          % (name, hit[0][-18:], os.path.basename(dst), out.size[0], out.size[1],
             os.path.getsize(dst) / 1024))


def contact():
    from PIL import ImageDraw
    fs = raw()
    if not fs:
        raise SystemExit('nothing in %s -- run tools/gen_icons.py first' % SRC)
    T, cols = 300, 6
    rows = (len(fs) + cols - 1) // cols
    sh = Image.new('RGB', (T*cols, (T+20)*rows), (18, 10, 30))
    d = ImageDraw.Draw(sh)
    for i, f in enumerate(fs):
        im = Image.open(os.path.join(SRC, f)).convert('RGB')
        im.thumbnail((T, T), Image.LANCZOS)
        x, y = (i % cols)*T, (i // cols)*(T+20)
        sh.paste(im, (x + (T-im.width)//2, y+20))
        d.text((x+6, y+4), f[-18:-6], fill=(255, 213, 74))
    p = os.path.join(SRC, '_contact.png')
    sh.save(p)
    print('contact sheet: %s   (%d takes)' % (p, len(fs)))


if __name__ == '__main__':
    need(SRC)
    if '--list' in sys.argv:
        contact()
    else:
        for k, v in PICK.items():
            cut(k, v)
