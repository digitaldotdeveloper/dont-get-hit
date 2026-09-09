# -*- coding: utf-8 -*-
"""Cut the fried-egg UFO out of its sheet, and MEASURE its three lamps.

ONE PICTURE, NOT A CYCLE -- and that is the same decision the wheel got. A
saucer's tilt has a rule (it leans with its vertical speed) and so does its
underlight (it burns with the button), so both are solved in code off one still
instead of baked into three. Three tilts would be bigger, wrong at every angle
between them, and would still not answer the press on the frame it happened.

    python tools/cut_ufo.py            # sheets/v2/ufo_ride_b.png -> art/ufo.webp
    python tools/cut_ufo.py --sheet X  # cut a different take
    python tools/cut_ufo.py --check    # + a crosshair proof next to it

What it prints is the LAMP TABLE, and it is measured rather than read off a
grid by eye: the lenses are found as the pale bright blobs inside the dark
underside, and their centres come back as fractions of the finished picture,
which is exactly what `UFO_LAMPS` in index.html wants. Reading anchors off art
by eye has been wrong three times in this project; `--check` draws the answer
back onto the sprite so it can be looked at rather than trusted.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT as GAME, sheets, need
import numpy as np
from PIL import Image
from imglib import key_green, despill, bbox, label

SH   = sheets("v2")
ART  = os.path.join(GAME, "art")
OUT_W = 800            # the finished sprite's width; ufoGeom scales off it


def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def main():
    src = need(os.path.join(SH, arg('--sheet', 'ufo_ride_b.png')))
    rgba = despill(key_green(Image.open(src)))
    """The sheet came back as three saucers at three sizes in a staggered
    layout rather than the row that was asked for -- which is normal, and why
    nothing here slices by column. The craft wanted is the LEVEL one, and it is
    the biggest blob on the sheet."""
    lab, n = label(rgba[..., 3] > 0)
    blobs = []
    for i in range(1, n + 1):
        m = lab == i
        a = int(m.sum())
        if a > 3000: blobs.append((a, m))
    blobs.sort(key=lambda b: -b[0])
    print("  %d saucers on the sheet; taking the largest" % len(blobs))
    m = blobs[0][1]
    bb = bbox(m)
    sub = rgba[bb[1]:bb[3], bb[0]:bb[2]].copy()
    sub[..., 3] = np.where(m[bb[1]:bb[3], bb[0]:bb[2]], sub[..., 3], 0)

    im = Image.fromarray(sub, "RGBA")
    h = max(1, round(im.height * OUT_W / im.width))
    im = im.resize((OUT_W, h), Image.LANCZOS)

    """THE LAMPS. Pale, bright and enclosed by the dark grey underside, so they
    are the only blobs on the sprite that are both very light and sitting in
    the bottom half. Found, not guessed: the code below takes the three largest
    of them, sorted left to right, and reports each centre and radius as a
    fraction of the finished picture."""
    a = np.asarray(im).astype(np.int16)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    bright = (al > 120) & (r > 205) & (g > 175) & (b < 205) & (r >= b + 25)
    bright[: int(h * 0.45)] = False              # the yolk's highlight is up top
    llab, ln = label(bright)
    lamps = []
    for i in range(1, ln + 1):
        mm = llab == i
        n_px = int(mm.sum())
        if n_px < 150: continue
        ys, xs = np.nonzero(mm)
        lamps.append({"n": n_px,
                      "cx": (xs.min() + xs.max() + 1) / 2 / OUT_W,
                      "cy": (ys.min() + ys.max() + 1) / 2 / h,
                      "r": (xs.max() + 1 - xs.min()) / 2 / OUT_W})
    lamps.sort(key=lambda l: -l["n"])
    lamps = sorted(lamps[:3], key=lambda l: l["cx"])
    for l in lamps: l.pop("n")

    """The BODY BOX -- what a hazard actually hits. The picture is the saucer
    plus the dome, and the dome is a good third of it; a box the height of the
    whole image would have the yolk colliding with a wire the craft has already
    flown under. So the widest run (the rim) and the metal underneath are what
    the number is taken from."""
    solid = (np.asarray(im)[..., 3] > 90)
    rows = solid.sum(1)
    rim = int(np.argmax(rows))                              # the rim: the widest row
    body = np.nonzero(rows > OUT_W * 0.02)[0]
    meta = {"w": OUT_W, "h": h,
            "rim": round(rim / h, 4),                       # where the saucer's waist is
            "top": round(float(body.min()) / h, 4),
            "bot": round(float(body.max() + 1) / h, 4),
            "lamps": [{k: round(v, 4) for k, v in l.items()} for l in lamps]}

    im.save(os.path.join(ART, "ufo.webp"), "WEBP", lossless=True, method=6)
    print("   ufo.webp  %dx%d  %.0f KB" %
          (OUT_W, h, os.path.getsize(os.path.join(ART, "ufo.webp")) / 1024))
    print(json.dumps(meta, separators=(",", ":")))

    if '--check' in sys.argv:
        """Proof, not assertion: the lamp centres drawn back onto the art. An
        anchor that is a few percent out looks exactly like a correct one in a
        JSON dump and is obvious the moment it is on the metal."""
        from PIL import ImageDraw
        pv = Image.new("RGBA", (OUT_W, h), (24, 26, 32, 255))
        pv.alpha_composite(im)
        d = ImageDraw.Draw(pv)
        for l in lamps:
            x, y, rr = l["cx"] * OUT_W, l["cy"] * h, l["r"] * OUT_W
            d.line([(x - rr * 1.4, y), (x + rr * 1.4, y)], fill=(255, 0, 200, 255), width=3)
            d.line([(x, y - rr * 1.4), (x, y + rr * 1.4)], fill=(255, 0, 200, 255), width=3)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(0, 255, 255, 255), width=3)
        d.line([(0, meta["rim"] * h), (OUT_W, meta["rim"] * h)], fill=(255, 220, 0, 255), width=3)
        p = os.path.join(os.environ.get('TEMP', '.'), 'ufo_check.png')
        pv.convert("RGB").save(p)
        print("   check -> %s" % p)
    return meta


if __name__ == "__main__":
    main()
