# -*- coding: utf-8 -*-
"""Cut the ant actors into art/ant/ and print their FRAME rows.

    python tools/cut_ants.py
    python tools/cut_ants.py --list

    ant_walk   -> antw0..5   one walk cycle
    ant_carry  -> antc0..3   sugar cube / crumb / leaf / berry
    ant_guard  -> antg0..1   bored, then startled

REGISTRATION IS THE WHOLE JOB and it is the same lesson the crow taught: cutting
each frame to its own bounding box and drawing them centred makes the walk
BOB, because the box is mostly legs and the legs are the thing that moves.

The datum here is the GROUND LINE, not a feature of the ant -- these are
characters standing on a floor, and the floor is the thing that must not move.
The generator helpfully draws that line, and it draws one per ROW when it
decides to lay six frames out as two rows of three (which it did). So the
ground is measured PER ROW: the lowest pixel of the tallest frame in that row.
Take one ground line for the whole sheet and the second row walks underground.

`ay` in the printed rows is pixels from the top of the frame down to that
ground line, which is exactly what FRAME_DATA means by it everywhere else."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cut_obstacles import parts                              # noqa: E402
from imglib import key_green, despill, bbox, label           # noqa: E402
from PIL import Image                                        # noqa: E402
import numpy as np                                           # noqa: E402

LIB = r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard\library"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'art', 'ant')

JOBS = [
    ('SIX separate drawings of THE SAME single cartoon worker ant', 6, 'antw'),
    ('FOUR separate drawings of cartoon worker ants in a row',      4, 'antc'),
    ('TWO separate drawings of the same cartoon guard ant',         2, 'antg'),
    # who works down there. The scientists' LAST frame is the startled one --
    # drawAnts relies on that ordering to make them react to the chicken.
    ('FOUR separate drawings of cartoon ant SCIENTISTS',            4, 'antsci'),
    ('THREE separate drawings of cartoon worker ants in a row',     3, 'antt'),
]


def candidates():
    try:
        idx = json.load(open(os.path.join(LIB, 'index.json'), encoding='utf-8'))
    except Exception:
        return {}
    out = {}
    for e in idx:
        pr = e.get('prompt') or ''
        for needle, _, _ in JOBS:
            if needle in pr:
                p = os.path.join(LIB, e['file'].replace('/', os.sep))
                if os.path.exists(p):
                    out.setdefault(needle, []).append(p)
    return out


def parts_no_rule(path, want, tol=52):
    """`parts()`, but with the drawn ground line taken out first.

       The generator obligingly draws a black rule under each row so the ants
       have something to stand on, and that rule TOUCHES ALL OF THEM: the
       connected-component split then returns one row-wide blob per row instead
       of one ant per ant. Six frames came back as two.

       Any horizontal run of dark pixels spanning most of the sheet is that
       rule and nothing else -- no ant is 60% of the width -- so those rows are
       erased before labelling. The ants keep their own outlines; they just stop
       holding hands. The baseline itself is not lost: it is exactly where the
       erased rows were, and that is what grounds the frames afterwards."""
    rgba = despill(key_green(Image.open(path), tol))
    a = rgba[..., 3] > 0
    dark = a & (rgba[..., :3].max(axis=2) < 110)
    h, w = a.shape
    wide = dark.sum(axis=1) > w*0.55
    ruled = np.where(wide)[0]
    for y in ruled:
        rgba[y, :, 3] = 0
    lab, n = label(rgba[..., 3] > 0)
    cand = []
    for i in range(1, n + 1):
        m = lab == i
        px = int(m.sum())
        if px < 1200:
            continue
        bb = bbox(m)
        cand.append((px, i, m, bb))
    cand.sort(key=lambda c: -c[0])
    out = []
    for px, i, m, bb in cand[:want]:
        sub = rgba[bb[1]:bb[3], bb[0]:bb[2]].copy()
        sub[..., 3] = np.where(m[bb[1]:bb[3], bb[0]:bb[2]], sub[..., 3], 0)
        out.append({'img': sub, 'x': int(bb[0]), 'y': int(bb[1]),
                    'w': int(bb[2]-bb[0]), 'h': int(bb[3]-bb[1])})
    if len(ruled):
        print('    (erased %d ground-rule rows)' % len(ruled))
    return out


def rows_of(items, tol=0.6):
    """Regroup the reading-ordered items back into rows, so each row can be
       grounded on its own baseline."""
    rows = []
    for p in items:
        cy = p['y'] + p['h']/2.0
        for r in rows:
            if abs(cy - r['cy']) < max(p['h'], r['h'])*tol:
                r['items'].append(p)
                r['cy'] = sum(q['y'] + q['h']/2.0 for q in r['items'])/len(r['items'])
                r['h'] = max(r['h'], p['h'])
                break
        else:
            rows.append({'cy': cy, 'h': p['h'], 'items': [p]})
    rows.sort(key=lambda r: r['cy'])
    for r in rows:
        r['items'].sort(key=lambda p: p['x'])
    return rows


def main():
    cands = candidates()
    if '--list' in sys.argv:
        for k, v in cands.items():
            print(k[:46], len(v))
        return
    os.makedirs(ART, exist_ok=True)
    pins = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)

    out = {}
    for needle, n, stem in JOBS:
        src = pins.get(stem) or (cands.get(needle) or [None])[0]
        if not src:
            print('  %-6s no render yet -- skipped' % stem)
            continue
        got = parts_no_rule(src, n)
        if len(got) < n:
            print('  %-6s only %d of %d found' % (stem, len(got), n))
        i, rows = 0, rows_of(got)
        frames = []
        for r in rows:
            # one baseline per row: the lowest pixel any frame in it reaches
            ground = max(p['y'] + p['h'] for p in r['items'])
            for p in r['items']:
                im = Image.fromarray(p['img'], 'RGBA')
                name = '%s%d' % (stem, i)
                im.save(os.path.join(ART, name + '.webp'), 'WEBP',
                        quality=92, method=6, exact=True)
                # numpy ints all the way from the labeller; json wants python ones
                frames.append({'f': 'ant/%s.webp' % name, 'w': int(im.width),
                               'h': int(im.height),
                               'ay': round(float(ground) - float(p['y']), 1)})
                i += 1
        out[stem] = frames
        print('%-6s %d frames from %s' % (stem, len(frames), os.path.basename(src)[-30:]))
        for fr in frames:
            print('   %-18s %3dx%-3d ay %.1f' % (fr['f'], fr['w'], fr['h'], fr['ay']))

    print('\n--- paste into ANT_FR in index.html ---')
    print(json.dumps(out, separators=(',', ':')))


if __name__ == '__main__':
    main()
