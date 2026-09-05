# -*- coding: utf-8 -*-
"""Generate the truck's moving parts through Gemini Studio.

   The rig was one flat picture per pose, so it slid down the road with its
   wheels locked -- the single loudest thing wrong with it, because a wheel that
   does not turn reads as a sticker rather than a vehicle. And the exhaust fire
   was three quadratic curves drawn in code, which is fine for a flicker and
   nothing like the painted art it comes out of.

   Both are fixed the same way: take the moving part OUT of the still and give
   it its own frames.

     truck_wheel   one wheel, dead centre, square -- rotated in code, so one
                   picture covers every speed instead of a fixed cycle
     truck_flame   a strip of exhaust blasts, drawn in the game's own style and
                   played back off the same clock the flicker used

   Both are asked for on flat green, which is what imglib.key_green expects and
   what every other sheet in this project uses. The driving frame goes along as
   an attachment so the style, the palette and the line weight match the rig
   they are going onto -- asking for "cartoon wheel" without it comes back in
   somebody else's game's style.

     python tools/gen_truckfx.py           # queue and wait
     python tools/gen_truckfx.py --fetch   # just pull whatever is ready
"""
import os, sys, json
sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'sheets', 'v2')
TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '4bb94235a6d0b1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8')

STYLE = ("2D mobile game sprite art in the EXACT style of the attached picture: "
         "bold black outlines, flat cel-shaded colours, clean vector cartoon "
         "look, saturated, no gradients, no photorealism, no text, no watermark. ")

GREEN = ("The background is SOLID FLAT PURE GREEN #00FF00, completely empty, "
         "edge to edge, with no shadow, no gradient, no ground and no glow "
         "spilling onto it. Nothing green anywhere in the artwork itself. ")

JOBS = [
    ('truck_wheel', STYLE + GREEN +
     "ONE monster-truck wheel on its own, seen exactly side-on, filling the "
     "frame, PERFECTLY CENTRED in a SQUARE image so the middle of the image is "
     "the middle of the axle. Match the wheels in the attached picture: a fat "
     "black off-road tyre with deep chunky tread blocks around the outside, a "
     "bright red rim with a dark centre hub and small silver bolts around it, "
     "and a thick black outline. Draw the tread blocks clearly and evenly all "
     "the way round the tyre so the wheel obviously reads as turning when it "
     "is spun. Perfectly circular. Just the wheel -- no truck, no axle, no "
     "suspension, no shadow, no motion blur, no speed lines."),

    ('truck_flame', STYLE + GREEN +
     "A HORIZONTAL STRIP OF EXACTLY 6 SEPARATE PICTURES of a cartoon exhaust "
     "flame, evenly spaced in one row with clear green gaps between them, all "
     "the same size, all on the same horizontal centre line. Every flame is a "
     "jet of fire blasting HORIZONTALLY TO THE LEFT, with its blunt root at the "
     "RIGHT-HAND edge of its picture and its pointed tip at the LEFT. Layered "
     "cartoon fire: a deep red-orange outer flame, a bright orange middle, and "
     "a pale yellow-white core running down the middle, each with a bold black "
     "outline, plus a few small separate flecks of flame breaking off near the "
     "tip. The 6 pictures are the same flame at 6 moments of one loop -- the "
     "tongues lick and curl into different shapes and the flame is a little "
     "longer and shorter across the strip -- so they play as a smooth cycle. "
     "No pipe, no exhaust, no truck, no smoke."),
]


def main():
    s = Studio(TOKEN)
    if '--fetch' not in sys.argv:
        ref = s.upload(os.path.join(ROOT, 'art', 'truck_drive.webp'))
        for name, prompt in JOBS:
            print('queueing %s ...' % name)
            s.generate(prompt, runs=2, model='Pro', attach=[ref])
        print('waiting for the queue to drain (a few minutes)')
        s.wait()
    lib = s.library()
    print('library has %d items; newest first' % len(lib))
    for item in lib[:6]:
        print('  downloaded %s' % s.download(item, OUT))


if __name__ == '__main__':
    main()
