# -*- coding: utf-8 -*-
"""Bring the oversampled cut-out art down to the size it is actually drawn.

    python tools/shrink_art.py            # report only
    python tools/shrink_art.py --write    # resize, verify, replace

THE CHARACTER PARTS AND THE HATS WERE 6-15x OVERSAMPLED. `part-shoe` is a 599px
picture drawn at about 40 device pixels on a phone; `part-leg` is 233x1024 drawn
at 19. Between them the thirteen lossless files were 1.26MB of a 4.4MB payload,
which on the 5 Mbps line this is tested against is two seconds of the loading
screen spent on detail no display can resolve.

HOW THE TARGET IS DERIVED, rather than guessed:

    SCALE = min(CH/980, CW/1450)        (index.html, resize())

so one world unit is SCALE device pixels. A 4K landscape screen -- far past any
phone -- gives min(2160/980, 3840/1450) = 2.20. Round to 2.3 and multiply by 1.5
for the rig's squash/stretch and the larger draw in the intro: **3.45 device
pixels per world unit**, and a part declared `w:78` needs 269 pixels, not 599.

WHY LOSSLESS IS KEPT. The obvious alternative is to leave the resolution alone
and encode lossy, and it is a worse trade -- measured, at the size the sprite is
actually drawn, which is the only place the comparison means anything:

    part          resize (lossless)   lossy q90    both
    part-wing        RMSE 0.63          1.40       2.60
    part-shoe             1.59          0.78       4.48
    part-leg              0.94          0.88       6.49

Resizing is near-invisible; lossy costs two to seven times more error for a
similar saving, because these are the three things lossy WebP is worst at at
once: hard ink outlines, flat cel fills, and an alpha edge. Comparing at native
resolution would have hidden all of it.

NOTHING IS OVERWRITTEN UNTIL THE RE-ENCODE IS VERIFIED to open, keep its alpha,
and land under the original size."""
import io
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'art')

PX_PER_UNIT = 3.45          # 2.3 (4K landscape) x 1.5 (rig + intro headroom)
FLOOR = 64                  # never go below this on the long edge

# file -> the width it is drawn at, in WORLD units.
#   parts     : the `w:` in loadPart()
#   cosmetics : cosmeticImage `w:` is a MULTIPLE of the head (~78 units)
TARGETS = {
    'part-wing':     78,
    'part-head':     78,
    'part-shoe':     36,
    'part-wingfold': 62,
    'part-leg':      17,
    'part-headref':  84,
    'part-bodyref':  150,
    'cos-shades':    1.60 * 78,
    'cos-scarf':     1.30 * 78,
}

# The four hats are NOT sprites and must not be treated as any. They are opaque
# 1024x559 reference renders of the whole character, shown as picture cards by
# chickens.html and never composited into the game -- which is why they have no
# alpha channel at all, and why the sprite rule (lossless, protect the alpha
# edge) buys nothing here. A photograph-shaped image gets photograph treatment:
# a sensible display width and a lossy encode. They are not in the game's
# payload, so this is chickens.html's weight, not the run's.
CARDS = {'beanie': 512, 'snapback': 512, 'bucket': 512, 'fedora': 512}
CARD_Q = 88


def job(name, target, card):
    """Returns (old_bytes, new_bytes_or_None, blob, note)."""
    p = os.path.join(ART, name + '.webp')
    if not os.path.exists(p):
        return None, None, None, 'missing'

    old = os.path.getsize(p)
    src = Image.open(p)
    src.load()
    has_alpha = 'A' in src.mode or src.mode == 'P'
    src = src.convert('RGBA' if has_alpha else 'RGB')

    if src.width <= target:
        return old, old, None, 'already <= %dpx, left alone' % target

    h = max(1, int(round(src.height * target / src.width)))
    small = src.resize((target, h), Image.LANCZOS)
    buf = io.BytesIO()
    if card or not has_alpha:
        small.save(buf, 'WEBP', quality=CARD_Q, method=6)
    else:
        small.save(buf, 'WEBP', lossless=True, method=6, exact=True)
    blob = buf.getvalue()

    # verify before replacing: it must open, keep the alpha it had, and shrink
    back = Image.open(io.BytesIO(blob))
    back.load()
    kept_alpha = ('A' in back.mode) if has_alpha else True
    if not (back.size == (target, h) and kept_alpha and len(blob) < old):
        return old, old, None, 'REJECTED (%s %s, %.0fKB)' % (back.mode, back.size, len(blob) / 1024)
    return old, len(blob), blob, ''


def main():
    write = '--write' in sys.argv
    tot_old = tot_new = 0
    changed = []

    items = [(n, max(FLOOR, int(round(u * PX_PER_UNIT))), False) for n, u in TARGETS.items()]
    items += [(n, px, True) for n, px in CARDS.items()]

    for name, target, card in sorted(items):
        old, new, blob, note = job(name, target, card)
        if old is None:
            print('  %-16s missing, skipped' % name)
            continue
        tot_old += old
        tot_new += new
        if note:
            print('  %-16s %s' % (name, note))
            continue
        print('  %-16s -> %4dpx  %6.0fKB -> %6.0fKB  (-%.0f%%)%s'
              % (name, target, old / 1024, new / 1024,
                 100.0 * (old - new) / old, '  [card]' if card else ''))
        changed.append((os.path.join(ART, name + '.webp'), blob))

    print('\n  %d files  %.0f KB -> %.0f KB   saving %.0f KB (%.0f%%)'
          % (len(TARGETS) + len(CARDS), tot_old / 1024, tot_new / 1024,
             (tot_old - tot_new) / 1024,
             100.0 * (tot_old - tot_new) / tot_old if tot_old else 0))

    if not write:
        print('  dry run: pass --write to replace them')
        return
    for p, blob in changed:
        with open(p, 'wb') as fh:
            fh.write(blob)
    print('  written: %d files' % len(changed))


if __name__ == '__main__':
    main()
