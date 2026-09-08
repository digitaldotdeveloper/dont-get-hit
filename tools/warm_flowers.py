# -*- coding: utf-8 -*-
"""Take the blue out of the scenery, because blue means DEATH in this game.

    python tools/warm_flowers.py            # report what is blue, change nothing
    python tools/warm_flowers.py --write    # recolour it

Every hazard here is a cyan wire. So a blue thing painted into the background
is not a decoration, it is a false positive the player has to learn to ignore --
and the first kilometre had a knot of BLUEBELLS painted into the grass at both
ends of `art/bg/near.webp`. That tile is about half a screen wide, so those two
knots came round every half screen forever: little blue shapes at the edge of
every repeat, in the one colour that otherwise only ever means "do not touch".

THE FLOWERS ARE KEPT, NOT DELETED. Cutting them out would leave a hole in a
painted tile and need inpainting; recolouring them needs nothing, because a
flower is the right thing to have in the grass -- it is only the hue that was
wrong. Each blue pixel is remapped onto a warm ramp BY ITS OWN LUMINANCE, so
the petal keeps its shading and its ink outline (which is not blue and is
therefore never touched) still fits it exactly.

The same test finds the glowing cyan mushrooms in the underground layers. They
are left alone by default and listed by `--all`: down there the wire is cyan
too, but the mushrooms are the only light in an amber cave and the call is a
design one rather than a bug -- see the note at the bottom of this file."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image                                        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FARM = ['art/bg/near.webp']
UNDER = ['art/ant/near.webp', 'art/deep/near.webp', 'art/lab/near.webp',
         'art/ant/hang.webp', 'art/deep/hang.webp', 'art/lab/hang.webp']

# Warm ramp, dark -> light, sampled off the game's own gold and cream so the
# flowers land in a palette the map already contains.
RAMP = [(0.00, (140, 96, 30)), (0.45, (222, 168, 52)), (0.75, (247, 214, 118)),
        (1.00, (255, 244, 214))]


def is_blue(r, g, b, a):
    return a > 40 and b > 110 and b > r + 45 and b > g + 30


def warm(r, g, b):
    """Same pixel, warm hue. Luminance is what carries the drawing, so that is
       the thing that has to survive; the hue is what was wrong."""
    L = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    for i in range(len(RAMP) - 1):
        t0, c0 = RAMP[i]
        t1, c1 = RAMP[i + 1]
        if L <= t1 or i == len(RAMP) - 2:
            k = 0 if t1 == t0 else max(0.0, min(1.0, (L - t0) / (t1 - t0)))
            return tuple(int(round(c0[j] + (c1[j] - c0[j]) * k)) for j in range(3))
    return (r, g, b)


def do(rel, write):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print('%-24s (not here)' % rel)
        return
    im = Image.open(p).convert('RGBA')
    px = im.load()
    W, H = im.size
    n = 0
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if not is_blue(r, g, b, a):
                continue
            n += 1
            if write:
                nr, ng, nb = warm(r, g, b)
                px[x, y] = (nr, ng, nb, a)
    print('%-24s %5d blue px of %d  %s' % (rel, n, W * H,
                                           'RECOLOURED' if (write and n) else ''))
    if write and n:
        # lossless, like every other sprite here: these are flat cel fills with
        # ink outlines and an alpha edge, which is everything lossy rings on
        im.save(p, 'WEBP', lossless=True, quality=100, method=6)



# ---------------------------------------------------------------- the clouds
# Not blue by the test above -- they are near-white -- but they are CEL-SHADED
# with a cool grey, and a cool grey on a gold sky reads lilac. They are also
# the biggest thing in the sky after the sky. So the cast is rotated warm and
# nothing else about them changes: same shapes, same alpha, same shading, just
# no longer a cold light on a warm day.
CLOUDS = ['art/cloud%d.webp' % i for i in range(5)]


def warm_clouds(write):
    for rel in CLOUDS:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert('RGBA')
        px = im.load()
        W, H = im.size
        for y in range(H):
            for x in range(W):
                r, g, b, a = px[x, y]
                if a < 8:
                    continue
                if write:
                    px[x, y] = (min(255, int(r * 1.00)),
                                min(255, int(g * 0.985)),
                                min(255, int(b * 0.945)), a)
        if write:
            im.save(p, 'WEBP', lossless=True, quality=100, method=6)
        print('%-24s %s' % (rel, 'WARMED' if write else '(would warm)'))


# ------------------------------------------------------------- the mushrooms
# The cave's glowing mushrooms were CYAN -- the exact hue of a live wire, and
# not caught by is_blue() above because cyan carries as much green as blue.
# Underground the wires are cyan too, so this is the same fault as the
# bluebells and worse: down there the only two glowing things in the frame
# were the thing that kills you and a plant.
#
# They keep their job. A cave wants a light source that is not a lantern, so
# they go to the lanterns' own amber rather than away from light altogether,
# mapped by luminance so the glow and the ink outline still fit.
MUSH = ['art/ant/near.webp', 'art/deep/near.webp']
# The lab set is lit in CYAN -- strip lamps, screens, glowing ports -- and it
# now stands in for four zones (the base, Area 51, the alien facility, space),
# so the hazard hue lights the whole back half of the game. The tanks' GREEN
# liquid is not cyan and is left alone; only the lighting moves, to the amber
# these places would actually be lit in. Originals are in git if the lab ever
# wants its cold light back.
LAB = ['art/lab/far.webp', 'art/lab/mid.webp', 'art/lab/near.webp', 'art/lab/hang.webp']
MUSH_RAMP = [(0.00, (122, 74, 22)), (0.45, (216, 154, 42)), (0.75, (245, 214, 138)),
             (1.00, (255, 240, 200))]


def is_cyan(r, g, b, a):
    return a > 40 and b > 90 and g > 90 and r < g - 30 and r < b - 30


def warm_mushrooms(write, files=None):
    for rel in (files or MUSH):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert('RGBA')
        px = im.load()
        W, H = im.size
        n = 0
        for y in range(H):
            for x in range(W):
                r, g, b, a = px[x, y]
                if not is_cyan(r, g, b, a):
                    continue
                n += 1
                if write:
                    L = (0.299*r + 0.587*g + 0.114*b) / 255.0
                    for i in range(len(MUSH_RAMP) - 1):
                        t0, c0 = MUSH_RAMP[i]
                        t1, c1 = MUSH_RAMP[i + 1]
                        if L <= t1 or i == len(MUSH_RAMP) - 2:
                            k = 0 if t1 == t0 else max(0.0, min(1.0, (L - t0)/(t1 - t0)))
                            px[x, y] = (int(round(c0[0] + (c1[0]-c0[0])*k)),
                                        int(round(c0[1] + (c1[1]-c0[1])*k)),
                                        int(round(c0[2] + (c1[2]-c0[2])*k)), a)
                            break
        if write and n:
            im.save(p, 'WEBP', lossless=True, quality=100, method=6)
        print('%-24s %5d cyan px %s' % (rel, n, 'RECOLOURED' if (write and n) else ''))


# ------------------------------------------------------- the last few pixels
# The two tests above catch blue and cyan by channel arithmetic, which is what
# they were written for -- a bluebell, a glowing mushroom. What they miss is a
# handful of pixels sitting in the hazard's own HUE without tripping either
# rule: a window pane in the farmhouse, a rim on the silo. 181 of them across
# the whole background, which is nothing to look at and everything to a rule
# that is supposed to be absolute: blue means the thing that kills you.
#
# The wire's core is #4CCFFF, hue about 197 degrees. Anything from 165 to 265
# with real saturation competes with it; greens and greys do not, which is why
# this is measured in HUE and not in channels -- a channel test flags the hills.
import colorsys

# Every background panel, wherever it lives. Enumerated rather than listed by
# hand: 42 panels across nine worlds is past the point where a hand-kept list
# stays true, and the whole value of this pass is that it is exhaustive.
import glob as _glob
HUE_FILES = sorted([os.path.relpath(f, ROOT) for f in
                    _glob.glob(os.path.join(ROOT, 'art', 'bg', '*.webp')) +
                    _glob.glob(os.path.join(ROOT, 'art', 'panels', '*', '*.webp'))])


def hazard_hue(r, g, b):
    h, sat, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    return 165 <= h*360 <= 265 and sat > 0.25 and v > 0.25


def dehue(write):
    for rel in HUE_FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert('RGBA')
        px = im.load()
        n = 0
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a < 40 or not hazard_hue(r, g, b):
                    continue
                n += 1
                if write:
                    # keep the pixel's lightness, take its hue to warm grey --
                    # a window stays a window, it just stops being blue
                    h, sat, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                    nr, ng, nb = colorsys.hsv_to_rgb(0.09, sat*0.45, v)
                    px[x, y] = (int(nr*255), int(ng*255), int(nb*255), a)
        if write and n:
            im.save(p, 'WEBP', lossless=True, quality=100, method=6)
        print('%-24s %4d px in the hazard hue %s' % (rel, n, 'WARMED' if (write and n) else ''))


if __name__ == '__main__':
    write = '--write' in sys.argv
    files = FARM + (UNDER if '--all' in sys.argv else [])
    for f in files:
        do(f, write and (f in FARM or '--all' in sys.argv))
    if '--clouds' in sys.argv:
        warm_clouds(write)
    if '--mushrooms' in sys.argv:
        warm_mushrooms(write)
    if '--lab' in sys.argv:
        warm_mushrooms(write, LAB)
    if '--hue' in sys.argv:
        dehue(write)
    if not write:
        print('\nnothing written; pass --write')

# The underground question, written down so it gets decided rather than drifted
# into: the cyan mushrooms in art/ant/near.webp are the same hue as a live wire,
# which is the same fault as the bluebells -- but they are also the only cool
# light in an amber cavern, and the ant world was designed around them. If they
# go, they should go WARM-GREEN rather than gold, or the near bank loses its
# only accent. Run with --all --write to do it and look before keeping it.
