# -*- coding: utf-8 -*-
"""Check every background picture in the game for the faults we have shipped.

    python tools/audit_map.py            # every panel and tile, worst first
    python tools/audit_map.py --all      # ...including the ones that pass

Eyeballing 54 pictures does not work -- half of what is wrong with a panel is
invisible until it is beside its neighbour, and by then it is in the game. Each
check below is a fault that actually reached a screenshot, written down so it
cannot reach one twice:

  SLICED        the picture ends MID-OBJECT -- a mound or a shed cut off with
                a straight vertical line. Screenshotted three times and missed
                by every check here, because the cutter centres the picture
                afterwards and the slice ends up sitting inside the margin,
                where a test that reads the frame's edge columns cannot see it.
  RAMP BITE     content sitting inside the 7% the game ramps as it draws. That
                ramp is what dissolves one panel into the next; landing it on a
                real object is what made a coop and a tree see-through.
  CUTOUT EDGE   content touching the frame edge. A panel is placed BESIDE other
                panels, so anything running off its own edge butts into whatever
                the next one starts with -- half a barn door against half an egg
                shelf. (Tiles are exempt: they are MEANT to reach both edges.)
  GROUND RULE   the solid dark bar the generator paints under a row. In the game
                that bar is the edge of a rectangle and the panel reads as
                pasted on.
  HAZARD HUE    anything in the wire's own colour, 165-265 degrees at real
                saturation. Blue means the thing that kills you, everywhere.
  STACKED ROWS  two rows of buildings in a frame that holds one, which comes out
                at half scale with a row floating in the sky.
  THIN FLOOR    a `near` tile is scaled BY ITS HEIGHT, so height is resolution.
                Under ~140px it gets magnified into mush.
  OPEN SEAM     a tile is repeated against ITSELF, so its left and right edges
                have to meet. Scored by comparing the two edge columns.
  SQUAT / TALL  a panel far off the reference aspect is a panel at the wrong
                scale, because the slot places all of them with one number.

Nothing here is a judgement about whether a picture is GOOD. It catches the
mechanical faults; the ones about taste still need eyes."""
import colorsys
import glob
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_mid_panels import INTERIORS, OUTDOORS              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_ASPECT = 830 / 240.0          # art/bg/mid.webp, which every panel is cut to


# WHAT COUNTS AS THE HAZARD HUE, and it is narrower than "blue-ish".
# The wire is #4CCFFF, hue 197. What competes with it is CYAN THROUGH BLUE,
# 170-250. Violet past that does not: the haze in the lab set is 255-263 dark
# purple-grey silhouettes, which is haze rather than paint and has to stay.
#
# THE VALUE FLOOR IS 0.12, NOT 0.25, AND THAT WAS A REAL MISS. A DARK navy is
# still navy: the alien facility's floor came back 33% hexagonal tiles at hue
# 235, saturation 0.43 -- unmistakably blue on screen, on the layer closest to
# the player -- and it passed clean because its value was 0.20. Re-measured
# across the whole map, dropping the floor to 0.12 flags those two tiles at 40%
# and 26% and nothing else above 0.2%, which is the trace the de-hue in
# opt_panels.py clears on its next pass. The old floor was not protecting
# anything; it was hiding one thing.
# This comment used to go on to defend the magenta accents in the alien facility
# and in space. Those are gone now, for an unrelated reason worth knowing here:
# the colour key deletes any bright pink or purple pixel, because that is how
# the sky is removed -- so asking for magenta in the artwork was asking for a
# hole through the middle of the picture.
def hazard_px(a):
    op = a[..., 3] > 40
    if not op.any():
        return 0
    rgb = a[op][..., :3] / 255.0
    n = 0
    for r, g, b in rgb[::7]:       # every 7th pixel: enough to catch a glow
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if 170 <= h * 360 <= 250 and s > 0.25 and v > 0.12:
            n += 1
    return n * 7


