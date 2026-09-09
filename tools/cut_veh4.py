# -*- coding: utf-8 -*-
"""Cut the four new vehicles, and MEASURE the anchor each one needs.

    python tools/cut_veh4.py            # all four
    python tools/cut_veh4.py --check    # + crosshair proofs in TEMP

Every one of these ships as a still, for the reason the wheel and the saucer
already established: the moving part of each vehicle has a RULE, and a rule is
cheaper, exact at every value, and can answer an input on the frame it happens.
So what the generator was asked NOT to draw is what this script has to find the
anchor for:

    rocket   the nozzles          -> the flame grows out of them with speed
    hopper   the shell's underside -> the spring is drawn under it, compressed
    spoon    the two coils         -> the magnetic arc snaps between them
    toaster  the slots            -> the toast rises out of them with charge

The anchors come back as fractions of each finished picture, which is what the
tables in index.html want. `--check` draws them back onto the sprite, because
every anchor in this project that was estimated by eye was wrong -- three of
the truck's four exhausts, to start with.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT as GAME, sheets, need
import numpy as np
from PIL import Image, ImageDraw
from imglib import despill, bbox, label

SH  = sheets("v2")
ART = os.path.join(GAME, "art")


def key(im, colour, tol=52):
    """Alpha-key a flat screen. `imglib.key_green` only knows green, and the
       corn rocket had to be shot on MAGENTA -- a corn husk is bright green, so
       keying green out of it takes the leaves with it. Same test, other
       channel: the key channel(s) clearly dominant over the rest."""
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    if colour == "green":
        m = (g - np.maximum(r, b)) > tol
    else:                                   # magenta: red AND blue over green
        m = (np.minimum(r, b) - g) > tol
    return np.dstack([a.astype(np.uint8), np.where(m, 0, 255).astype(np.uint8)])


def blobs(rgba, floor=3000):
    lab, n = label(rgba[..., 3] > 0)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        if int(m.sum()) > floor:
            xs = np.nonzero(m.any(0))[0]
            out.append({"m": m, "a": int(m.sum()), "x0": int(xs.min())})
    return sorted(out, key=lambda b: -b["a"])


def cut(rgba, m, width):
    bb = bbox(m)
    sub = rgba[bb[1]:bb[3], bb[0]:bb[2]].copy()
    sub[..., 3] = np.where(m[bb[1]:bb[3], bb[0]:bb[2]], sub[..., 3], 0)
    im = Image.fromarray(sub, "RGBA")
    return im.resize((width, max(1, round(im.height*width/im.width))), Image.LANCZOS)


def save(im, name):
    p = os.path.join(ART, name)
    im.save(p, "WEBP", lossless=True, method=6)
    print("   %-20s %dx%d  %4d KB" % (name, im.width, im.height,
                                      os.path.getsize(p)//1024))


def solid(im, a=110):
    return np.asarray(im)[..., 3] > a


def col_centroid(im, x0f, x1f):
    """Vertical centre of the coverage in a slice of the picture, as a
       fraction of its height. Used for the rocket's nozzles: they are the
       whole of the left-hand edge, so the edge IS the anchor."""
    s = solid(im)
    sl = s[:, int(im.width*x0f):max(int(im.width*x0f)+1, int(im.width*x1f))]
    ys = np.nonzero(sl.any(1))[0]
    return float((ys.min() + ys.max() + 1)/2/im.height) if len(ys) else 0.5


def bright_discs(im, n, want_dark=False):
    """The spoon's coils: the two chunky machined discs with a glowing blue
       band. Found as strongly BLUE blobs, which nothing else on a silver
       spoon is, then taken largest-first and sorted top to bottom."""
    a = np.asarray(im).astype(np.int16)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    m = (al > 120) & (b > 120) & (b - r > 40) & (b - g > 15)
    lab, k = label(m)
    got = []
    for i in range(1, k + 1):
        mm = lab == i
        if int(mm.sum()) < 120: continue
        ys, xs = np.nonzero(mm)
        got.append({"n": int(mm.sum()),
                    "cx": (xs.min()+xs.max()+1)/2/im.width,
                    "cy": (ys.min()+ys.max()+1)/2/im.height,
                    "r":  (xs.max()+1-xs.min())/2/im.width})
    got.sort(key=lambda d: -d["n"])
    got = sorted(got[:n], key=lambda d: d["cy"])
    for d in got: d.pop("n")
    return got


def main():
    meta = {}

    # ---- CORN ROCKET, on magenta ------------------------------------------
    rgba = despill(key(Image.open(need(os.path.join(SH, "veh_rocket.png"))), "magenta"))
    im = cut(rgba, blobs(rgba)[0]["m"], 820)
    save(im, "veh_rocket.webp")
    meta["rocket"] = {"w": im.width, "h": im.height,
                      "ex": 0.035, "ey": round(col_centroid(im, 0.0, 0.10), 4)}

    # ---- EGGSHELL HOPPER, on green ----------------------------------------
    rgba = despill(key(Image.open(need(os.path.join(SH, "veh_hopper.png"))), "green"))
    im = cut(rgba, blobs(rgba)[0]["m"], 560)
    save(im, "veh_hopper.webp")
    """Where the spring bolts on: the widest run of the shell's LOWEST tenth,
       so the coil is drawn under the middle of the base rather than under the
       middle of the bounding box -- a cracked shell is not symmetrical."""
    s = solid(im)
    low = s[int(im.height*0.90):]
    xs = np.nonzero(low.any(0))[0]
    meta["hopper"] = {"w": im.width, "h": im.height,
                      "footx": round(float((xs.min()+xs.max()+1)/2/im.width), 4)
                               if len(xs) else 0.5}

    # ---- MAGNET SPOON, on green -------------------------------------------
    rgba = despill(key(Image.open(need(os.path.join(SH, "veh_spoon.png"))), "green"))
    im = cut(rgba, blobs(rgba)[0]["m"], 760)
    save(im, "veh_spoon.webp")
    coils = bright_discs(im, 2)
    meta["spoon"] = {"w": im.width, "h": im.height,
                     "coils": [{k: round(v, 4) for k, v in c.items()} for c in coils]}

    # ---- TOASTER JUMPER, on green: TWO objects ----------------------------
    rgba = despill(key(Image.open(need(os.path.join(SH, "veh_toaster.png"))), "green"))
    bs = blobs(rgba)
    print("  toaster sheet: %d objects" % len(bs))
    body = cut(rgba, bs[0]["m"], 620)
    save(body, "veh_toaster.webp")
    toast = cut(rgba, bs[1]["m"], 200)
    save(toast, "veh_toast.webp")
    """The slot the toast comes out of, and the first version of this measured
       the wrong thing entirely: it took the highest covered row of the middle
       third, and the middle third is the CHICKEN -- the crosshair landed on
       his cap, a third of a picture above the toaster.

       The generator was asked for empty slots and drew a lid, so there is no
       slot to find. What there IS is the top of the white CASING -- and the
       second version of this got that wrong too, because "near-white" also
       catches Nugget: his cream body is 240,235,215 and sails through any
       threshold the casing passes. Two pixels of his cap put the anchor back
       at the top of the picture.

       So it is the LARGEST WHITE COMPONENT, not the whitest pixels. The black
       outline separates the casing from the bird, and the casing is much the
       bigger of the two -- which is a fact about the sprite rather than a
       threshold that has to be tuned per render."""
    a = np.asarray(body).astype(np.int16)
    white = ((a[..., 3] > 120) & (a[..., 0] > 200) & (a[..., 1] > 200) &
             (a[..., 2] > 195))
    wlab, wn = label(white)
    best, bn = None, 0
    for i in range(1, wn + 1):
        mm = wlab == i
        if int(mm.sum()) > bn: bn, best = int(mm.sum()), mm
    ys, xs = np.nonzero(best)
    meta["toaster"] = {"w": body.width, "h": body.height,
                       "tw": toast.width, "th": toast.height,
                       "slotx": round(float((xs.min()+xs.max()+1)/2/body.width), 4),
                       "sloty": round(float(ys.min()/body.height), 4)}

    print(json.dumps(meta, separators=(",", ":")))

    if '--check' in sys.argv:
        from PIL import ImageDraw as D2
        def proof(name, im, pts):
            pv = Image.new("RGBA", im.size, (24, 26, 32, 255))
            pv.alpha_composite(im)
            d = D2.Draw(pv)
            for (fx, fy) in pts:
                x, y = fx*im.width, fy*im.height
                d.line([(x-26, y), (x+26, y)], fill=(255, 0, 200, 255), width=3)
                d.line([(x, y-26), (x, y+26)], fill=(255, 0, 200, 255), width=3)
            p = os.path.join(os.environ.get('TEMP', '.'), 'veh_%s_check.png' % name)
            pv.convert("RGB").save(p); print("   check -> %s" % p)
        proof('rocket', Image.open(os.path.join(ART, 'veh_rocket.webp')),
              [(meta['rocket']['ex'], meta['rocket']['ey'])])
        proof('hopper', Image.open(os.path.join(ART, 'veh_hopper.webp')),
              [(meta['hopper']['footx'], 0.99)])
        proof('spoon', Image.open(os.path.join(ART, 'veh_spoon.webp')),
              [(c['cx'], c['cy']) for c in meta['spoon']['coils']])
        proof('toaster', Image.open(os.path.join(ART, 'veh_toaster.webp')),
              [(meta['toaster']['slotx'], meta['toaster']['sloty'])])
    return meta


if __name__ == "__main__":
    main()
