import numpy as np, json, os, sys
from PIL import Image

GEN = "gen"
OUT = r"C:\Users\it\Desktop\jj-landscape"
ANIM = os.path.join(OUT, "anim")

def key_green(im, tol=52):
    """Alpha-key a flat green screen. Returns RGBA float-safe uint8 array."""
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # generous: green channel clearly dominant over both others
    green = (g - np.maximum(r, b)) > tol
    rgba = np.dstack([a.astype(np.uint8), np.where(green, 0, 255).astype(np.uint8)])
    return rgba

def despill(rgba):
    """Pull the green fringe out of the surviving edge pixels."""
    a = rgba.astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lim = np.maximum(r, b)
    over = (g > lim) & (rgba[..., 3] > 0)
    a[..., 1] = np.where(over, lim, g)
    return a.astype(np.uint8)

def col_split(alpha, n, minrun=6):
    """Split by empty-column gaps, keeping the n widest pieces."""
    cols = alpha.sum(0) > 0
    runs, s = [], None
    for x, v in enumerate(cols):
        if v and s is None: s = x
        elif not v and s is not None:
            runs.append((s, x)); s = None
    if s is not None: runs.append((s, len(cols)))
    runs = [r for r in runs if r[1] - r[0] >= minrun]
    runs.sort(key=lambda r: r[1] - r[0], reverse=True)
    runs = sorted(runs[:n])
    return runs

def bbox(alpha):
    ys, xs = np.nonzero(alpha)
    if not len(ys): return None
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1

def cap_area(rgb, alpha):
    """Teal baseball cap pixels — the one thing the same size in every pose."""
    r, g, b = [rgb[..., i].astype(np.int16) for i in range(3)]
    teal = (alpha > 0) & (g > 85) & (b > 85) & (r < 150) & (g > r + 22) & (b > r + 10) & (abs(g - b) < 70)
    return int(teal.sum())

from collections import deque

def label(mask):
    """4-connected components. Returns (labels, count) with 0 = background."""
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    n = 0
    for sy in range(h):
        row = mask[sy]
        for sx in range(w):
            if not row[sx] or lab[sy, sx]: continue
            n += 1
            q = deque([(sy, sx)]); lab[sy, sx] = n
            while q:
                y, x = q.popleft()
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny, nx = y+dy, x+dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = n; q.append((ny, nx))
    return lab, n

def flood_split(alpha, seeds, n):
    """Multi-source BFS: every silhouette pixel joins the seed it is nearest to
    THROUGH the silhouette, so a leg that crosses in front of a neighbour still
    goes with its own body. A straight cut always clips a wing or a shoe."""
    h, w = alpha.shape
    own = np.zeros((h, w), np.int32)
    q = deque()
    for i, (sy, sx) in enumerate(seeds, 1):
        own[sy, sx] = i; q.append((sy, sx))
    solid = alpha > 0
    while q:
        y, x = q.popleft(); me = own[y, x]
        for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny, nx = y+dy, x+dx
            if 0 <= ny < h and 0 <= nx < w and solid[ny, nx] and not own[ny, nx]:
                own[ny, nx] = me; q.append((ny, nx))
    return own

def erode(m):
    e = m.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0: continue
            s = np.zeros_like(m)
            ys0, ys1 = max(0, dy), m.shape[0] + min(0, dy)
            xs0, xs1 = max(0, dx), m.shape[1] + min(0, dx)
            s[ys0:ys1, xs0:xs1] = m[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
            e &= s
    return e

def fat_radius(mask):
    """How many times the silhouette can be shrunk before it vanishes - the
    radius of his fattest part. Ignores wing spread, leg position and which way
    up he is, which is why it sizes poses consistently where cap area does not."""
    m = mask.copy(); n = 0
    while m.any():
        m = erode(m); n += 1
    return n


def key_sky(im):
    """Flood the blue sky out from the top row. It stops dead at the black ink
    outlines, which is what makes it reliable on this art; the painted clouds
    are white, fail the blue test, and survive as cutouts."""
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    h, w = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    sky = (b > 140) & ((b - r) > 45) & (b >= g)
    seen = np.zeros((h, w), bool)
    q = deque((0, x) for x in range(w) if sky[0, x])
    for _, x in list(q): seen[0, x] = True
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and sky[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    return np.dstack([a.astype(np.uint8), np.where(seen, 0, 255).astype(np.uint8)])
