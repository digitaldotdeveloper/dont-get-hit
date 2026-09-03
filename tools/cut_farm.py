# -*- coding: utf-8 -*-
"""Rebuild every asset the farm and the cage intro use, from the sheets in
sheets/v2. Run it from this directory:  python cut_farm.py

    sheets/v2/kick.png            -> anim/kick0..4.webp   (+ the FRAME_DATA rows)
    sheets/v2/boom.png            -> anim/boom0..4.webp
    sheets/v2/farm_props_a|b      -> art/farm/*.webp
    sheets/v2/farm_a|b|c_src.png  -> sheets/v2/farm_a|b|c.webp   (sky keyed out)
    sheets/v2/cage_src.png        -> sheets/v2/cage_scene.webp   (sky keyed out)
    sheets/v2/cage_door_src.png   -> art/cage_door.webp

It prints the FRAME_DATA rows for `kick` and `boom` rather than editing
index.html, because the anchors there are worth a human's eyes.
"""
import json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imglib import (key_green, despill, bbox, label, flood_split, fat_radius,
                    erode, key_sky)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH   = os.path.join(ROOT, "sheets", "v2")
ANIM = os.path.join(ROOT, "anim")
ART  = os.path.join(ROOT, "art", "farm")

REF_R = 30.0        # median fat radius of the run cycle: the size everything matches
COM_D = 100.0       # origin sits this far below the body core, measured off the
                    # grounded frames of the existing sets


def parts(path, tol=52, minpx=2500):
    """Every separate object on the green, in reading order (row, then x)."""
    rgba = despill(key_green(Image.open(path), tol))
    lab, n = label(rgba[..., 3] > 0)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        px = int(m.sum())
        if px < minpx: continue
        bb = bbox(m)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        if w < 14 or h < 14 or px / float(w * h) < 0.045: continue   # divider rules
        sub = rgba[bb[1]:bb[3], bb[0]:bb[2]].copy()
        sub[..., 3] = np.where(m[bb[1]:bb[3], bb[0]:bb[2]], sub[..., 3], 0)
        out.append({"img": sub, "x": bb[0], "y": bb[1], "w": w, "h": h})
    out.sort(key=lambda p: p["y"] + p["h"] / 2)
    rows = []
    for p in out:
        cy = p["y"] + p["h"] / 2
        for r in rows:
            if abs(cy - r["cy"]) < max(p["h"], r["h"]) * 0.6:
                r["items"].append(p)
                r["cy"] = np.mean([q["y"] + q["h"] / 2 for q in r["items"]])
                r["h"] = max(r["h"], p["h"]); break
        else:
            rows.append({"cy": cy, "h": p["h"], "items": [p]})
    ordered = []
    for r in sorted(rows, key=lambda r: r["cy"]):
        ordered += sorted(r["items"], key=lambda p: p["x"])
    return ordered


def cut_kick():
    """The escape. Five figures, split by flooding out from each teal cap --
    a straight vertical cut through overlapping chickens always clips a wing or
    a shoe, and this sheet has fewer empty-column gaps than figures."""
    rgba = despill(key_green(Image.open(os.path.join(SH, "kick.png"))))
    alpha, rgb = rgba[..., 3], rgba[..., :3]
    r, g, b = [rgb[..., i].astype(np.int16) for i in range(3)]
    teal = ((alpha > 0) & (g > 85) & (b > 85) & (r < 150) &
            (g > r + 22) & (b > r + 10) & (abs(g - b) < 70))
    lab, n = label(teal)
    sizes = sorted(((int((lab == i).sum()), i) for i in range(1, n + 1)), reverse=True)
    keep = sorted(sizes[:5], key=lambda s: np.nonzero(lab == s[1])[1].mean())
    seeds = [(int(np.nonzero(lab == i)[0].mean()), int(np.nonzero(lab == i)[1].mean()))
             for _, i in keep]
    own = flood_split(alpha, seeds, 5)

    figs = []
    for i in range(1, 6):
        m = own == i; bb = bbox(m)
        sub = rgba[bb[1]:bb[3], bb[0]:bb[2]].copy()
        sub[..., 3] = np.where(m[bb[1]:bb[3], bb[0]:bb[2]], sub[..., 3], 0)
        figs.append(sub)

    rads = np.array([fat_radius(f[..., 3] > 8) for f in figs], float)
    med = np.median(rads)
    s_sheet = (REF_R / med) * 0.95
    GROUNDED = [True, True, False, False, True]   # 2 and 3 are airborne
    meta = []
    for i, sub in enumerate(figs):
        sc = s_sheet * min(1.15, max(0.85, med / rads[i]))   # 15% per-frame trim
        im = Image.fromarray(sub, "RGBA")
        w, h = max(1, round(im.width * sc)), max(1, round(im.height * sc))
        im = im.resize((w, h), Image.LANCZOS)
        m = np.asarray(im)[..., 3] > 8
        for _ in range(5):
            m2 = erode(m)
            if not m2.any(): break
            m = m2
        ys, _ = np.nonzero(m)
        ay = float(h) if GROUNDED[i] else round(ys.mean() + COM_D, 1)
        im.save(os.path.join(ANIM, "kick%d.webp" % i), "WEBP", quality=88, method=6)
        meta.append({"f": "kick%d.webp" % i, "w": w, "h": h, "ay": ay})
    return meta


