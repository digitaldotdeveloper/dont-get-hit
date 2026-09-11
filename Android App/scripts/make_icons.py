# -*- coding: utf-8 -*-
"""Launcher icons, the pre-Android-12 splash badge and the Play listing icon,
all from the game's one icon master (../icon/icon-master.png -- the file the
web set is built from by tools/make_icons.py).

    python scripts/make_icons.py

The master is the whole badge, and ITS ROUNDED CORNERS ARE BAKED IN, IN BLACK.
They are flooded to transparent from the four corners inwards, exactly as
tools/make_icons.py does for the web set -- not by a global near-black cut,
which would eat holes out of the bird's outline. Android then wants the badge
in three shapes:

- legacy (Android 7.x): the badge as it is, plus a round cut of it;
- adaptive (8+): TWO layers on a 108dp canvas, of which the launcher shows the
  middle 72dp through a mask of its own choosing -- a circle on a Pixel, a
  squircle on a Samsung. The badge goes on the FOREGROUND at 76dp, just wider
  than the mask, so no mask ever shows the badge's own edge or corners; the
  BACKGROUND is the same painting blurred to full bleed, which only shows when
  a launcher slides the two layers apart.

Rasters are lossy WebP q90: an icon is painted art at small sizes, and the
universal APK carries every density at once.
"""
import glob, os
from collections import deque
from PIL import Image, ImageDraw, ImageFilter

APP    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(os.path.dirname(APP), 'icon', 'icon-master.png')
RES    = os.path.join(APP, 'android', 'app', 'src', 'main', 'res')
STORE  = os.path.join(APP, 'store')
DENS   = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}
FG_DP  = 76


def save(im, path, q=90):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, 'WEBP', quality=q, method=6)


def fit(im, px):
    return im.resize((px, px), Image.LANCZOS)


def corner_alpha(im, near_black=34):
    """The same pass as tools/make_icons.py: flood near-black to alpha 0 from
    each corner, so only the baked corner mask goes."""
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    q = deque()
    for sx, sy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if max(px[sx, sy][:3]) <= near_black:
            q.append((sx, sy))
            seen[sy * w + sx] = 1
    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and max(px[nx, ny][:3]) <= near_black:
                seen[ny * w + nx] = 1
                q.append((nx, ny))
    return im


src = corner_alpha(Image.open(MASTER))
src = src.crop(src.getchannel('A').getbbox())          # any margin around the badge
S = min(src.size)
if src.size != (S, S):
    src = fit(src, S)

# The inset that clears the rounded corners: walk in along the diagonal to the
# first fully opaque pixel. Inside that square there is no transparency at all.
alpha = src.getchannel('A')
d = next(i for i in range(S // 2) if alpha.getpixel((i, i)) == 255) + 2
inner = src.crop((d, d, S - d, S - d))


def bleed(px):
    """The painting's own colours, softened past recognition, edge to edge."""
    return fit(inner, px).filter(ImageFilter.GaussianBlur(px * 0.06)).convert('RGB')


def disc(px, ss=4):
    m = Image.new('L', (px * ss, px * ss), 0)
    ImageDraw.Draw(m).ellipse((0, 0, px * ss - 1, px * ss - 1), fill=255)
    return m.resize((px, px), Image.LANCZOS)


# Capacitor's template rasters carry its own logo; clear them before writing ours
# (a .png and a .webp of the same name is a duplicate-resource build error).
for f in glob.glob(os.path.join(RES, 'mipmap-*', 'ic_launcher*.png')) + \
         glob.glob(os.path.join(RES, 'drawable*', 'splash.png')):
    os.remove(f)
for dd in glob.glob(os.path.join(RES, 'drawable-*')):
    if not os.listdir(dd):
        os.rmdir(dd)

for name, s in DENS.items():
    out = os.path.join(RES, 'mipmap-' + name)
    leg = round(48 * s)
    save(fit(src, leg), os.path.join(out, 'ic_launcher.webp'))
    r = fit(inner, leg)
    r.putalpha(disc(leg))
    save(r, os.path.join(out, 'ic_launcher_round.webp'))
    full, fg = round(108 * s), round(FG_DP * s)
    canvas = Image.new('RGBA', (full, full), (0, 0, 0, 0))
    canvas.alpha_composite(fit(src, fg), ((full - fg) // 2, (full - fg) // 2))
    save(canvas, os.path.join(out, 'ic_launcher_foreground.webp'))
    save(bleed(full), os.path.join(out, 'ic_launcher_background.webp'))

save(fit(src, 432), os.path.join(RES, 'drawable-nodpi', 'splash_badge.webp'))

# Play listing: 512x512 and square -- Play cuts its own corners, and asks that
# the art not bring rounded ones of its own. The badge's corners are filled
# with the same bleed the adaptive background uses.
os.makedirs(STORE, exist_ok=True)
play = bleed(512).convert('RGBA')
play.alpha_composite(fit(src, 512))
play.convert('RGB').save(os.path.join(STORE, 'play-icon-512.png'), optimize=True)

print('master %dpx, corner inset %dpx' % (S, d))
total = 0
for f in sorted(glob.glob(os.path.join(RES, 'mipmap-*', '*.webp'))) + \
         [os.path.join(RES, 'drawable-nodpi', 'splash_badge.webp')]:
    total += os.path.getsize(f)
    print('  %-52s %7d B' % (os.path.relpath(f, RES), os.path.getsize(f)))
print('  total %d KB' % (total // 1024))
