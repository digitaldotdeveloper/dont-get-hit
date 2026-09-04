# -*- coding: utf-8 -*-
"""Cut the Farm Scene obstacle sheets into art/farm/*.webp.

    sheets/v2/farm_props_c.png -> fence gate haywagon cart tractorwheel engine
    sheets/v2/farm_props_d.png -> corn1 corn3 cornrow mud
    sheets/v2/farm_elec_a.png  -> e_post e_posttall e_gateframe e_mill
                                  e_rotor e_bar e_battery e_sign

Same pipeline as cut_farm.py -- key the flat green, split by connected
component, trim each to what it owns -- with two differences:

* it keeps the N LARGEST blobs rather than everything over a pixel floor, so a
  stray grass tuft at the foot of a fence cannot shift the whole naming by one;
* `--contact` writes a numbered contact sheet. The row order a sheet comes back
  in is not the order it was asked for, so look at that before trusting names.

The windmill came back with its rotor already on the tower, and the rotor has
to turn on its own. `strip_grey` drops the metal out of the tower blob, which
leaves the timber -- cheaper and cleaner than masking by hand.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imglib import key_green, despill, bbox, label

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH   = os.path.join(ROOT, "sheets", "v2")
ART  = os.path.join(ROOT, "art", "farm")

SHEETS = [
    ("farm_props_c.png", ["fence", "gate", "haywagon",
                          "cart", "tractorwheel", "engine"]),
    ("farm_props_d.png", ["corn1", "corn3", "cornrow", "mud"]),
    ("farm_elec_a.png",  ["e_post", "e_posttall", "e_gateframe", "e_mill",
                          "e_rotor", "e_bar", "e_battery", "e_sign"]),
]


def parts(path, want, tol=52):
    """The `want` biggest objects on the green, back in reading order."""
    rgba = despill(key_green(Image.open(path), tol))
    lab, n = label(rgba[..., 3] > 0)
    cand = []
    for i in range(1, n + 1):
        m = lab == i
        px = int(m.sum())
        if px < 1200:
            continue
        bb = bbox(m)
        cand.append((px, i, m, bb))
    cand.sort(key=lambda c: -c[0])
    cand = cand[:want]
    out = []
    for px, i, m, bb in cand:
        sub = rgba[bb[1]:bb[3], bb[0]:bb[2]].copy()
        sub[..., 3] = np.where(m[bb[1]:bb[3], bb[0]:bb[2]], sub[..., 3], 0)
        out.append({"img": sub, "x": bb[0], "y": bb[1],
                    "w": bb[2] - bb[0], "h": bb[3] - bb[1]})
    # reading order: group into rows by centre-y, then left to right
    out.sort(key=lambda p: p["y"] + p["h"] / 2.0)
    rows = []
    for p in out:
        cy = p["y"] + p["h"] / 2.0
        for r in rows:
            if abs(cy - r["cy"]) < max(p["h"], r["h"]) * 0.6:
                r["items"].append(p)
                r["cy"] = np.mean([q["y"] + q["h"] / 2.0 for q in r["items"]])
                r["h"] = max(r["h"], p["h"])
                break
        else:
            rows.append({"cy": cy, "h": p["h"], "items": [p]})
    ordered = []
    for r in sorted(rows, key=lambda r: r["cy"]):
        ordered += sorted(r["items"], key=lambda p: p["x"])
    return ordered


def strip_grey(sub):
    """Drop the desaturated metal out of a piece, keeping the timber."""
    rgb = sub[..., :3].astype(np.int16)
    mx, mn = rgb.max(2), rgb.min(2)
    grey = (mx - mn < 34) & (mx > 96)
    out = sub.copy()
    out[..., 3] = np.where(grey, 0, out[..., 3])
    m = out[..., 3] > 0
    if not m.any():
        return sub
    lab, n = label(m)                       # keep the biggest surviving piece
    sizes = [(int((lab == i).sum()), i) for i in range(1, n + 1)]
    keep = max(sizes)[1]
    out[..., 3] = np.where(lab == keep, out[..., 3], 0)
    bb = bbox(lab == keep)
    return out[bb[1]:bb[3], bb[0]:bb[2]]


def crop_tower(sub):
    """Keep the windmill's timber, from its platform down.

    strip_grey takes the metal out of the rotor but not the black outline
    around each blade, and the hub stem keeps that wreckage connected to the
    tower. The platform is the first row from the top that is more than half
    as wide as the widest -- everything above it is rotor."""
    m = sub[..., 3] > 0
    wid = m.sum(1)
    top = int(np.argmax(wid > wid.max() * 0.55))
    return sub[top:]


def contact(path, ps, names):
    """A numbered strip of what was cut, at one shared scale."""
    H = 200
    sc = [H / float(p["h"]) for p in ps]
    ws = [int(p["w"] * s) for p, s in zip(ps, sc)]
    im = Image.new("RGB", (sum(ws) + 12 * len(ps), H + 26), (28, 12, 48))
    d, x = ImageDraw.Draw(im), 6
    for k, (p, s, w) in enumerate(zip(ps, sc, ws)):
        pc = Image.fromarray(p["img"], "RGBA").resize((w, H), Image.LANCZOS)
        im.paste(pc, (x, 0), pc)
        d.text((x + 2, H + 6), "%d %s %dx%d" % (k, names[k] if k < len(names)
                else "?", p["w"], p["h"]), fill=(255, 242, 222))
        x += w + 12
    im.save(path)
    return path


if __name__ == "__main__":
    os.makedirs(ART, exist_ok=True)
    for f, names in SHEETS:
        ps = parts(os.path.join(SH, f), len(names))
        if len(ps) != len(names):
            print("  %-18s WRONG COUNT: %d pieces for %d names"
                  % (f, len(ps), len(names)))
        for p, nm in zip(ps, names):
            img = p["img"]
            if nm == "e_mill":
                img = crop_tower(strip_grey(img))
            Image.fromarray(img, "RGBA").save(
                os.path.join(ART, nm + ".webp"), "WEBP", quality=88, method=6)
            print("  %-14s %dx%d" % (nm, img.shape[1], img.shape[0]))
        if "--contact" in sys.argv:
            print("  ->", contact(os.path.join(ROOT, "_cut_" +
                  f.split(".")[0] + ".png"), ps, names))