def cut_boom():
    bl = sorted(parts(os.path.join(SH, "boom.png"), minpx=1500), key=lambda p: p["x"])[:5]
    mx = max(p["w"] for p in bl)
    meta = []
    for i, p in enumerate(bl):
        im = Image.fromarray(p["img"], "RGBA")
        sc = 260.0 / mx                                  # one scale for the set
        w, h = max(1, round(im.width * sc)), max(1, round(im.height * sc))
        im.resize((w, h), Image.LANCZOS).save(
            os.path.join(ANIM, "boom%d.webp" % i), "WEBP", quality=86, method=6)
        meta.append({"f": "boom%d.webp" % i, "w": w, "h": h})
    return meta


def cut_props():
    os.makedirs(ART, exist_ok=True)
    # Names follow the ROW ORDER the sheets came back in, which is not the order
    # they were asked for -- check a contact sheet before trusting a new sheet.
    for f, names in (("farm_props_a.jpg",
                      ["haybale", "barrel", "trough", "crates", "wheelbarrow", "milkcan"]),
                     ("farm_props_b.png",
                      ["scarecrow", "feedbin", "tyre", "pitchfork", "kennel",
                       "drum_s", "hopper", "drum"])):
        ps = parts(os.path.join(SH, f), tol=42 if f.endswith("jpg") else 52)
        for p, nm in zip(ps, names):
            Image.fromarray(p["img"], "RGBA").save(
                os.path.join(ART, nm + ".webp"), "WEBP", quality=88, method=6)
        print("  %-18s %d pieces -> %s" % (f, len(ps), ", ".join(names)))


def cut_panels():
    for name, src in (("farm_a", "farm_a_src.png"), ("farm_b", "farm_b_src.png"),
                      ("farm_c", "farm_c_src.png")):
        rgba = key_sky(Image.open(os.path.join(SH, src)))
        Image.fromarray(rgba, "RGBA").save(os.path.join(SH, name + ".webp"),
                                           "WEBP", quality=86, method=6)
        print("  %-10s -> %s.webp" % (src, name))
    rgba = key_sky(Image.open(os.path.join(SH, "cage_src.png")))
    Image.fromarray(rgba, "RGBA").save(os.path.join(SH, "cage_scene.webp"),
                                       "WEBP", quality=90, method=6)
    d = despill(key_green(Image.open(os.path.join(SH, "cage_door_src.png"))))
    bb = bbox(d[..., 3] > 0)
    Image.fromarray(d[bb[1]:bb[3], bb[0]:bb[2]], "RGBA").save(
        os.path.join(ROOT, "art", "cage_door.webp"), "WEBP", quality=88, method=6)
    print("  cage scene + door")


if __name__ == "__main__":
    print("panels:");  cut_panels()
    print("props:");   cut_props()
    kick = cut_kick(); boom = cut_boom()
    print("\nFRAME_DATA rows -- paste these over the existing ones:")
    print('  "kick":' + json.dumps(kick, separators=(",", ":")))
    print('  "boom":' + json.dumps(boom, separators=(",", ":")))