def wall_cover(a):
    """For an INTERIOR panel: how much of the frame the space actually fills.

       This is the check that was missing while the map was at its worst. Every
       one of the 65 pictures passed every test in this file, and the map still
       looked like an asset flip, because nothing here asked the question a
       person asks in one glance: is this a PLACE, or is it four objects with
       nothing between them? A prison panel drawn as four detached cell doors
       has a clean key, clean edges, no hazard hue, one row and the right
       aspect. It passes, and it looks cheap.

       An interior is one continuous space, so its columns should nearly all
       have something in them and its wall should reach both edges. Returns
       (covered fraction of columns, worst edge coverage) -- low is bad, and
       low is what "floating props" measures as."""
    h = a.shape[0]
    band = a[int(h*0.25):, :, 3] > 24          # ignore the empty air at the top
    cols = band.any(axis=0).mean()
    al = a[..., 3] > 24
    edge = min(al[:, 0].mean(), al[:, -1].mean())
    return float(cols), float(edge)


def checkerboard(a):
    """Did the generator paint the TRANSPARENCY CHECKER as artwork?

       Asked for a picture whose background is empty, a model will sometimes
       draw the thing that means "empty" in an image editor: a grey-and-white
       chequered board, in paint, opaque. No colour key touches it -- it is not
       the key colour, it is not enclosed, and it is not a slab of one tone --
       and it shipped as a chequered rectangle around the approach panel.

       Pale-and-neutral on its own does not identify it: the prison's breeze
       block is 33-38% pale neutral and the space station is off-white
       panelling, and both are correct. What identifies it is that a checker
       ALTERNATES. Measured across the map, tr2 alternated at 0.23 transitions
       per pale pixel and the next highest picture in the game was 0.05, with
       every prison panel at 0.0000. The line is at 0.12, in the middle of that
       gap.

       Returns (pale fraction, alternation rate)."""
    op = a[..., 3] > 40
    if op.sum() < 500:
        return 0.0, 0.0
    rgb = a[..., :3].astype(int)
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    pale = op & (sat < 0.12) & (mx > 140)
    frac = pale.sum() / float(op.sum())
    if frac < 0.20:
        return frac, 0.0
    lum = rgb.mean(axis=2)
    lo, hi = np.percentile(lum[pale], 20), np.percentile(lum[pale], 80)
    if hi - lo < 40:
        return frac, 0.0
    b = (lum > (lo + hi) / 2).astype(np.int8)
    tr = n = 0
    for y in range(0, a.shape[0], 3):
        xs = pale[y].nonzero()[0]
        if len(xs) < 40:
            continue
        seg = b[y, xs]
        tr += int((seg[1:] != seg[:-1]).sum()); n += len(seg)
    return frac, tr / float(max(1, n))


def sliced(a):
    """How tall the content is in its own outermost columns -- see SLICED."""
    al = a[..., 3] > 24
    cols = al.any(axis=0)
    if not cols.any():
        return 0.0
    xs = cols.nonzero()[0]
    return max(al[:, int(xs.min())].sum(), al[:, int(xs.max())].sum()) / float(a.shape[0])


def edge_contact(a):
    """How much of the left and right edge columns has content on it."""
    h = a.shape[0]
    left = (a[:, 0, 3] > 24).sum() / float(h)
    right = (a[:, -1, 3] > 24).sum() / float(h)
    return max(left, right)


# How much of its own width the game ramps at draw time. Must match
# MID_OVERLAP in index.html; the two are a pair.
MID_OVERLAP = 0.07


def ramp_bite(a):
    """Does the draw-time ramp land on a real object, or on empty margin?

       This replaces a check that asked the OPPOSITE question. HARD EDGE used to
       flag any panel that went from nothing to solid in a pixel or two, because
       panels BUTTED and a picture that stopped dead met the next one at a hard
       line. The cutter therefore baked a fade into each end.

       The game now overlaps panels and ramps each left edge as it draws, so
       nothing butts anything and the baked fade became a SECOND ramp on top of
       the first. Where the two met, both were half transparent and a quarter of
       the sky came through solid objects -- a chicken coop and a tree you could
       see the hills through. So the fade is gone, and the fault worth checking
       is the one that caused: content sitting inside the 7% the game ramps,
       which gets eaten instead of empty margin.

       Full-bleed pictures are exempt: their content reaches the edge on
       purpose, and the ramp dissolving it onto the panel behind is the whole
       mechanism. Returns how far in the content starts, as a fraction."""
    al = a[..., 3]
    cols = (al > 24).any(axis=0)
    if not cols.any():
        return 1.0
    xs = cols.nonzero()[0]
    w = float(a.shape[1])
    return min(int(xs.min()), int(w - 1 - xs.max())) / w


