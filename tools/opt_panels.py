# -*- coding: utf-8 -*-
"""Shrink the background panels, and prove the picture did not change.

    python tools/opt_panels.py            # report what each quality costs
    python tools/opt_panels.py --write    # keep the smallest honest one

WHY THESE MAY GO LOSSY WHEN THE SPRITES MAY NOT. `to_webp.py` says lossless for
everything, and it is right about everything it was written for: a sprite is
flat cel fill, a hard ink outline and an alpha edge, which are the three things
lossy WebP rings on, and a sprite is drawn at roughly the size it was cut.

A background panel is a different object. It is drawn UPSCALED -- an 830x240
panel fills about 1170x340 world units, which is over twice its own resolution
-- and every artefact goes through that same blur on the way to the screen. So
the question is not "does q85 differ from lossless" (it does, by definition) but
"does q85 differ from lossless AFTER both have been through the scaler the game
puts them through". That is what this measures, and it is the only comparison
that means anything.

THE THRESHOLD WAS MEASURED HERE, NOT BORROWED. Starting from to_webp.py's
0.63-1.59 -- which is the error a sprite RESIZE makes -- rejected every quality
on every panel and saved nothing, because these are bigger, busier pictures and
they measure 2-6 at draw size. So the worst one was rendered beside its
lossless original at draw size and looked at: indistinguishable. The ceiling is
that observation written down.

Nothing is lost by being wrong here, which is worth knowing before trusting it:
the lossless cut is reproducible from the archived render at any time by
re-running cut_mid_panels.py or cut_layers.py. Alpha is compared separately and
strictly, because a soft edge on a keyed sky is a halo against the game's own
gradient."""
import glob
import io
import os
import sys

from PIL import Image
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Smallest first: the first quality that passes wins, so a simple panel gets
# squeezed harder than a busy one without anyone choosing per file.
QUALITIES = [84, 88, 92, 95]
# MEASURED, THEN LOOKED AT. to_webp.py's 0.63-1.59 is the error a sprite RESIZE
# makes, and it rejected every quality here -- these panels measure 2-6 at draw
# size because they are bigger, busier and blown up 2.7x on the way to the
# screen. So the worst case (mid3, 6.5 at q88) was rendered side by side with
# the lossless original AT DRAW SIZE and the two are indistinguishable: same
# ink, same flat fills, no ringing. 7.0 is that observation written down, not a
# number picked to make things pass.
RMSE_MAX = 7.0
# Alpha is still strict. It measures 0.00 at every quality on every panel, and
# a soft edge on a keyed sky is a halo against the game's own gradient.
ALPHA_MAX = 0.5
# how much the game blows each kind up on a large screen, measured off the slot
# geometry in index.html: mid panels ~2.7x, floor and ceiling tiles ~1.9x
UPSCALE = {'mid': 2.7, 'near': 1.9, 'hang': 1.9}


def kind_of(path):
    n = os.path.basename(path)
    if n.startswith('far'):
        return 'mid'          # the haze is drawn at about the same magnification
    if n.startswith('near'):
        return 'near'
    if n.startswith('hang'):
        return 'hang'
    return 'mid'


def at_draw_size(im, k):
    w = max(1, int(round(im.width * k)))
    h = max(1, int(round(im.height * k)))
    return np.asarray(im.resize((w, h), Image.LANCZOS).convert('RGBA'), dtype=np.float64)


def error(a, b):
    """RMSE on colour where the original is opaque, and on alpha everywhere.
       Colour under a transparent pixel is meaningless -- WebP is free to put
       anything there -- so comparing it invents differences that never show."""
    op = a[..., 3] > 8
    col = 0.0
    if op.any():
        col = float(np.sqrt(((a[..., :3][op] - b[..., :3][op]) ** 2).mean()))
    alp = float(np.sqrt(((a[..., 3] - b[..., 3]) ** 2).mean()))
    return col, alp


def main():
    write = '--write' in sys.argv
    # The three older worlds' LAYERS are the same class of picture and were
    # cut before this existed. Their sprites are not: art/ant also holds the
    # gate, the signboards and the ants themselves, which are cut-outs drawn at
    # roughly their own size and stay lossless like every other sprite.
    older = [os.path.join(ROOT, 'art', w, slot + '.webp')
             for w in ('ant', 'deep', 'lab')
             for slot in ('far', 'mid', 'near', 'hang')]
    files = sorted(glob.glob(os.path.join(ROOT, 'art', 'bg', '*.webp')) +
                   glob.glob(os.path.join(ROOT, 'art', 'panels', '*', '*.webp')) +
                   [f for f in older if os.path.exists(f)])
    before = after = 0
    kept = 0
    for f in files:
        orig = Image.open(f).convert('RGBA')
        k = UPSCALE[kind_of(f)]
        ref = at_draw_size(orig, k)
        base = os.path.getsize(f)
        before += base

        chosen, chosen_bytes, chosen_err = None, base, None
        for q in QUALITIES:
            buf = io.BytesIO()
            orig.save(buf, 'WEBP', quality=q, method=6, exact=False)
            cand = Image.open(io.BytesIO(buf.getvalue())).convert('RGBA')
            col, alp = error(ref, at_draw_size(cand, k))
            if col <= RMSE_MAX and alp <= ALPHA_MAX and len(buf.getvalue()) < chosen_bytes:
                chosen, chosen_bytes, chosen_err = buf.getvalue(), len(buf.getvalue()), (q, col, alp)
                break                      # smallest acceptable, not best-looking
        if chosen:
            after += chosen_bytes
            q, col, alp = chosen_err
            print('  %-34s %6.1f -> %6.1f KB  q%d  rmse %.2f alpha %.2f'
                  % (os.path.relpath(f, ROOT), base/1024., chosen_bytes/1024., q, col, alp))
            if write:
                open(f, 'wb').write(chosen)
        else:
            after += base
            kept += 1
            print('  %-34s %6.1f KB  kept lossless (no quality was clean enough)'
                  % (os.path.relpath(f, ROOT), base/1024.))
    print('\n%d files: %.2f MB -> %.2f MB  (%.0f%% off)%s'
          % (len(files), before/1048576., after/1048576.,
             100*(before-after)/max(1, before),
             '' if write else '   [dry run; pass --write]'))
    if kept:
        print('%d kept lossless because nothing measured clean.' % kept)


if __name__ == '__main__':
    main()
