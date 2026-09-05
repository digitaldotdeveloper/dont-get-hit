# -*- coding: utf-8 -*-
"""Cut the Ant Territory props: the gate, the anthills, the blank signboards.

    python tools/cut_ant_props.py            # newest matching renders
    python tools/cut_ant_props.py --list

Same pipeline as cut_obstacles.py -- key the flat green, split by connected
component, keep the N biggest, put them back in reading order -- and it imports
that module's `parts()` rather than owning a second copy.

THE SIGNBOARDS ARE GENERATED BLANK ON PURPOSE and the game letters them in
code. Three reasons, and the first is the one that decided it: a generator
cannot spell reliably at sign size, and "ANT TERRIROTY" shipped in a screenshot
is a bad day. Second, the jokes are meant to be occasional and varied -- NO
CHICKENS, SUGAR STORAGE, QUEEN ONLY, WORK HARD STAY ANTSOME -- and one blank
board with drawn text is every sign, where one baked sign is one sign. Third,
drawn text stays sharp at any scale on any screen."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import sheets                                    # noqa: E402
from cut_obstacles import parts                             # noqa: E402
from PIL import Image                                       # noqa: E402
import numpy as np                                          # noqa: E402
import json                                                 # noqa: E402

LIB = r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard\library"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'art', 'ant')

# needle in the prompt -> (how many objects, names in reading order)
JOBS = {
    'ONE enormous ancient tree-root and earth mound': (1, ['gate']),
    'THREE separate drawings of an ant hill':         (3, ['hill1', 'hill2', 'hill3']),
    'FOUR separate weathered wooden signboards':      (4, ['sign_a', 'sign_arrow',
                                                           'sign_b', 'sign_wide']),
    # the second doorway, and the signage on the other side of it
    'ONE enormous industrial security door':         (1, ['lab_door']),
    'FOUR separate industrial warning signs':        (4, ['plate_plain', 'plate_hazard',
                                                          'plate_screen', 'plate_chain']),
}


def candidates():
    try:
        idx = json.load(open(os.path.join(LIB, 'index.json'), encoding='utf-8'))
    except Exception:
        return {}
    out = {}
    for e in idx:
        pr = e.get('prompt') or ''
        for needle in JOBS:
            if needle in pr:
                p = os.path.join(LIB, e['file'].replace('/', os.sep))
                if os.path.exists(p):
                    out.setdefault(needle, []).append(p)
    return out


def main():
    cands = candidates()
    if '--list' in sys.argv:
        for k, v in cands.items():
            print(k[:44], len(v))
            for p in v[:4]:
                print('   ', os.path.basename(p))
        return

    os.makedirs(ART, exist_ok=True)
    pins = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)
    for needle, (n, names) in JOBS.items():
        src = pins.get(names[0]) or (cands.get(needle) or [None])[0]
        if not src:
            print('  %-10s no render yet -- skipped' % names[0])
            continue
        got = parts(src, n)
        if len(got) < n:
            print('  %-10s only %d of %d objects found on %s'
                  % (names[0], len(got), n, os.path.basename(src)))
        for name, p in zip(names, got):
            im = Image.fromarray(p['img'], 'RGBA')
            out = os.path.join(ART, name + '.webp')
            im.save(out, 'WEBP', quality=92, method=6, exact=True)
            print('  %-11s %4dx%-4d %5d KB' % (name, im.width, im.height,
                                               os.path.getsize(out) // 1024))


if __name__ == '__main__':
    main()
