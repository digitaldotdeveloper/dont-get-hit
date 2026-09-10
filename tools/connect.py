# -*- coding: utf-8 -*-
"""Give every panel in a world the SAME left and right edge, so they just butt.

    python tools/connect.py            # report
    python tools/connect.py --write
    python tools/connect.py prison --write

THIS REPLACES THE OVERLAP, AND IT IS HOW SIDE-SCROLLERS ACTUALLY DO IT.

Six panels generated independently have six different edges. Butt them and the
join is a hard vertical line; the previous answer was to overlap them by 7% and
ramp each left edge, so the next panel dissolves in over the current one. That
hides the line and creates two worse things, both of which were reported:

    "the floor fading"                  -- the ramp, eating the near tile's edge
    "scene from behind suddenly appearing" -- in the overlap band you are looking
                                           at TWO walls at once, the new one
                                           materialising through the old one

Jetpack Joyride does not do that. Its room segments are authored so that every
segment's right edge is identical to every segment's left edge -- one fixed
connector profile per set -- and then any segment can follow any other and butt
perfectly, with no fade at all, ever.

This makes that true after the fact. For each world it finds the most FEATURELESS
band of columns across all of that world's pictures -- plain wall, no door, no
crate -- and stamps that same band onto both ends of every one of them, blending
inward so it merges with each picture's own content. Panel A's right edge is then
byte-identical to panel B's left edge, whichever two the game picks, and the
overlap and the ramp can go.

The blend is INSIDE the picture, over content, never at the edge: nothing is
faded to transparent, so nothing shows the sky through it and nothing appears
from behind anything."""
import glob
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PURE = 40      # columns of pure connector at each end -- these must match exactly
BLEND = 56     # columns over which the connector merges into the picture's own art
TILES = ('near', 'near2', 'near3', 'hang', 'far', 'mid', 'upper')


def groups():
    """Every set of pictures that must connect to each other."""
    out = {}
    for d in sorted(glob.glob(os.path.join(ROOT, 'art', 'panels', '*'))):
        w = os.path.basename(d)
        panels = sorted(f for f in glob.glob(os.path.join(d, '*.webp'))
                        if os.path.basename(f).split('.')[0] not in TILES)
        if len(panels) > 1:
            out[w] = panels
        floors = sorted(f for f in glob.glob(os.path.join(d, 'near*.webp')))
        if len(floors) > 1:
            out[w + ' floor'] = floors
    for name, d in (('farm floor', 'bg'), ('empire floor', 'ant')):
        fs = sorted(glob.glob(os.path.join(ROOT, 'art', d, 'near*.webp')))
        if len(fs) > 1:
            out[name] = fs
    return out


def busy(a):
    """How much each column differs from the one beside it -- low is plain wall."""
    return np.abs(np.diff(a[..., :3].astype(float), axis=1)).mean(axis=(0, 2))