def ground_rule(a):
    """The darkest full-width row in the bottom third, relative to the picture."""
    h, w = a.shape[:2]
    lum, worst = [], 0.0
    for y in range(h):
        row = a[y, ::4]
        op = row[row[..., 3] > 120]
        lum.append(op[..., :3].mean() if len(op) else None)
    body = [l for l in lum if l is not None]
    if not body:
        return 0.0
    med = float(np.median(body))
    for y in range(int(h * 0.66), h):
        row = a[y, ::4]
        op = row[row[..., 3] > 120]
        if len(op) > len(row) * 0.9 and lum[y] is not None and lum[y] < med * 0.55:
            worst = max(worst, 1 - lum[y] / med)
    return worst


def bands(a, gap=14):
    rows = (a[..., 3] > 24).sum(axis=1)
    out, start, empty = [], None, 0
    for y, n in enumerate(rows):
        if n > 0:
            if start is None:
                start = y
            empty = 0
        else:
            if start is not None:
                empty += 1
                if empty >= gap:
                    out.append((start, y - empty)); start = None
    if start is not None:
        out.append((start, len(rows) - 1))
    return [b for b in out if b[1] - b[0] > max(8, a.shape[0] * 0.12)]


def seam(a):
    """RMSE between the first and last columns, on the opaque part."""
    l, r = a[:, 0, :], a[:, -1, :]
    op = (l[:, 3] > 24) | (r[:, 3] > 24)
    if not op.any():
        return 0.0
    return float(np.sqrt(((l[op][:, :3].astype(float) - r[op][:, :3]) ** 2).mean()))


