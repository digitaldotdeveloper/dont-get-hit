# -*- coding: utf-8 -*-
"""Build the portrait title art out of the landscape key art.

   The key art is 16:9 and the game is a phone held upright, so a `cover` crop
   of it would show about a quarter of the width -- not enough to hold both the
   logo and the chicken. Instead the strongest square of the poster (barn, dog,
   chicken, logo, eggs) is kept whole and the picture is *extended*: flat sky
   above it and dirt below, both graded so they fall away from the art.

   The extensions are one colour per row, not a stretch of the edge pixels. A
   stretch drags whatever touches the edge -- the barn's roof line, the tip of
   a siren ray -- into a full-height streak, which is exactly what the first
   attempt looked like. Only the last ~30px before the seam are cross-faded to
   the real edge colours, so anything cut off dissolves instead of cutting.

   Nothing inside the poster is redrawn or regenerated: every original pixel is
   still there, in place.

     python tools/title_art.py            # -> art/title.webp
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import SHEETS, REF, AUDIOSRC, ROOT as GAME, sheets, need
import os, sys
from PIL import Image

SRC = os.path.join(REF, 'keyart.png')
OUT = 'art/title.webp'
W, H = 1080, 1920          # 9:16, enough for a 1.75x backing store on a phone
FADE = 34                  # px of cross-fade into the real edge


def row_colour(img, y0, y1, sky):
    """A representative colour for a band -- median over the columns that are
       actually the thing we are extending, so a barn or a rock cannot drag the
       average sideways."""
    band = img.crop((0, y0, img.width, y1)).resize((img.width, 1), Image.BILINEAR)
    px = [band.getpixel((x, 0)) for x in range(band.width)]
    if sky: px = [c for c in px if c[2] > c[0] + 25 and c[2] > 110] or px
    px.sort(key=lambda c: c[0]*0.3 + c[1]*0.59 + c[2]*0.11)
    return px[len(px)//2]


def extend(edge, height, base, dark, up):
    """A flat graded fill of `height`, cross-faded into `edge` (a 1px strip) at
       the seam. `up` means the seam is at the bottom."""
    out = Image.new('RGB', (edge.width, height))
    ep, op = edge.load(), out.load()
    for y in range(height):
        t = y/(height-1.0)                      # 0 at the far end, 1 at the seam
        if not up: t = 1-t
        k = dark + (1-dark)*(t**0.85)           # darkens away from the art
        row = tuple(int(c*k) for c in base)
        d = (height-1-y) if up else y           # distance from the seam
        m = max(0.0, 1 - d/float(FADE))         # cross-fade weight
        for x in range(edge.width):
            if m <= 0: op[x, y] = row
            else:
                e = ep[x, 0]
                op[x, y] = tuple(int(row[i]*(1-m) + e[i]*m) for i in range(3))
    return out


# The crop is not a taste decision. A phone is about 0.47 wide for its height
# while the poster is 0.5625, so `cover` throws away ~17% of the width and the
# visible window is roughly 0.085..0.915 of the picture. The logo has to sit
# inside that with margin, and so does the chicken, which pins both edges: with
# the lockup at 0.334..0.714 of the source and the chicken's wing reaching
# 0.229, the crop must be at least 0.595 wide, and 0.171..0.781 clears every
# constraint with room to spare. Measured, not eyeballed -- 0.19..0.75 put the
# T of HIT at 0.935 of the poster and a phone cut it in half.
def build(src=SRC, out=OUT, x0f=0.171, x1f=0.781, sky=300):
    im = Image.open(src).convert('RGB')
    iw, ih = im.size
    crop = im.crop((int(x0f*iw), 0, int(x1f*iw), ih))
    ah = int(round(crop.height * (W/crop.width)))
    art = crop.resize((W, ah), Image.LANCZOS)
    ground = H - sky - ah
    assert ground > 0, 'no room left for the ground'

    canvas = Image.new('RGB', (W, H))
    top = art.crop((0, 0, W, 4)).resize((W, 1), Image.BILINEAR)
    bot = art.crop((0, ah-5, W, ah)).resize((W, 1), Image.BILINEAR)
    canvas.paste(extend(top, sky, row_colour(art, 0, 6, True), 0.66, True), (0, 0))
    canvas.paste(art, (0, sky))
    canvas.paste(extend(bot, ground, row_colour(art, ah-8, ah, False), 0.30, False),
                 (0, sky + ah))
    canvas.save(out, 'WEBP', quality=86, method=6)
    canvas.save('_title_preview.png')      # scratch, for eyeballing; gitignored
    print('%s  %dx%d  %d KB   art band y=%d..%d' %
          (out, W, H, os.path.getsize(out)//1024, sky, sky+ah))
    return canvas


if __name__ == '__main__':
    build(*sys.argv[1:])
