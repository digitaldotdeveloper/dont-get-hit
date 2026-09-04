# -*- coding: utf-8 -*-
"""Make the three farm panels into one painting.

   They are three separate paintings of the same farm, and the game was drawing
   them as three: overlapped, cross-faded into each other, and each scaled by a
   different amount so that two landmarks would line up. That is what produced
   the ghosting -- a silo showing faintly through a windmill -- and the fence
   that changes size halfway across the field.

   This joins them once, offline, and the game then draws a single image:

   1. **Seams are searched for, not assumed.** tools/farm_seams.py scores every
      pair of columns near the facing edges and keeps the pair that meets best,
      so the join lands where the fence, the horizon and the grass already
      agree. Content outside those columns is dropped.
   2. **Ground lines are levelled by shifting, never by scaling.** The painted
      ground sits at 0.785, 0.802 and 0.820 of the three images. Scaling each
      panel to reconcile that is what made the scenery change size; sliding each
      one down instead keeps every fence post the size it was painted, and the
      sky it exposes at the top is the panel's own top row.
   3. **The painted sky is thrown away.** The three skies are not variations of
      one sky, they are different skies: (27,157,252), (56,182,253) and
      (1,117,216) at the same height. Nothing short of repainting reconciles
      that, and matching them flattens the art while still leaving a step. So
      the sky is keyed out and the game's own gradient shows through the whole
      strip -- one sky by construction, and one less thing to keep in step. The
      painted clouds stay: they are enclosed by sky, so the flood never reaches
      them.
   4. **The fields are tone-matched** row by row, additively, measuring only
      pixels that are actually grass so a red barn cannot drag a row with it,
      and the seams get a local correction on top. The dirt band below the
      ground line is skipped -- the game crops it and draws the road there.

     python tools/farm_strip.py          # -> sheets/v2/farm_strip.webp
"""
import io, json, os, sys
from PIL import Image

SRCS = ['sheets/v2/farm_a.webp', 'sheets/v2/farm_b.webp', 'sheets/v2/farm_c.webp']
OUT = 'sheets/v2/farm_strip.webp'
SPANS = [[259, 927], [147, 983], [3, 975]]      # from tools/farm_seams.py
GROUND_F = [0.7850, 0.8024, 0.8199]             # painted ground line, per panel
RAIL_F = [0.6084, 0.6102, 0.6119]               # top of the fence's top rail
KEEP = 0.86                                     # tone is measured above this


def level(im, gf, target):
    """Slide the painting down so its ground line sits at `target`, filling the
       sky it uncovers with the panel's own top row."""
    dy = int(round((target - gf) * im.height))
    if dy <= 0: return im, gf
    out = Image.new('RGB', im.size)
    sky = im.crop((0, 0, im.width, 2)).resize((im.width, dy), Image.BILINEAR)
    out.paste(sky, (0, 0))
    out.paste(im.crop((0, 0, im.width, im.height - dy)), (0, dy))
    return out, target


def band_mean(im, span, y, pick):
    """The mean colour of one row, over the pixels that are the thing being
       matched -- sky pixels in the sky, grass pixels in the grass. Measuring
       the whole row instead would let a red barn drag the correction with it."""
    px = im.load()
    tot = [0.0, 0.0, 0.0]; n = 0
    for x in range(span[0], span[1], 3):
        c = px[x, y]
        if pick(c):
            tot[0] += c[0]; tot[1] += c[1]; tot[2] += c[2]; n += 1
    return ([t/n for t in tot], n) if n > 8 else (None, 0)


def is_sky(c):   return c[2] > c[0] + 24 and c[2] > 110
def is_grass(c): return c[1] > c[0] + 10 and c[1] > c[2] + 20