def main():
    show_all = '--all' in sys.argv
    files = sorted(glob.glob(os.path.join(ROOT, 'art', 'bg', '*.webp')) +
                   glob.glob(os.path.join(ROOT, 'art', 'panels', '*', '*.webp')) +
                   [f for w in ('ant', 'deep', 'lab')
                    for f in glob.glob(os.path.join(ROOT, 'art', w, '*.webp'))
                    if os.path.basename(f).split('.')[0].rstrip('23')
                       in ('far', 'mid', 'near', 'hang')])
    rows = []
    for f in files:
        rel = os.path.relpath(f, ROOT).replace('\\', '/')
        name = os.path.basename(f).split('.')[0]
        # A TILE IS ANYTHING REPEATED AGAINST ITSELF, which is every slot of the
        # three original worlds plus every floor and ceiling -- those are MEANT
        # to reach both edges, and flagging them as cut-outs is the audit being
        # wrong rather than the art. Only the numbered panels are placed beside
        # a different picture.
        is_tile = (name.rstrip('23') in ('near', 'hang', 'far', 'mid')
                   or rel.startswith('art/ant/') or rel.startswith('art/deep/')
                   or rel.startswith('art/lab/'))
        a = np.asarray(Image.open(f).convert('RGBA'))
        faults = []

        # An interior panel is judged by the OPPOSITE rules to a farm panel: it
        # is supposed to reach both edges, because the wall runs on into its
        # neighbour, and it is supposed to fill its frame. Testing it for empty
        # margins and a soft fade is testing it for being the thing that made
        # the map look cheap.
        # An OUTDOOR panel is full-bleed too, and judged more loosely: a desert
        # at night legitimately has empty sky above the dunes, so it is not
        # asked to fill its frame -- only to carry its GROUND to both edges, so
        # the interior wall it sits beside does not open onto a hole.
        if not is_tile and name in OUTDOORS:
            _, edge = wall_cover(a)
            if edge < 0.12:
                faults.append('GROUND STOPS the land covers %d%% of an edge column, so the '
                              'panel beside it opens onto sky' % (edge*100))
        elif not is_tile and name in INTERIORS:
            cov, edge = wall_cover(a)
            if cov < 0.90:
                faults.append('VOID only %d%% of the columns have anything in them; this '
                              'reads as props floating apart, not a place' % (cov*100))
            if edge < 0.35:
                faults.append('WALL STOPS the wall covers %d%% of an edge column, so it '
                              'ends instead of running into the next panel' % (edge*100))
        elif not is_tile and sliced(a) > 0.30:
            faults.append('SLICED the outermost column is %d%% of the picture tall; '
                          'something is cut off with a straight vertical line'
                          % (sliced(a)*100))
        elif not is_tile and edge_contact(a) > 0.10:
            faults.append('CUTOUT EDGE %d%% of an edge column has content' % (edge_contact(a)*100))
        if not is_tile and name not in INTERIORS and name not in OUTDOORS:
            b = ramp_bite(a)
            if b < MID_OVERLAP:
                faults.append('RAMP BITE content starts %.1f%% in, inside the %.0f%% the '
                              'game ramps; the ramp will fade a real object'
                              % (b*100, MID_OVERLAP*100))
        # Only a PANEL can have a false ground rule. A floor tile's bottom IS
        # the ground line -- it sits on the road, which is drawn over it -- so a
        # dark horizontal band down there is the edge of the plating or the foot
        # of the bank, and flagging it is the audit not knowing what it is
        # looking at. Checked and confirmed on cia/near: a cable tray and a
        # floor plate, exactly as drawn.
        # An INTERIOR is exempt for the same reason a tile is. The check exists
        # to catch the solid dark bar the generator paints UNDER a row of
        # objects, which makes a panel read as pasted onto the sky. An interior
        # has no "under": it fills its frame to the bottom edge, so its lowest
        # rows are floor, skirting and dado -- checked on p2, where the 54% bar
        # it flagged is a wooden skirting board in a guard station that is
        # otherwise the best panel in the world.
        g = 0.0 if (is_tile or name in INTERIORS or name in OUTDOORS) else ground_rule(a)
        if g > 0.30:
            faults.append('GROUND RULE a dark bar %d%% under the picture' % (g*100))
        pale, alt = checkerboard(a)
        if alt > 0.12:
            faults.append('CHECKERBOARD the scene is painted on a transparency checker '
                          '(%d%% pale, alternating %.2f)' % (pale*100, alt))
        hz = hazard_px(a)
        opq = max(1, int((a[..., 3] > 40).sum()))
        if hz / float(opq) > 0.0015:
            faults.append('HAZARD HUE %.1f%% of the picture is in the wire colour (~%d px)'
                          % (100.0 * hz / opq, hz))
        if not is_tile and len(bands(a)) > 1:
            faults.append('STACKED ROWS %d bands' % len(bands(a)))
        if name.startswith('near') and a.shape[0] < 140:
            faults.append('THIN FLOOR only %dpx tall; it gets magnified' % a.shape[0])
        siblings = len(glob.glob(os.path.join(os.path.dirname(f), name.rstrip('23') + '*.webp')))
        if is_tile and name.rstrip('23') in ('near', 'hang') and siblings < 2:
            sm = seam(a)
            if sm > 60:
                faults.append('OPEN SEAM edges differ by %.0f' % sm)
        if not is_tile:
            asp = a.shape[1] / float(a.shape[0])
            if abs(asp - REF_ASPECT) > 0.6:
                faults.append('ASPECT %.2f against the reference %.2f' % (asp, REF_ASPECT))
        rows.append((len(faults), rel, faults))

    rows.sort(key=lambda r: -r[0])
    bad = [r for r in rows if r[0]]
    for n, rel, faults in (rows if show_all else bad):
        print('%-34s %s' % (rel, '; '.join(faults) if faults else 'ok'))
    print('\n%d pictures checked, %d with something to answer for.' % (len(rows), len(bad)))


if __name__ == '__main__':
    main()
