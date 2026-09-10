# -*- coding: utf-8 -*-
"""Build the icon set from the one master artwork.

   THE MASTER HAS ITS ROUNDED CORNERS BAKED IN, IN BLACK. That is fine for a
   favicon and fine for iOS -- which masks with a rounded rect of very nearly
   this shape, so the black never shows -- and it is wrong for Google Play,
   which wants a full 512x512 with alpha and applies its own mask. Handing Play
   a baked corner gets you a black notch in every surface that masks less
   aggressively than the artwork does.

   So the corners are flood-filled to transparent from each corner inwards,
   rather than by thresholding the whole image: the chicken has a black outline
   and half the sunburst has black in it, and a global "near-black is
   transparent" pass would eat holes out of the bird.
"""
import os, sys
from PIL import Image
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\it\Desktop\Dont Get Hit Icon.png"
OUT  = os.path.join(ROOT, "icon")
os.makedirs(OUT, exist_ok=True)

NEAR_BLACK = 34          # 0-255; the corners measured (0,0,0)

def corner_alpha(im):
    """Flood the baked corner mask to alpha 0, from the four corners only."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    q = deque()
    for sx, sy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        r, g, b, _ = px[sx, sy]
        if max(r, g, b) <= NEAR_BLACK:
            q.append((sx, sy)); seen[sy * w + sx] = 1
    n = 0
    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0); n += 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                r, g, b, _ = px[nx, ny]
                if max(r, g, b) <= NEAR_BLACK:
                    seen[ny * w + nx] = 1
                    q.append((nx, ny))
    return im, n

def save(im, name, size, opaque=False, bg=(0, 0, 0)):
    o = im.resize((size, size), Image.LANCZOS)
    if opaque:
        flat = Image.new("RGB", (size, size), bg)
        flat.paste(o, (0, 0), o if o.mode == "RGBA" else None)
        o = flat
    p = os.path.join(OUT, name)
    o.save(p)
    print("  %-22s %4dx%-4d %7d bytes" % (name, size, size, os.path.getsize(p)))

master = Image.open(SRC)
print("master:", master.size, master.mode)

cut, n = corner_alpha(master)
print("corner pixels made transparent: %d (%.2f%% of the image)" % (n, 100.0 * n / (master.size[0] * master.size[1])))

print("\nwith alpha corners -- Play listing, PWA, favicon:")
save(cut, "icon-512.png", 512)      # Play Store listing + PWA
save(cut, "icon-192.png", 192)      # PWA / Android home screen
save(cut, "icon-96.png",   96)
save(cut, "favicon-32.png", 32)
save(cut, "favicon-16.png", 16)

print("\nopaque -- iOS masks its own corners, so the baked ones never show:")
save(master, "apple-touch-icon.png", 180, opaque=True)

# A real .ico so a bare /favicon.ico request is not a 404
ico = os.path.join(OUT, "favicon.ico")
cut.resize((64, 64), Image.LANCZOS).save(ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
print("  %-22s multi-size %7d bytes" % ("favicon.ico", os.path.getsize(ico)))

# The master, kept in the repo so the set can be rebuilt without the Desktop file
mp = os.path.join(OUT, "icon-master.png")
master.save(mp)
print("  %-22s %4dx%-4d %7d bytes" % ("icon-master.png", master.size[0], master.size[1], os.path.getsize(mp)))
print("\nrebuild with:  python tools/make_icons.py")