def match_rows(ims, spans, ground_f):
    """Correct each panel towards the group so the three skies become one sky
       and the three fields one field. Additive only -- a gain would flatten the
       clouds, and all that has to agree here is the tone.

       The corrections are worked out per row and then SMOOTHED down the image
       before they are applied. Measured row by row and used raw they band the
       sky visibly: a row that happens to be mostly cloud offers only a handful
       of sky pixels to average, the delta jumps against its neighbours, and the
       result is a stack of horizontal stripes -- which is exactly what the
       first attempt painted across panel B."""
    h = ims[0].height
    horizon = int(h*0.62)
    gline = int(h*ground_f)
    span_n = [max(1, (sp[1]-sp[0])//3) for sp in spans]

    deltas = [[None]*gline for _ in ims]          # per panel, per row, per channel
    # rows above the horizon are sky and are about to be keyed away entirely
    for y in range(horizon, gline):                # the sky is keyed out, not matched
        pick = is_grass
        means, counts = [], []
        for im, sp in zip(ims, spans):
            m, n = band_mean(im, sp, y, pick)
            means.append(m); counts.append(n)
        if any(m is None for m in means): continue
        if any(counts[i] < span_n[i]*0.22 for i in range(len(ims))): continue
        tgt = [sum(m[c] for m in means)/len(means) for c in range(3)]
        for i, m in enumerate(means):
            deltas[i][y] = [tgt[c]-m[c] for c in range(3)]

    SM = 21                                        # rows in the smoothing window
    CAP = 16.0                                     # no correction is bigger than this
    out = []
    for i, im in enumerate(ims):
        d = deltas[i]
        last = [0.0, 0.0, 0.0]                     # carry the last good row into gaps
        filled = []
        for y in range(gline):
            if d[y] is not None: last = d[y]
            filled.append(last)
        sm = []
        for y in range(gline):
            lo, hi = max(0, y-SM//2), min(gline, y+SM//2+1)
            sm.append([max(-CAP, min(CAP, sum(filled[k][c] for k in range(lo, hi))/(hi-lo)))
                       for c in range(3)])
        cp = im.copy()
        for y in range(gline):
            dd = sm[y]
            if max(abs(v) for v in dd) < 0.8: continue
            row = cp.crop((0, y, cp.width, y+1))
            row = row.point([max(0, min(255, int(v + dd[c]))) for c in range(3) for v in range(256)])
            cp.paste(row, (0, y))
        out.append(cp)
    return out


def feather_seams(strip, seams, ground_f, reach=260):
    """Take the step out of each join.

       Matching whole panels row by row cannot fix a join, because the sky in
       these paintings is not flat across a panel: it darkens towards one edge,
       so two panels can have identical row averages and still meet with a
       visible step. This measures the difference across each seam and spreads
       half of it into each side, fading to nothing over a couple of hundred
       pixels.

       Two numbers per seam, not one per row: a sky offset and a grass offset,
       each averaged over its whole band and blended between. Per-row deltas
       sound better and are worse -- where a cloud or a watchtower happens to
       sit against the seam there is nothing to measure, the row falls back to
       its neighbour, and the fix either bands or quietly does nothing, which is
       what left the second seam stepping by 30 points of red."""
    w, h = strip.size
    gline = int(h*ground_f)
    horizon = int(h*0.62)
    px = strip.load()
    CAP = 34.0
    for sx in seams:
        def side_mean(x0, dirn, pick, y0, y1):
            tot = [0.0, 0.0, 0.0]; n = 0
            for k in range(20):
                x = (x0 + dirn*k) % w
                for y in range(y0, y1, 2):
                    c = px[x, y]
                    if pick(c):
                        tot[0] += c[0]; tot[1] += c[1]; tot[2] += c[2]; n += 1
            return ([t/n for t in tot], n) if n > 40 else (None, n)
        band = [[0.0, 0.0, 0.0]]                   # the sky is keyed out; nothing to match
        for pick, y0, y1 in ((is_grass, horizon, gline),):
            L, nl = side_mean(sx-1, -1, pick, y0, y1)
            R, nr = side_mean(sx,    +1, pick, y0, y1)
            if L is None or R is None: band.append([0.0, 0.0, 0.0]); continue
            band.append([max(-CAP, min(CAP, L[c]-R[c])) for c in range(3)])
        sky_d, grass_d = band
        fade0, fade1 = horizon - 60, horizon + 60
        for k in range(reach):
            t = 1.0 - k/float(reach)
            t = t*t*(3-2*t)                       # smoothstep, so the fix has no edge
            xr = (sx + k) % w
            xl = (sx - 1 - k) % w
            for y in range(gline):
                if y <= fade0: d = sky_d
                elif y >= fade1: d = grass_d
                else:
                    u = (y-fade0)/float(fade1-fade0)
                    d = [sky_d[c]*(1-u) + grass_d[c]*u for c in range(3)]
                cr = px[xr, y]
                px[xr, y] = tuple(max(0, min(255, int(cr[c] + d[c]*0.5*t))) for c in range(3))
                cl = px[xl, y]
                px[xl, y] = tuple(max(0, min(255, int(cl[c] - d[c]*0.5*t))) for c in range(3))
    return strip


def key_sky(strip, ground_f):
    """Flood the sky away from the top edge, so the game's gradient shows.

       A flood, not a colour key: the clouds are white and enclosed by sky, so
       the flood cannot reach them and they survive as painted clouds over the
       game's sky. Nothing else in the picture is this blue, and the windmill's
       lattice and the gaps under the water tower open onto the sky, so they
       clear too."""
    strip = strip.convert('RGBA')
    w, h = strip.size
    px = strip.load()
    gline = int(h*ground_f)

    def skyish(c):
        return c[3] and c[2] > c[0] + 40 and c[2] > 150 and c[1] > c[0] + 20

    from collections import deque
    seen = bytearray(w*h)
    q = deque()
    for x in range(w):
        if skyish(px[x, 0]): seen[x] = 1; q.append((x, 0))
    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < gline and not seen[ny*w+nx] and skyish(px[nx, ny]):
                seen[ny*w+nx] = 1; q.append((nx, ny))

    # one pass of feathering, so the hard pixel edge does not fizz against a
    # gradient it was never painted over
    edge = []
    for y in range(1, gline-1):
        for x in range(1, w-1):
            if px[x, y][3] == 0: continue
            if (px[x-1, y][3] == 0 or px[x+1, y][3] == 0 or
                px[x, y-1][3] == 0 or px[x, y+1][3] == 0):
                edge.append((x, y))
    for x, y in edge:
        c = px[x, y]
        px[x, y] = (c[0], c[1], c[2], 170)
    return strip


def build():
    ims = [Image.open(s).convert('RGB') for s in SRCS]
    target = max(GROUND_F)
    levelled = []
    for im, gf in zip(ims, GROUND_F):
        out, _ = level(im, gf, target)
        levelled.append(out)
    fixed = match_rows(levelled, SPANS, target)

    total = sum(e-s for s, e in SPANS)
    strip = Image.new('RGB', (total, ims[0].height))
    x = 0
    for im, (s, e) in zip(fixed, SPANS):
        strip.paste(im.crop((s, 0, e, im.height)), (x, 0)); x += e-s
    seams = []
    x = 0
    for sp in SPANS[:-1]:
        x += sp[1]-sp[0]; seams.append(x)
    seams.append(0)                                # the loop point is a seam too
    strip = feather_seams(strip, seams, target)
    strip = key_sky(strip, target)
    strip.save(OUT, 'WEBP', quality=90, method=6, lossless=False, exact=True)

    rail = sum(RAIL_F)/3.0 + (target - sum(GROUND_F)/3.0)   # the rail slides too
    print('%s  %dx%d  %d KB' % (OUT, strip.width, strip.height, os.path.getsize(OUT)//1024))
    print('ground %.4f   rail %.4f   (both fractions of the image height)' % (target, rail))

    two = Image.new('RGB', (int(total*1.4), strip.height), (34, 120, 214))
    two.paste(strip, (0, 0), strip)
    cut = strip.crop((0, 0, int(total*0.4), strip.height))
    two.paste(cut, (total, 0), cut)
    two.resize((two.width//2, two.height//2), Image.LANCZOS).save('_farm_strip.png')
    return strip


if __name__ == '__main__':
    build()
