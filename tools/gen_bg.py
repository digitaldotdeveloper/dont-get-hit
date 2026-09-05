# -*- coding: utf-8 -*-
"""Generate the parallax background layers through Gemini Studio.

   Two layers, generated separately so they can move at different speeds:

     bg_far   hills and a treeline, hazy, almost no detail -- the slow layer
     bg_mid   the farm itself, buildings spaced out with sky between them

   Both are asked for on a flat magenta field rather than a painted sky. Magenta
   appears nowhere in the palette, so it keys out cleanly, and keying the sky is
   the whole trick: the game draws one sky behind everything and the layers
   never have to agree about what colour it is. (The old three panels each had
   their own painted sky -- (27,157,252), (56,182,253) and (1,117,216) at the
   same height -- and that is exactly what could not be reconciled.)

     python tools/gen_bg.py            # queues the jobs and waits
     python tools/gen_bg.py --fetch    # just download whatever is ready
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import SHEETS, REF, AUDIOSRC, ROOT as GAME, sheets, need
import os, sys, time, json
sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio

TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN', '1a64c4bc884692a41e0bf84ed3fb4729a4a650484f264530')
OUT = sheets('v2')

STYLE = ("2D side-scrolling mobile game background art, bold black outlines, flat "
         "cel-shaded colours, clean vector cartoon look, bright and friendly, "
         "wide banner composition, no text, no watermark, no characters, no people, "
         "no animals. ")

JOBS = [
    ('bg_far', STYLE +
     "FAR DISTANCE LAYER ONLY. Soft rolling green hills and a low line of round "
     "trees along the bottom third, with two or three tiny distant barn roofs. "
     "Hazy, pale, low contrast, muted -- this sits far away behind everything. "
     "The hills run unbroken from the left edge to the right edge, and the left "
     "and right edges are at the same height so the image can repeat. "
     "Everything above the hills is SOLID FLAT MAGENTA #FF00FF, completely "
     "empty -- no sky, no clouds, no gradient, no shading in the magenta area. "
     "No fence, no foreground, no ground texture."),
    ('bg_mid', STYLE +
     "MIDDLE LAYER ONLY. A row of farm structures standing side by side on one "
     "straight ground line at the very bottom edge: a big red barn with a grey "
     "roof, a tall grey grain silo, a wooden windmill on a lattice tower, a "
     "water tower, a small wooden chicken coop, and a patch of tall green corn. "
     "They are evenly spaced with clear empty gaps between them, all the same "
     "distance away, all standing on the bottom edge. Saturated and clear. "
     "Everything that is not a building is SOLID FLAT MAGENTA #FF00FF, "
     "completely empty -- no sky, no clouds, no gradient, no hills, no ground "
     "below the line. No fence."),
]


def main():
    s = Studio(TOKEN)
    fetch_only = '--fetch' in sys.argv
    if not fetch_only:
        for name, prompt in JOBS:
            print('queueing %s ...' % name)
            s.generate(prompt, runs=2, model='Pro')
        print('waiting for the queue to drain (a few minutes)')
        s.wait()
    lib = s.library()
    print('library has %d items; newest first' % len(lib))
    got = 0
    for item in lib[:8]:
        path = s.download(item, OUT)
        print('  downloaded %s' % path)
        got += 1
        if got >= 4: break


if __name__ == '__main__':
    main()
