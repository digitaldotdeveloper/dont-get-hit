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
PURE = 40         # columns of pure connector at each end -- these must match exactly
BLEND_PILLAR = 8  # behind a column: just enough to stop the edge aliasing
BLEND_PLAIN = 56  # no column to hide it, so the join is eased in properly
BLEND = BLEND_PLAIN
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


def share_back(arrs):
    """Make a floor's variants share the structure along the back of the band.

       A floor tile is two things stacked: the BACK -- a kerb, a low wall, a
       hazard-striped lip, a fence -- which runs continuously down the whole
       corridor, and the SURFACE in front of it, which is where the variation
       belongs. Generating both twice gets you variants whose back structure is
       in a different place, or is a different thing entirely, and then the
       continuous element stops dead every time the floor shuffles: sand meeting
       a hard line and becoming red dirt, hazard chevrons that do not line up
       across the cut.

       That is the farm's fence again -- three rails across the top of the tile
       that two variants simply did not have -- and the cure is the same one, and
       the same rule: anything that has to LINE UP between two pictures is
       composited, never prompted. The tiles are all the same size, so the base's
       back is copied onto the variants and feathered where it meets their own
       ground.

       The surface in front is left alone. That is the half that is supposed to
       differ, and it is the half a player actually looks at."""
    if len(arrs) < 2:
        return arrs
    base = arrs[0].astype(float)
    h = base.shape[0]
    cut = int(h * 0.45)                  # back structure above, walking surface below
    feather = max(6, int(h * 0.05))
    out = [arrs[0]]
    for a in arrs[1:]:
        b = a.astype(float).copy()
        b[:cut] = base[:cut]
        t = np.linspace(0, 1, feather)[:, None, None]
        b[cut:cut + feather] = (base[cut:cut + feather] * (1 - t)
                                + b[cut:cut + feather] * t)
        out.append(np.clip(b, 0, 255).astype(np.uint8))
    return out


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
    # THE BAND IS THE PILLAR'S OWN HALF-WIDTH. Padding a narrow pillar out to a
    # fixed 40 columns by repeating its outermost column puts twenty columns of
    # horizontal smear beside every join -- a stretched sliver of wall reading as
    # a hard stripe, which is what was left once the cross-fade went. Scaled to
    # the panel's height the pillar is about 39 columns, so half of it is about
    # 19. Only the outermost column has to agree between two panels; the rest of
    # the band exists to carry the column, so it is exactly as wide as the column.
    half = a[:, a.shape[1] // 2:]                # centre -> outer edge, left to right
    pure = int(max(12, min(PURE, half.shape[1])))
    half = half[:, :pure].astype(float)

    conn = base.astype(float).copy()
    al = half[..., 3:4] / 255.0                  # composite the column over the wall
    conn[:, :pure, :3] = half[..., :3] * al + conn[:, :pure, :3] * (1 - al)
    conn[:, :pure, 3] = np.maximum(conn[:, :pure, 3], half[..., 3])
    return np.clip(conn, 0, 255).astype(np.uint8), pure


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


def _stamp_left(out, conn, blend, pure):
    ramp = np.linspace(0.0, 1.0, blend)[None, :, None]
    out[:, :pure] = conn[:, :pure]
    out[:, pure:pure + blend] = (conn[:, pure:pure + blend] * (1 - ramp)
                                 + out[:, pure:pure + blend] * ramp)
    return out


def stamp(a, conn, blend=BLEND_PLAIN, pure=PURE):
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
    out = _stamp_left(out, conn, blend, pure)
    out = _stamp_left(out[:, ::-1].copy(), conn, blend, pure)[:, ::-1]
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
            (conn, pure), score, how = pill, 0.0, 'pillar'
        else:
            conn, score = pick_connector(arrs); how = 'plain'; pure = PURE
        arrs = share_back(arrs)
        before = edge_gap(arrs)
        outs = [stamp(a, conn, BLEND_PILLAR if how == 'pillar' else BLEND_PLAIN, pure)
                for a in arrs]
        after = edge_gap(outs)
        print('  %-14s %d pictures  %-6s connector  worst join %5.1f -> %5.1f%s'
              % (name, len(files), how, before, after, '' if write else '   [dry run]'))
        if write:
            for f, o in zip(files, outs):
                # LOSSLESS HERE UNDOES opt_panels.py, and it did: re-running this
                # over an optimised set put 4 MB back on the download, because a
                # connector stamp is a few edge columns and this rewrote the whole
                # picture at quality 100 to place them.
                # q84 is opt_panels' own measured floor for a panel -- the number
                # it arrives at on nearly every one of these -- so writing at it
                # keeps the join work and leaves the file the size that tool
                # already proved was honest. Run `python tools/opt_panels.py`
                # after this to re-check, not to re-shrink.
                Image.fromarray(o, 'RGBA').save(f, 'WEBP', quality=84, method=6, exact=True)
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
