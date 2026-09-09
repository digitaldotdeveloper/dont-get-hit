# -*- coding: utf-8 -*-
"""Cut the mid-layer panels to the frame the slot expects.

    python tools/cut_mid_panels.py --list        # what came back
    python tools/cut_mid_panels.py               # cut every panel that exists
    python tools/cut_mid_panels.py mid2          # just one

THE FRAME IS NOT NEGOTIABLE, because the slot places every panel with one
number. `art/bg/mid.webp` is 830x240 and the game anchors it by its BOTTOM
EDGE at a height derived from GROUND, so a panel that is a different shape is a
panel at a different scale with its ground line in the wrong place -- which
shows up as the middle distance stepping up and down as you run. So every panel
comes out of here at exactly the reference's pixel size, with its content
standing on the bottom edge.

WHAT IS MEASURED RATHER THAN ASSUMED:

  * THE GROUND LINE. The generator draws the row a little above the bottom edge
    as often as not. The content's own bounding box is found after keying and
    slid down so it sits ON the bottom edge -- no gap, no crop.
  * THE SCALE. The prompt asks for "a barn about two thirds of the height" and
    the model obliges to within about 30%. Scaling by the content's HEIGHT
    would make a panel of low sheds as tall as a panel with a silo in it, so
    the scale comes off the TALLEST STRUCTURE against the reference's own
    tallest structure -- which is what "the same distance away" actually means.
  * THE MARGINS. Content is centred in the frame, and anything past the edge is
    a panel that will butt into its neighbour, so it is scaled to fit rather
    than cropped.

A panel that comes back with its subject touching an edge, or with a painted
sky the key could not remove, is reported and skipped: the next stage measures,
it does not hope."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image                                       # noqa: E402
import numpy as np                                          # noqa: E402
from gen_mid_panels import PANELS                           # noqa: E402

# Phrases from earlier wordings, so a re-prompt never orphans what came back.
EXTRA_NEEDLES = {
    'tr4': ['A great bank of packed red-brown earth filling most of the picture'],
}

LIB = r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard\library"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, 'art', 'bg')

# Where each panel belongs. The farm's and the approach's live beside the
# painting they were matched to; every other world keeps its own folder, so a
# zone's art can be looked at, replaced or deleted as a set.
def dest_dir(name):
    from gen_mid_panels import WORLDS
    for world, panels in WORLDS.items():
        if name in panels:
            d = os.path.join(ROOT, 'art', 'panels', world)
            os.makedirs(d, exist_ok=True)
            return d
    return BG
REF = os.path.join(BG, 'mid.webp')
# the share of the frame a panel's content may occupy, leaving 4% clear
# on each side so no two panels ever butt content against content
MARGIN_FIT = 0.92


def key_magenta(im):
    """Magenta out, and pull the purple fringe off whatever it touched."""
    a = np.array(im.convert('RGBA')).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (r > 150) & (b > 150) & (g < 110) & ((r - g) > 60) & ((b - g) > 60)
    a[mag, 3] = 0
    # half-keyed edge pixels read as a purple rim against a warm sky
    rim = (a[..., 3] > 0) & (r > g + 40) & (b > g + 40)
    a[rim, 0] = np.minimum(a[rim, 0], a[rim, 1] + 40)
    a[rim, 2] = np.minimum(a[rim, 2], a[rim, 1] + 40)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def key_by_flood(im, tol=42):
    """Key the background by GROWING IN FROM THE BORDER, not by naming a colour.

       The colour test wants magenta near #FF00FF. Sometimes the generator
       returns a washed-out pink instead -- 162,134,164 on the alien machinery
       panel, which is 79% of the picture and sails straight past a test that
       needs green under 110. Loosening that test is not the answer: the alien
       facility and space were given MAGENTA accents on purpose, and a looser
       colour key would eat them out of the artwork.

       So this floods from the edge, the way npc_frames.py keys a character who
       is wearing the key colour: whatever is connected to the border and close
       to the border's own colour is background, and anything enclosed by an ink
       outline cannot be reached however magenta it is."""
    a = np.asarray(im.convert('RGBA')).astype(np.int16).copy()
    h, w = a.shape[:2]
    seed = np.concatenate([a[0, :, :3], a[-1, :, :3], a[:, 0, :3], a[:, -1, :3]])
    base = np.median(seed, axis=0)
    close = (np.abs(a[..., :3] - base).sum(axis=2) < tol)

    out = np.zeros((h, w), bool)
    stack = [(0, x) for x in range(w) if close[0, x]] +             [(h-1, x) for x in range(w) if close[h-1, x]] +             [(y, 0) for y in range(h) if close[y, 0]] +             [(y, w-1) for y in range(h) if close[y, w-1]]
    for y, x in stack:
        out[y, x] = True
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1,0), (-1,0), (0,1), (0,-1)):
            ny, nx = y+dy, x+dx
            if 0 <= ny < h and 0 <= nx < w and not out[ny, nx] and close[ny, nx]:
                out[ny, nx] = True
                stack.append((ny, nx))
    a[out, 3] = 0
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def key_panel(path):
    """The colour key, with the flood as a fallback when it plainly failed."""
    im = key_magenta(Image.open(path))
    a = np.asarray(im)
    op = a[..., 3] > 40
    if op.sum():
        r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
        # The TRIGGER is looser than the key on purpose. It is not deciding what
        # to erase -- the flood decides that -- it is only answering "did the
        # colour key plainly fail here". The alien panel came back at 162,134,164
        # and fired; the docking bay came back paler still, sailed under a
        # stricter test, and shipped 78% background as a pink slab behind the
        # shuttle. A trigger that misses is worse than a trigger that fires
        # once too often, because the flood is harmless on a picture that was
        # already keyed properly.
        left = op & (r > 110) & (b > 110) & (g < r - 18) & (g < b - 18)
        if left.sum() > op.sum() * 0.25:
            return key_by_flood(Image.open(path))
    return im


def content_box(im):
    al = np.array(im)[..., 3] > 24
    if not al.any():
        return None
    ys, xs = np.where(al)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def tallest_run(im):
    """Height of the tallest opaque column: 'how big is the biggest building'.
       Column-wise rather than by bounding box, because one stray cloud the key
       missed would otherwise set the scale for the whole panel."""
    al = np.array(im)[..., 3] > 24
    cols = al.sum(axis=0)
    if not cols.any():
        return 1
    return int(np.percentile(cols[cols > 0], 99))


def strip_baseline(im):
    """Cut the ground rule the generator paints under the row, and its spatter.

       Asked for "one straight ground line along the bottom edge", the model
       often draws it LITERALLY: a solid bar across the full width. In a picture
       that stands on its own that is a nice touch. Placed in the game it is the
       edge of a rectangle -- the panel stops reading as part of the farm and
       starts reading as a cut-out pasted onto it, which is exactly what "this
       house in the background is cutout" was.

       Two things had to be measured rather than assumed, and each cost a pass:

       THE BAR IS NOT ALWAYS THE LAST THING IN THE PICTURE. The transition
       panels spatter loose soil BELOW their rule, so walking up from the bottom
       and stopping at the first row with anything in it never reaches it.

       AND THE BAR IS NOT BLACK. It is dark BROWN -- mean 29,12,10 on one panel,
       69,34,26 on another -- so an absolute threshold either misses it or eats
       a barn. What is reliable is that it is much darker than the picture it
       sits under, so the test is RELATIVE: a full-width row at less than 55% of
       the panel's own median brightness. Nothing else in these pictures is both
       full-width and that dark."""
    a = np.array(im)
    h, w = a.shape[:2]
    lum, opq = [], []
    for y in range(h):
        row = a[y, ::4]
        op = row[row[..., 3] > 120]
        opq.append(len(op)/float(len(row)))
        lum.append(op[..., :3].mean() if len(op) else 255.0)
    body = [l for l, o in zip(lum, opq) if o > 0.25]
    if not body:
        return im
    med = float(np.median(body))
    cut = None
    for y in range(h - 1, int(h*0.60), -1):
        if opq[y] > 0.90 and lum[y] < med*0.55:
            cut = y
        elif cut is not None and opq[y] > 0.90 and lum[y] < med*0.75:
            cut = y                      # the rule fades into the art above it
        elif cut is not None:
            break
    return im.crop((0, 0, w, cut)) if cut else im


# How much of a panel's own width fades out at each end. 7% of 830 is about
# 58px, which at the size a panel is drawn is a soft edge rather than a visible
# gap.
EDGE_FADE = 0.07


def fade_edges(im):
    """Ramp the alpha out at the left and right ends of the content.

       22 of the panels END MID-OBJECT: a mound, a wall of cells, a rack of
       servers that runs the width of the picture and stops dead, because that
       is what the generator drew and no crop can invent what is past the edge.
       Butted against the next panel that is a hard vertical join -- the thing
       reported as "the background walls suddenly appear".

       Re-rendering 22 pictures would not reliably fix it either: a corridor has
       walls, and a wall that reaches the edge is what a corridor looks like.

       So the panels dissolve into each other instead, which is what the ORIGINAL
       painted farm panels did -- loadPanels has laid them overlapping with an
       alpha ramp down one edge since long before any of this. A wall that fades
       over its last 7% reads as distance; a wall that stops on a pixel column
       reads as a mistake."""
    a = np.asarray(im).astype(np.float32).copy()
    h, w = a.shape[:2]
    al = a[..., 3] > 24
    cols = al.any(axis=0)
    if not cols.any():
        return im
    xs = cols.nonzero()[0]
    x0, x1 = int(xs.min()), int(xs.max())
    n = max(4, int((x1 - x0)*EDGE_FADE))
    ramp = np.ones(w, np.float32)
    for i in range(n):
        t = (i + 0.5)/n
        t = t*t*(3 - 2*t)                     # smoothstep, so the fade has no visible start
        if x0 + i < w:
            ramp[x0 + i] = min(ramp[x0 + i], t)
        if x1 - i >= 0:
            ramp[x1 - i] = min(ramp[x1 - i], t)
    a[..., 3] *= ramp[None, :]
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def trim_clipped(im, gap=6, max_bite=0.25):
    """Drop objects the generator drew running off its own edge.

       The prompt asks for empty margins and the cutter leaves 4% clear, and a
       half barn door STILL turns up butted against the next panel -- because
       the margin is around the CONTENT, and the content itself ends in half a
       chamber that the generator cut with its own frame. A panel that ends
       mid-object cannot sit beside anything.

       So: walk in from each edge to the first real GAP -- a run of empty
       columns -- and cut there, discarding whatever partial thing was outside
       it. Bounded, because some panels are legitimately continuous (a wall, an
       earth bank), and eating a quarter of one of those would be worse than
       the seam it fixes; past that limit the panel is left alone."""
    a = np.array(im)
    h, w = a.shape[:2]
    col = (a[..., 3] > 24).any(axis=0)
    if not col.any():
        return im

    def first_gap(rng):
        run = 0
        for x in rng:
            if not col[x]:
                run += 1
                if run >= gap:
                    return x
            else:
                run = 0
        return None

    left = first_gap(range(0, int(w*max_bite))) if col[0] else 0
    right = first_gap(range(w - 1, int(w*(1 - max_bite)), -1)) if col[w - 1] else w - 1
    if left is None or right is None or right - left < w*0.5:
        return im
    return im.crop((left, 0, right + 1, h))


def row_bands(im, gap=14):
    """The horizontal bands of content, top to bottom.

       A panel is ONE row standing on ONE ground line. The generator does not
       always agree: asked for a machinery yard it drew a combine and a barn,
       then a SECOND row underneath with the plough and the workshop. Squeezed
       into an 830x240 frame that comes out at half scale with a row of
       buildings floating in the sky, which is not something a later stage can
       fix -- so it is caught here and the panel is refused.

       Measured off the alpha profile: rows of the image with nothing in them
       separate one band from the next."""
    al = np.array(im)[..., 3] > 24
    rows = al.sum(axis=1)
    bands, start = [], None
    empty = 0
    for y, n in enumerate(rows):
        if n > 0:
            if start is None:
                start = y
            empty = 0
        else:
            if start is not None:
                empty += 1
                if empty >= gap:
                    bands.append((start, y - empty))
                    start = None
    if start is not None:
        bands.append((start, len(rows) - 1))
    return [b for b in bands if b[1] - b[0] > 8]


def is_row(im, band, main):
    """Is this band a ROW of buildings, or a speck the generator left behind?

       A row spans the picture; a speck is a mark in a corner. Height alone
       cannot tell them apart -- a low row of troughs is short too -- so the
       test is how much of the WIDTH the band actually covers, with the tallest
       band always counting as a row."""
    if band is main:
        return True
    al = np.array(im)[band[0]:band[1] + 1, :, 3] > 24
    if not al.any():
        return False
    cols = al.any(axis=0)
    span = (cols.nonzero()[0].max() - cols.nonzero()[0].min() + 1) / float(im.width)
    tall = (band[1] - band[0]) / float(max(1, main[1] - main[0]))
    return span > 0.35 and tall > 0.20


def candidates_for(table):
    """Newest-first renders per name, for any prompt table -- the panels here or
       the floor and ceiling tiles in cut_layers.py. One index walk, two callers,
       so the two cutters can never disagree about what exists."""
    try:
        idx = json.load(open(os.path.join(LIB, 'index.json'), encoding='utf-8'))
    except Exception:
        return {}
    out = {}
    for e in idx:
        pr = e.get('prompt') or ''
        for name, body in table.items():
            keys = [body[:48]] + EXTRA_NEEDLES.get(name, [])
            if any(k in pr for k in keys):
                p = os.path.join(LIB, e['file'].replace('/', os.sep))
                if os.path.exists(p):
                    out.setdefault(name, []).append((e.get('createdAt', 0), p))
    for k in out:
        out[k].sort(reverse=True)
        out[k] = [p for _, p in out[k]]
    return out


def candidates():
    return candidates_for(PANELS)


def main():
    ref = Image.open(REF).convert('RGBA')
    W, H = ref.size
    ref_tall = tallest_run(ref)
    cands = candidates()

    if '--list' in sys.argv:
        print('reference %s is %dx%d, tallest structure %dpx' % (
            os.path.basename(REF), W, H, ref_tall))
        for name in PANELS:
            v = cands.get(name, [])
            print('  %-6s %d take(s)%s' % (name, len(v), '' if v else '   <-- nothing back'))
        return

    want = [a for a in sys.argv[1:] if not a.startswith('--')] or list(PANELS)
    for name in want:
        src = (cands.get(name) or [None])[0]
        if not src:
            print('  %-6s no render yet -- skipped' % name)
            continue
        im = trim_clipped(strip_baseline(key_panel(src)))
        box = content_box(im)
        if not box:
            print('  %-6s nothing survived the key' % name)
            continue
        im = im.crop(box)

        # AND REFUSE A PANEL THAT IS STILL MOSTLY BACKGROUND. The docking bay came
        # back with the scene drawn on a PINK CARD inside the picture -- a
        # lighter magenta than the true background, so the colour key cannot
        # name it and the flood cannot reach it: it is enclosed, exactly like
        # artwork. Nothing downstream can fix that, and it shipped as a slab
        # behind the shuttle. A picture that is three quarters background is a
        # failed render, not a panel.
        chk = np.asarray(im)
        opq = chk[..., 3] > 40
        if opq.any():
            cr, cg, cb = chk[..., 0].astype(int), chk[..., 1].astype(int), chk[..., 2].astype(int)
            slab = opq & (cr > 110) & (cb > 110) & (cg < cr - 18) & (cg < cb - 18)
            if slab.sum() > opq.sum() * 0.25:
                print('  %-6s REFUSED: %.0f%% of it is still background -- the scene was '
                      'drawn on a coloured card. Re-render it.'
                      % (name, 100.0 * slab.sum() / opq.sum()))
                continue

        bands = row_bands(im)
        if len(bands) > 1:
            main = max(bands, key=lambda b: b[1] - b[0])
            rows, junk = [], []
            for b in bands:
                (rows if is_row(im, b, main) else junk).append(b)
            if len(rows) > 1:
                print('  %-6s REFUSED: the generator drew %d stacked rows (%s). A panel is '
                      'one row on one ground line -- re-prompt it.'
                      % (name, len(rows), ', '.join('%d-%d' % (b[0], b[1]) for b in rows)))
                continue
            if junk:
                # Not a row -- a speck. The dairy panel came back with a little
                # purple four-pointed sparkle in the corner, 20px wide, which is
                # both floating debris AND in the one hue this game reserves for
                # hazards. Erase it and keep the panel.
                a = np.array(im)
                for b in junk:
                    a[b[0]:b[1] + 1, :, 3] = 0
                im = Image.fromarray(a, 'RGBA')
                box2 = content_box(im)
                if box2:
                    im = im.crop(box2)
                print('  %-6s (cleared %d stray speck(s) off the panel)' % (name, len(junk)))

        # scale off the tallest structure, not the bounding box
        k = ref_tall / float(tallest_run(im))
        # ...but never let a panel overflow the frame it has to live in
        k = min(k, H / float(im.height), (W * 0.92) / float(im.width))
        # AND ALWAYS LEAVE A MARGIN. A panel is placed BESIDE other panels, so
        # anything touching its own edge meets whatever the next panel starts
        # with -- which is how half a barn door ends up butted against half an
        # egg shelf in the middle of a chamber. The prompt asks for empty
        # margins and the generator often draws right up to the edge anyway, so
        # the fit is enforced here rather than hoped for: at least 4% of the
        # frame clear on each side, which costs a little scale and buys a panel
        # that can sit next to anything.
        k = min(k, (W * MARGIN_FIT) / float(im.width))
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))),
                       Image.LANCZOS)

        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        out.alpha_composite(im, ((W - im.width) // 2, H - im.height))   # on the bottom edge
        out = fade_edges(out)
        dst = os.path.join(dest_dir(name), name + '.webp')
        out.save(dst, 'WEBP', lossless=True, quality=100, method=6)

        margin = (W - im.width) // 2
        print('  %-6s %4dx%-4d -> %dx%d  margins %dpx  %5.1f KB%s'
              % (name, box[2] - box[0], box[3] - box[1], W, H, margin,
                 os.path.getsize(dst) / 1024.0,
                 '   <-- TIGHT, it will butt its neighbour' if margin < 12 else ''))


if __name__ == '__main__':
    main()
