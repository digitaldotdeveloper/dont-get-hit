# -*- coding: utf-8 -*-
"""Cut the Ant Empire parallax layers, and split the hanging half off the top.

    python tools/cut_ant_bg.py                # pick the newest matching renders
    python tools/cut_ant_bg.py --list         # show candidates and exit
    python tools/cut_ant_bg.py far=FILE ...   # pin a specific take

Reuses tools/bg_layers.py wholesale for the parts that are the same -- key the
magenta, search for the loop seam, crop between -- because they are the same
problem and a second copy of a seam searcher is a second thing to get wrong.

WHAT IS DIFFERENT, AND WHY THERE IS A FOURTH LAYER SLOT.

The farm's near layer is a fence: a short band along the bottom. The ant near
layer is an earth bank along the bottom AND a set of roots hanging DOWN from the
top with open air between them -- because the brief's hard rule is that Nugget
can fly to the top of the screen, so the upper area has to be framed rather than
closed.

The game anchors every layer by its BOTTOM edge and scales it by a fraction of
GROUND. One tall tile holding both halves cannot work: sized so the bank sits
right, the roots are somewhere in the middle of the sky; sized so the roots
reach the top, the bank is enormous. They are two things at two anchors.

So the source is SPLIT on the empty band that already separates them: content
above the gap becomes `hang`, drawn anchored to the TOP of the screen; content
below becomes `near`, anchored to the ground like everything else. The split is
found by measuring the widest run of near-empty rows in the middle of the image,
never assumed -- the generator puts the gap in a different place every take."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import sheets                                   # noqa: E402
import bg_layers as BL                                     # noqa: E402
from PIL import Image                                      # noqa: E402

SRC = sheets('v5')
LIB = r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard\library"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'art', 'ant')

# layer -> (words that must appear in the prompt, edge window for the seam search)
WANT = {
    'far':  ('FAR DISTANCE LAYER of a huge underground', 0.30),
    'mid':  ('MIDDLE LAYER of a busy underground', 0.22),
    'near': ('NEAR FOREGROUND LAYER: a bank of rich brown', 0.26),
}


def library_index():
    import json
    p = os.path.join(LIB, 'index.json')
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return []


def candidates():
    """newest-first render paths per layer, matched on the prompt that made them."""
    out = {k: [] for k in WANT}
    for e in library_index():
        pr = e.get('prompt') or ''
        for k, (needle, _) in WANT.items():
            if needle in pr:
                p = os.path.join(LIB, e['file'].replace('/', os.sep))
                if os.path.exists(p):
                    out[k].append((e.get('createdAt', 0), p))
    for k in out:
        out[k].sort(reverse=True)
        out[k] = [p for _, p in out[k]]
    return out


def split_row(im, lo=0.18, hi=0.86):
    """The widest run of near-empty rows between lo and hi -> where to cut.

       Returns None when there is no gap, which is the honest answer for the
       far layer: it is all one silhouette band and has nothing hanging."""
    w, h = im.size
    px = im.load()
    empt = []
    for y in range(int(h*lo), int(h*hi)):
        n = sum(1 for x in range(0, w, 4) if px[x, y][3] > 40)
        empt.append(n <= max(1, (w // 4) * 0.02))
    best = cur = 0
    beststart = curstart = None
    for i, e in enumerate(empt):
        if e:
            if curstart is None: curstart = i
            cur += 1
            if cur > best: best, beststart = cur, curstart
        else:
            cur = 0; curstart = None
    if best < h*0.06:
        return None
    return int(h*lo) + beststart + best // 2


def save(im, name):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + '.webp')
    im.save(p, 'WEBP', quality=92, method=6, exact=True)
    print('  %-6s %4dx%-4d  %5d KB' % (name, im.width, im.height,
                                       os.path.getsize(p) // 1024))
    return p


def main():
    pins = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)
    cands = candidates()

    if '--list' in sys.argv:
        for k, v in cands.items():
            print(k)
            for p in v[:5]:
                print('   ', os.path.basename(p))
        return

    for name, (_, window) in WANT.items():
        src = pins.get(name) or (cands[name][0] if cands[name] else None)
        if not src:
            print('  %-6s no render found yet -- skipped' % name)
            continue
        if not os.path.isabs(src):
            src = os.path.join(SRC, src)
        im = BL.key_magenta(Image.open(src))
        b, a, score = BL.loop_seam(im, window)
        tile = im.crop((b, 0, a, im.height))
        print('%-5s from %-28s seam %4d..%-4d score %d'
              % (name, os.path.basename(src)[-28:], b, a, score // 1000))

        cut = split_row(tile) if name != 'far' else None
        if cut:
            top = tile.crop((0, 0, tile.width, cut))
            bot = tile.crop((0, cut, tile.width, tile.height))
            t, _ = BL.content_rows(top)
            if t > 0.02:
                pass                     # hang is anchored at the TOP: keep its origin
            tb, _ = BL.content_rows(bot)
            if tb > 0.02:
                bot = bot.crop((0, int(tb*bot.height), bot.width, bot.height))
            save(bot, name)
            if name == 'near':
                # trim the hang tile's empty BOTTOM, it hangs from y=0
                w, h = top.size
                px = top.load()
                last = 0
                for y in range(h):
                    if any(px[x, y][3] > 40 for x in range(0, w, 5)): last = y
                save(top.crop((0, 0, w, min(h, last + 2))), 'hang')
        else:
            t, _ = BL.content_rows(tile)
            if t > 0.02:
                tile = tile.crop((0, int(t*tile.height), tile.width, tile.height))
            save(tile, name)


if __name__ == '__main__':
    main()