def pillar_connector(world, arrs):
    """Build the connector out of that world's COLUMN, if one has been drawn.

       The plain-band connector works -- the joins measure zero -- and it reads
       flat: two featureless bands meeting is about 190px of dead wall every time
       two panels touch, which came back as "I don't like this fade". A column
       there is what a building actually has at that spacing.

       The column is SPLIT DOWN THE MIDDLE, and the arithmetic matters. Panels
       butt when the LAST column of one equals the FIRST column of the next, and
       stamp() achieves that by mirroring. So the connector's column 0 -- the one
       that lands on the frame edge at both ends -- has to be the PILLAR'S CENTRE,
       and column PURE-1 its outer edge. Then a join reads outer edge, centre,
       centre, outer edge: one whole symmetric column, assembled from two halves
       that were never in the same picture.

       Behind it, the rest of the band is the plainest wall in the world, so the
       column has something to stand against and the blend inward has somewhere
       to go."""
    f = os.path.join(ROOT, 'tools', 'pillars', world + '.webp')
    if not os.path.exists(f):
        return None
    base, _score = pick_connector(arrs)          # plain wall, full PURE+BLEND wide
    h = arrs[0].shape[0]
    p = Image.open(f).convert('RGBA')
    p = p.resize((max(2, int(round(p.width * h / float(p.height)))), h), Image.LANCZOS)
    a = np.asarray(p)
    half = a[:, a.shape[1] // 2:]                # centre -> outer edge, left to right
    if half.shape[1] < PURE:
        pad = np.repeat(half[:, -1:], PURE - half.shape[1], axis=1)
        half = np.concatenate([half, pad], axis=1)
    half = half[:, :PURE].astype(float)

    conn = base.astype(float).copy()
    al = half[..., 3:4] / 255.0                  # composite the column over the wall
    conn[:, :PURE, :3] = half[..., :3] * al + conn[:, :PURE, :3] * (1 - al)
    conn[:, :PURE, 3] = np.maximum(conn[:, :PURE, 3], half[..., 3])
    return np.clip(conn, 0, 255).astype(np.uint8)


def pick_connector(arrs):
    """The plainest PURE+BLEND band in the whole group, taken from wherever it is.

       Deliberately not synthesised: a made-up flat column reads as a smear in a
       brick wall. A real band of real wall, chosen for having nothing in it,
       reads as wall -- and because it is the same band on both ends of every
       picture, seeing it twice at a join is just seeing more wall."""
    w = PURE + BLEND
    best, where = None, None
    for i, a in enumerate(arrs):
        b = busy(a)
        if len(b) < w + 4:
            continue
        # only look near the ends: that is the kind of content an edge has
        for x in list(range(0, min(len(b) - w, 160))) + \
                 list(range(max(0, len(b) - w - 160), len(b) - w)):
            score = b[x:x + w].mean()
            if best is None or score < best:
                best, where = score, (i, x)
    i, x = where
    return arrs[i][:, x:x + w].copy(), best


def _stamp_left(out, conn):
    ramp = np.linspace(0.0, 1.0, BLEND)[None, :, None]
    out[:, :PURE] = conn[:, :PURE]
    out[:, PURE:PURE + BLEND] = (conn[:, PURE:PURE + BLEND] * (1 - ramp)
                                 + out[:, PURE:PURE + BLEND] * ramp)
    return out


def stamp(a, conn):
    """Both ends, and the right one is the MIRROR of the left.

       This is the whole trick and it is easy to get subtly wrong: for two
       pictures to butt invisibly, the LAST column of one has to equal the FIRST
       column of the next. Stamping the same band the same way round at both ends
       gives a right edge ending on the connector's LAST column against a left
       edge starting on its FIRST -- close, because the band is plain, but not
       equal, and it measured 10-45 RMSE instead of 0.

       Mirroring the picture, stamping the left, and mirroring back makes the
       outermost column at both ends the same column of the connector. Then the
       join is exact by construction, whichever two pictures the game happens to
       pick, and no fade is needed to cover it."""
    out = a.astype(float).copy()
    out = _stamp_left(out, conn)
    out = _stamp_left(out[:, ::-1].copy(), conn)[:, ::-1]
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    write = '--write' in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith('-')]
    for name, files in groups().items():
        if want and not any(w in name for w in want):
            continue
        arrs = [np.asarray(Image.open(f).convert('RGBA')) for f in files]
        if len(set(a.shape for a in arrs)) > 1:
            print('  %-14s mixed sizes -- skipped' % name)
            continue
        world = name.split()[0]
        pill = None if name.endswith('floor') else pillar_connector(world, arrs)
        if pill is not None:
            conn, score, how = pill, 0.0, 'pillar'
        else:
            conn, score = pick_connector(arrs); how = 'plain'
        before = edge_gap(arrs)
        outs = [stamp(a, conn) for a in arrs]
        after = edge_gap(outs)
        print('  %-14s %d pictures  %-6s connector  worst join %5.1f -> %5.1f%s'
              % (name, len(files), how, before, after, '' if write else '   [dry run]'))
        if write:
            for f, o in zip(files, outs):
                Image.fromarray(o, 'RGBA').save(f, 'WEBP', lossless=True, quality=100, method=6)
    if not write:
        print('\n[dry run; pass --write]')


def edge_gap(arrs):
    """Worst RMSE between any picture's right edge column and any other's left."""
    worst = 0.0
    for i, a in enumerate(arrs):
        for j, b in enumerate(arrs):
            if i == j:
                continue
            l = a[:, -1, :3].astype(float); r = b[:, 0, :3].astype(float)
            worst = max(worst, float(np.sqrt(((l - r) ** 2).mean())))
    return worst


if __name__ == '__main__':
    main()
