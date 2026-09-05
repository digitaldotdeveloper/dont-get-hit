# -*- coding: utf-8 -*-
"""Cut the wheel and the exhaust flames into art/fx/.

THE WHEEL IS ONE PICTURE, NOT A CYCLE. A rolling wheel is a rotation, and a
rotation is exact at any angle -- baking twelve frames of one would look worse,
cost twelve times the bytes, and still be wrong at speeds between the frames.
So this cuts a single wheel, squares it about its own centre so the middle of
the image is the middle of the axle, and the game spins it off distance
travelled.

THE FLAME IS A CYCLE, because fire has no rule to solve. Six pictures of one
loop, each anchored on its ROOT -- the blunt bright end that sits in the pipe --
rather than on its bounding box, because the tip whips about and the root does
not. Anchoring on the box makes the whole flame jitter backwards and forwards
in the pipe at 12Hz, which is the one thing it must not do.

    python tools/cut_truckfx.py
"""
import os, sys, json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imglib import key_green, despill, bbox, label

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH   = os.path.join(ROOT, "sheets", "v2")
FX   = os.path.join(ROOT, "art", "fx")

WHEEL_PX = 320       # the wheel is drawn small; this is plenty and stays sharp
FLAME_H  = 260       # the tallest flame frame, in stored pixels


def cut_wheel():
    a = despill(key_green(Image.open(os.path.join(SH, "truck_wheel.png"))))
    m = a[..., 3] > 90
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    r = max(x1 - x0, y1 - y0) / 2.0
    """Square it ABOUT THE DISC, not about the sheet. The generator centres the
    subject well but not perfectly, and a wheel whose axle is four pixels off
    the middle of its own image wobbles once per revolution -- which is exactly
    what a buckled wheel looks like, so it reads as a bug rather than as
    imprecision."""
    s = int(np.ceil(r)) + 2
    L, T = int(round(cx)) - s, int(round(cy)) - s
    out = np.zeros((s * 2, s * 2, 4), np.uint8)
    sx0, sy0 = max(0, L), max(0, T)
    sx1, sy1 = min(a.shape[1], L + s * 2), min(a.shape[0], T + s * 2)
    out[sy0 - T:sy1 - T, sx0 - L:sx1 - L] = a[sy0:sy1, sx0:sx1]
    im = Image.fromarray(out, "RGBA").resize((WHEEL_PX, WHEEL_PX), Image.LANCZOS)
    im.save(os.path.join(FX, "wheel.webp"), "WEBP", quality=94, method=6)
    print("   wheel.webp        %dx%d  (disc r=%.0f of %d)" % (im.width, im.height, r, s))


def cut_flames():
    a = despill(key_green(Image.open(os.path.join(SH, "truck_flame.png"))))
    lab, n = label(a[..., 3] > 90)
    blobs = []
    for i in range(1, n + 1):
        m = lab == i
        if int(m.sum()) < a.shape[0] * a.shape[1] * 0.004: continue
        ys, xs = np.nonzero(m)
        blobs.append({"m": m, "x0": int(xs.min()), "x1": int(xs.max()) + 1,
                      "y0": int(ys.min()), "y1": int(ys.max()) + 1})
    """Reading order, not x order: the sheet comes back as a grid, so sort into
    rows first (anything whose centres are within half a blob height of each
    other is one row) and by x inside them."""
    hh = np.median([b["y1"] - b["y0"] for b in blobs])
    blobs.sort(key=lambda b: (round(((b["y0"] + b["y1"]) / 2) / (hh * 0.8)), b["x0"]))
    print("   %d flames on the sheet" % len(blobs))

    subs, meta = [], []
    for b in blobs:
        sub = a[b["y0"]:b["y1"], b["x0"]:b["x1"]].copy()
        sub[..., 3] = np.where(b["m"][b["y0"]:b["y1"], b["x0"]:b["x1"]], sub[..., 3], 0)
        subs.append(sub)
    scale = FLAME_H / float(max(s.shape[0] for s in subs))
    for i, sub in enumerate(subs):
        h = max(1, int(round(sub.shape[0] * scale)))
        w = max(1, int(round(sub.shape[1] * scale)))
        im = Image.fromarray(sub, "RGBA").resize((w, h), Image.LANCZOS)
        al = np.asarray(im)[..., 3]
        """The ROOT is the right-hand end -- the flame blows to the left, so the
        pipe is on the right. `ay` is the centre of mass of the rightmost eighth
        of the shape, which is the middle of the nozzle rather than the middle
        of a picture whose tail wanders."""
        cut = max(1, int(w * 0.125))
        rows = np.nonzero((al[:, -cut:] > 80).sum(1) > 0)[0]
        ay = float(rows.mean() + 0.5) if len(rows) else h / 2.0
        f = "flame%d.webp" % i
        im.save(os.path.join(FX, f), "WEBP", quality=92, method=6)
        meta.append({"f": f, "w": w, "h": h, "ay": round(ay, 1)})
        print("   %-16s %dx%d  root at y=%.0f" % (f, w, h, ay))
    return meta


def main():
    os.makedirs(FX, exist_ok=True)
    cut_wheel()
    meta = cut_flames()
    print(json.dumps(meta, separators=(",", ":")))
    return meta


if __name__ == "__main__":
    main()
