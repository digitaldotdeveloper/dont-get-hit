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
   3. **Tone is matched row by row.** Each panel's sky is nudged towards the
      mean of the three skies and its field towards the mean of the three
      fields, one row at a time and additively. The measurement only looks at
      pixels that are actually sky or actually grass, so a red barn cannot drag
      a row with it, and the dirt band below the ground line is skipped -- the
      game crops it and draws the road there instead.

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
    for y in range(gline):
        pick = is_sky if y < horizon else is_grass
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
        band = []
        for pick, y0, y1 in ((is_sky, 0, horizon), (is_grass, horizon, gline)):
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
    strip.save(OUT, 'WEBP', quality=90, method=6)

    rail = sum(RAIL_F)/3.0 + (target - sum(GROUND_F)/3.0)   # the rail slides too
    print('%s  %dx%d  %d KB' % (OUT, strip.width, strip.height, os.path.getsize(OUT)//1024))
    print('ground %.4f   rail %.4f   (both fractions of the image height)' % (target, rail))

    two = Image.new('RGB', (int(total*1.4), strip.height))
    two.paste(strip, (0, 0))
    two.paste(strip.crop((0, 0, int(total*0.4), strip.height)), (total, 0))
    two.resize((two.width//2, two.height//2), Image.LANCZOS).save('_farm_strip.png')
    return strip


if __name__ == '__main__':
    build()
