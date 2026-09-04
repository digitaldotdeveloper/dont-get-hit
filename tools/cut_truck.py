# -*- coding: utf-8 -*-
"""Cut the driving-truck frames and the mystery egg.

The truck is drawn anchored on its AXLE LINE, not on the bottom of its picture,
because the tyres are what sit on the road and they are a good fraction of the
image. The four frames are drawn at four different tilts, so their bounding
boxes disagree wildly -- normalising them to a common box would make the truck
grow and shrink as it jumped. Instead each frame records where its own tyre
contact sits inside it (`ay`), and one scale is applied to the whole sheet off
the DRIVING frame, so the truck is the size it is on the road and every other
frame is measured against that.

    python cut_truck.py     # sheets/v2/truck_ride.png -> art/truck_ride*.webp
"""
import os, sys, json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imglib import key_green, despill, bbox, label

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH   = os.path.join(ROOT, "sheets", "v2")
ART  = os.path.join(ROOT, "art")

DRIVE_W = 815.0      # the width the reference art/truck.webp is drawn at
NAMES   = ["drive", "launch", "air", "land"]


def main():
    rgba = despill(key_green(Image.open(os.path.join(SH, "truck_ride.png"))))
    """Split on CONNECTED COMPONENTS, not column gaps. The four trucks are drawn
    at four tilts and overlap each other horizontally -- two of them share a
    column run -- so a vertical cut puts half a tyre in the wrong frame. Each
    truck is one connected blob; the only loose piece is the cap flying off the
    driver's head in the launch frame, and that is given back to the nearest
    truck rather than dropped, because it is the best thing in the sheet."""
    lab, n = label(rgba[..., 3] > 0)
    blobs = []
    for i in range(1, n + 1):
        m = lab == i
        a = int(m.sum())
        if a < 200: continue
        xs = np.nonzero(m.any(0))[0]
        blobs.append({"m": m, "a": a, "x0": int(xs.min()), "x1": int(xs.max()) + 1})
    trucks = sorted([b for b in blobs if b["a"] > 3000], key=lambda b: b["x0"])
    seen = set(id(t) for t in trucks)   # `in` would compare the numpy masks
    print("  %d trucks, %d loose pieces" % (len(trucks), len(blobs) - len(trucks)))
    for b in blobs:
        if id(b) in seen: continue
        c = (b["x0"] + b["x1"]) / 2
        t = min(trucks, key=lambda q: abs((q["x0"] + q["x1"]) / 2 - c))
        t["m"] = t["m"] | b["m"]
        t["x0"] = min(t["x0"], b["x0"]); t["x1"] = max(t["x1"], b["x1"])
    subs = []
    for t in trucks:
        bb = bbox(t["m"])
        sub = rgba[bb[1]:bb[3], bb[0]:bb[2]].copy()
        sub[..., 3] = np.where(t["m"][bb[1]:bb[3], bb[0]:bb[2]], sub[..., 3], 0)
        subs.append(sub)

    # one scale for the sheet, taken off the DRIVING frame's width
    scale = DRIVE_W / subs[0].shape[1]
    meta = []
    for i, sub in enumerate(subs):
        im = Image.fromarray(sub, "RGBA")
        w = max(1, round(im.width * scale))
        h = max(1, round(im.height * scale))
        im = im.resize((w, h), Image.LANCZOS)
        # the tyre contact: the lowest row with real coverage, not the lowest
        # stray antialiased pixel
        a = np.asarray(im)[..., 3]
        rows = np.nonzero((a > 80).sum(1) > w * 0.02)[0]
        ay = float(rows.max() + 1) if len(rows) else float(h)
        f = "truck_%s.webp" % NAMES[i]
        im.save(os.path.join(ART, f), "WEBP", quality=92, method=6)
        meta.append({"f": f, "w": w, "h": h, "ay": round(ay, 1)})
        print("   %-18s %dx%d  axle at %.0f" % (f, w, h, ay))

    # the mystery egg: one picture, its own glow kept
    eg = despill(key_green(Image.open(os.path.join(SH, "mystery_egg.png")), 62))
    bb = bbox(eg[..., 3] > 0)
    im = Image.fromarray(eg[bb[1]:bb[3], bb[0]:bb[2]], "RGBA")
    im = im.resize((max(1, round(300 * im.width / im.height)), 300), Image.LANCZOS)
    im.save(os.path.join(ART, "mystery_egg.webp"), "WEBP", quality=92, method=6)
    print("   mystery_egg.webp   %dx%d" % (im.width, im.height))
    print(json.dumps(meta, separators=(",", ":")))
    return meta


if __name__ == "__main__":
    main()
