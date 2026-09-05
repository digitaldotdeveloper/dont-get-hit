# -*- coding: utf-8 -*-
"""Generate the angry crow through Gemini Studio.

   Two sheets, on flat green so cut_crow.py can key them:

     crow_fly    a 2x2 flap cycle of ONE furious crow, side on, facing LEFT
     crow_head   the same bird's screaming head, for the warning badge

   The crow flies right-to-left across the screen, so it is drawn facing LEFT
   and never mirrored in code -- a mirrored bird lights from the wrong side.

     python tools/gen_crow.py            # queue and wait
     python tools/gen_crow.py --fetch    # just pull what is ready
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import SHEETS, REF, AUDIOSRC, ROOT as GAME, sheets, need
import os, sys
sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio

TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '1a64c4bc884692a41e0bf84ed3fb4729a4a650484f264530')
OUT = sheets('v4')

STYLE = ("2D side-scrolling mobile game sprite art, bold black outlines, flat "
         "cel-shaded colours, clean vector cartoon look, bright and saturated, "
         "no text, no watermark, no logo, no border, no frame, no grid lines. ")

BIRD = ("The bird is a furious crow: glossy blue-black feathers, a bright "
        "orange beak held wide open mid-scream, angry narrowed eyes with red "
        "irises under heavy black scowling eyebrows, a few feathers sticking "
        "up off the back of its head. Bright orange legs tucked back under it. "
        "Nothing on the bird is green. Every wing is ONE solid clean shape "
        "with a crisp hard edge, never fine wispy see-through feathers. ")

GREEN = ("The background is SOLID FLAT PURE GREEN #00FF00 everywhere, "
         "completely empty -- no sky, no ground, no gradient, no shadow, no "
         "motion lines, no speed streaks, no dust, no clouds on the green. ")

JOBS = [
    ('crow_fly', STYLE +
     "A 2x2 grid of FOUR drawings of THE SAME single crow, flying. Strict side "
     "profile, the bird FACING LEFT and flying to the left in every one of the "
     "four. " + BIRD +
     "The four drawings are the four steps of one wing flap and differ ONLY in "
     "the wings -- same bird, same size, same angle, same colours, same "
     "expression in all four: "
     "TOP LEFT wings raised straight up above the body almost touching; "
     "TOP RIGHT wings halfway down, spread out level with the body; "
     "BOTTOM LEFT wings pushed fully down below the body; "
     "BOTTOM RIGHT wings halfway back up. "
     "The four drawings are clearly separated by empty space and must not "
     "touch or overlap each other. " + GREEN),
    ('crow_head', STYLE +
     "ONE single crow HEAD only, no body, no neck below the shoulders, no "
     "wings. Strict side profile FACING LEFT, screaming with the beak wide "
     "open. " + BIRD +
     "Exactly one head, do not draw it twice, no turnaround, no duplicate. "
     + GREEN),
]


def main():
    s = Studio(TOKEN)
    os.makedirs(OUT, exist_ok=True)
    if '--fetch' not in sys.argv:
        for name, prompt in JOBS:
            print('queueing %s ...' % name)
            s.generate(prompt, runs=3, model='Pro')
        print('waiting for the queue to drain (a few minutes)')
        s.wait()
    lib = s.library()
    print('library has %d items; newest first' % len(lib))
    for item in lib[:8]:
        print('  downloaded %s' % s.download(item, OUT))


if __name__ == '__main__':
    main()
