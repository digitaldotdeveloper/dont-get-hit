# -*- coding: utf-8 -*-
"""Cut the angry-crow sheets into art/farm/crow1..4.webp + crowhead.webp.

    sheets/v4/crow_raw_6.png  -> crow1 crow2 crow3 crow4   (one flap cycle)
    sheets/v4/crow_raw_2.png  -> crowhead                  (the alert badge)

Same green key and connected-component split as cut_obstacles.py, plus the one
thing a CYCLE needs and a set of props does not: REGISTRATION.

Cutting each frame to its own bounding box and drawing them all centred makes
the bird lurch about the screen, because the box is mostly wing and the wing is
the thing that moves. Gemini also draws one cell of a 2x2 a little smaller than
the others. So both are fixed off the one feature that is identical in every
frame -- the open orange beak:

  scale   each frame so its beak is the same width as the median beak
  anchor  every frame on the beak TIP, and on the beak's vertical centre

After that the head sits still and only the wings beat, which is the whole
point. `--preview` writes a strip and an animated GIF to check that by eye.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imglib import key_green, despill, bbox, label

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH   = os.path.join(ROOT, "sheets", "v4")
ART  = os.path.join(ROOT, "art", "farm")

FLY  = "crow_raw_6.png"          # the 2x2 whose four bodies sit level
HEAD = "crow_raw_2.png"          # the screaming head, for the warning badge

# the canvas every registered frame is pasted into, in beak-tip units
PAD_L, PAD_R, PAD_U, PAD_D = 40, 700, 330, 330


def blobs(path, want, floor=1500):
    """The `want` biggest objects on the green, in reading order."""
    rgba = despill(key_green(Image.open(path), 52))
    lab, n = label(rgba[..., 3] > 0)
    cand = []
    for i in range(1, n + 1):
        m = lab == i
        px = int(m.sum())
        if px < floor:
            continue
        bb = bbox(m)
        cand.append((px, m, bb))
    cand.sort(key=lambda c: -c[0])
    out = []
    for px, m, bb in cand[:want]:
        sub = rgba[bb[1]:bb[3], bb[0]:bb[2]].copy()
        sub[..., 3] = np.where(m[bb[1]:bb[3], bb[0]:bb[2]], sub[..., 3], 0)
        out.append({"img": sub, "x": bb[0], "y": bb[1],
                    "w": bb[2] - bb[0], "h": bb[3] - bb[1]})
    # rows first, then left to right
    out.sort(key=lambda p: p["y"] + p["h"] / 2.0)
    rows = []
    for p in out:
        cy = p["y"] + p["h"] / 2.0
        for r in rows:
            if abs(cy - r["cy"]) < max(p["h"], r["h"]) * 0.6:
                r["items"].append(p)
                r["h"] = max(r["h"], p["h"])
                break
        else:
            rows.append({"cy": cy, "h": p["h"], "items": [p]})
    ordered = []
    for r in rows:
        ordered += sorted(r["items"], key=lambda p: p["x"])
    return ordered


def beak(sub):
    """The open orange beak: (tip_x, centre_y, width) in the frame's own pixels.

    It is the only part of the bird that is the same shape in all four frames,
    which is what makes it the registration mark. Legs are orange too, so the
    beak is specifically the orange blob that owns the leftmost orange pixel --
    the bird faces left in every frame."""
    a = sub[..., :3].astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (sub[..., 3] > 0) & (r > 175) & (g > 80) & (g < 200) & (b < 120) & (r - b > 90)
    if not m.any():
        raise SystemExit("no beak found -- the key or the colours moved")
    lab, n = label(m)
    xs = np.nonzero(m.any(0))[0]
    left = int(xs.min())
    which = lab[:, left][lab[:, left] > 0]
    i = int(np.bincount(which).argmax())
    bm = lab == i
    bb = bbox(bm)
    ys = np.nonzero(bm[:, bb[0]:bb[0] + 4].any(1))[0]
    return bb[0], float(ys.mean()), float(bb[2] - bb[0])


def register(subs):
    """Scale every frame to the median beak, and hang them all off the tip."""
    marks = [beak(s) for s in subs]
    med = float(np.median([m[2] for m in marks]))
    out = []
    W, H = PAD_L + PAD_R, PAD_U + PAD_D
    for sub, (bx, by, bw) in zip(subs, marks):
        k = med / bw
        im = Image.fromarray(sub, "RGBA")
        if abs(k - 1) > 0.005:
            im = im.resize((max(1, int(round(im.width * k))),
                            max(1, int(round(im.height * k)))), Image.LANCZOS)
        ax, ay = bx * k, by * k                      # the anchor, in scaled pixels
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(im, (int(round(PAD_L - ax)), int(round(PAD_U - ay))), im)
        out.append(canvas)
    # trim the four together, so they keep the registration they just gained
    acc = np.zeros((H, W), bool)
    for c in out:
        acc |= np.asarray(c)[..., 3] > 0
    bb = bbox(acc)
    return [c.crop((bb[0], bb[1], bb[2], bb[3])) for c in out]


def preview(frames, head):
    strip = Image.new("RGB", (frames[0].width * 4 + 50, frames[0].height + 26), (28, 12, 48))
    d = ImageDraw.Draw(strip)
    for i, f in enumerate(frames):
        strip.paste(f, (10 + i * (f.width + 10), 0), f)
        d.text((12 + i * (f.width + 10), f.height + 6),
               "crow%d  %dx%d" % (i + 1, f.width, f.height), fill=(255, 242, 222))
    strip.save(os.path.join(ROOT, "_crow_strip.png"))
    flat = [Image.alpha_composite(Image.new("RGBA", f.size, (30, 140, 220, 255)), f).convert("P")
            for f in frames]
    flat[0].save(os.path.join(ROOT, "_crow_flap.gif"), save_all=True,
                 append_images=flat[1:], duration=58, loop=0)
    head.save(os.path.join(ROOT, "_crow_head.png"))
    print("  preview -> _crow_strip.png  _crow_flap.gif  _crow_head.png")


if __name__ == "__main__":
    os.makedirs(ART, exist_ok=True)
    subs = [p["img"] for p in blobs(os.path.join(SH, FLY), 4)]
    if len(subs) != 4:
        raise SystemExit("wanted 4 crows, found %d" % len(subs))
    frames = register(subs)
    for i, f in enumerate(frames):
        f.save(os.path.join(ART, "crow%d.webp" % (i + 1)), "WEBP", quality=90, method=6)
        print("  crow%d  %dx%d" % (i + 1, f.width, f.height))
    hp = blobs(os.path.join(SH, HEAD), 1)[0]
    head = Image.fromarray(hp["img"], "RGBA")
    head.save(os.path.join(ART, "crowhead.webp"), "WEBP", quality=90, method=6)
    print("  crowhead  %dx%d" % (head.width, head.height))
    if "--preview" in sys.argv:
        preview(frames, head)
