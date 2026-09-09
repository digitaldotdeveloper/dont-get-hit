# -*- coding: utf-8 -*-
"""Pull a world's panels onto one tone, so a join is a wall and not a building.

    python tools/harmonise.py                # report
    python tools/harmonise.py --write        # apply
    python tools/harmonise.py prison --write

Naming each world's palette in the prompt got most of the way there and cannot
get the rest: four panels are four independent renders, and "pale grey breeze
block" comes back as warm grey once and white subway tile the next time. In the
game that is a hard vertical step at the join -- the fault the continuous walls
were supposed to end.

The alternative was to attach the world's first panel to the other three as a
reference, which works and costs three more renders per world. This costs
nothing and is repeatable, so it is tried first.

The method is a partial Reinhard transfer: every panel is moved a fraction of
the way toward its WORLD'S median mean and median spread, per channel, measured
only where the panel is opaque. Partial on purpose -- a full transfer makes four
pictures with one histogram, which is flat and grey. The strength is set to
leave each panel its own character while removing the step between them.

It does not touch the farm or the approach: those panels are meant to be
separate buildings with sky between them, and matching their tone would erase
the deliberate difference between a red barn and a straw field."""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_mid_panels import WORLDS                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = 0.62          # how far toward the world's tone; 1.0 would flatten them


def stats(path):
    a = np.asarray(Image.open(path).convert('RGBA')).astype(np.float64)
    op = a[..., 3] > 40
    if not op.any():
        return None
    px = a[..., :3][op]
    return px.mean(axis=0), px.std(axis=0) + 1e-6


def apply(path, tgt_mean, tgt_std, write):
    a = np.asarray(Image.open(path).convert('RGBA')).astype(np.float64)
    op = a[..., 3] > 40
    px = a[..., :3][op]
    m, s = px.mean(axis=0), px.std(axis=0) + 1e-6
    gain = 1 + K * (tgt_std / s - 1)
    shift = K * (tgt_mean - m)
    out = (px - m) * gain + m + shift
    moved = float(np.abs(out - px).mean())
    if write:
        a[..., :3][op] = np.clip(out, 0, 255)
        Image.fromarray(a.astype(np.uint8), 'RGBA').save(
            path, 'WEBP', lossless=True, quality=100, method=6)
    return moved


def main():
    write = '--write' in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith('-')] or list(WORLDS)
    for world in want:
        files = [os.path.join(ROOT, 'art', 'panels', world, n + '.webp')
                 for n in sorted(WORLDS[world])]
        files = [f for f in files if os.path.exists(f)]
        if len(files) < 2:
            print('  %-7s only %d panel(s) -- nothing to match' % (world, len(files)))
            continue
        st = [stats(f) for f in files]
        tgt_mean = np.median([s[0] for s in st], axis=0)
        tgt_std = np.median([s[1] for s in st], axis=0)
        spread = float(np.abs(np.array([s[0] for s in st]) - tgt_mean).mean())
        print('  %-7s %d panels, brightness spread %.1f across them%s'
              % (world, len(files), spread, '' if write else '   [dry run]'))
        for f, s in zip(files, st):
            moved = apply(f, tgt_mean, tgt_std, write)
            print('     %-6s mean %3.0f %3.0f %3.0f  ->  moves %.1f'
                  % (os.path.basename(f).split('.')[0],
                     s[0][0], s[0][1], s[0][2], moved))
    if not write:
        print('\n[dry run; pass --write]')


if __name__ == '__main__':
    main()
