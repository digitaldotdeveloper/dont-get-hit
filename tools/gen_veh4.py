# -*- coding: utf-8 -*-
"""The four new vehicles, through Gemini Studio.

   Same two-attachment shape `gen_ufo.py` proved, and the prompt SAYS which is
   which, because with one reference "in the EXACT style of the attached
   picture" is unambiguous and with two it is not:

     1  art/truck_drive.webp   the GAME'S style and the PILOT. The brief is
                               emphatic that Nugget is not to be redesigned, so
                               he goes in as a picture rather than as adjectives
                               -- same cream chicken, same teal cap, same
                               shades, same orange beak.
     2  dgh/ref/veh-*.png      the DESIGN, from the user's own concept sheets.
                               They are marketing boards: several poses, a
                               background, a logo and captions. The prompt has
                               to say "take the vehicle, ignore the page".

   THE CORN ROCKET IS ASKED FOR ON MAGENTA and the other three on green, for
   exactly the reason the parallax layers are: **nothing in the art may be the
   key colour**, and a corn cob's husk is bright green. Key green out of it and
   you take the leaves with it. Nugget's teal cap survives a green key -- it
   was measured on the saucer sheet -- but a saturated leaf does not.

   WHAT IS NOT ASKED FOR is as deliberate as what is. No flame on the rocket,
   no spring or base under the eggshell, no lightning on the spoon, no toast in
   the toaster's slot: every one of those has a RULE (it burns with the button,
   it compresses with the landing, it arcs on the flip, it rises with the
   charge) and a painted one cannot answer an input on the frame it happens.
   They are drawn in code, the way the trolley's exhaust and the saucer's beam
   are. The toast is generated as its own object because it slides rather than
   changes shape.

     python tools/gen_veh4.py            # queue all four and wait
     python tools/gen_veh4.py --only rocket
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import REF, ROOT as GAME, sheets, need
sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio

OUT = sheets('v2')
TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '4bb94235c42a41f4eab766c1c8a33de9357d5b60c2164caf')

REFS = ("There are TWO attached pictures and they are used for different "
        "things. The FIRST attached picture is the ART STYLE and the PILOT: "
        "copy its bold black outlines, its flat cel-shaded colours and its "
        "clean vector cartoon look, and draw THE SAME chicken -- the same "
        "cream-white chicken in the same teal-green baseball cap, the same "
        "black sunglasses, the same orange beak and the same red comb. Do NOT "
        "redesign the chicken in any way. The SECOND attached picture is a "
        "CONCEPT SHEET for the vehicle: ignore its background, its logo, its "
        "captions and its extra poses, and take ONLY the vehicle design from "
        "it. REDRAW that vehicle in the first picture's flat cartoon style -- "
        "flat colours and a bold black outline, no soft airbrushed shading, no "
        "3D render, no gradients, no photorealism. ")

def key(colour):
    return ("The background is SOLID FLAT PURE %s, completely empty, edge to "
            "edge, with NO shadow, NO gradient, NO ground, NO sky and no glow "
            "spilling onto it. Nothing %s anywhere in the artwork itself. "
            "No text, no watermark, no logo, no border, no frame, no grid "
            "lines, no captions, no arrows. " % (colour[0], colour[1]))

GREEN   = key(("GREEN #00FF00", "green"))
MAGENTA = key(("MAGENTA #FF00FF", "magenta or pink"))

ONE = ("Draw EXACTLY ONE of it, one single vehicle, centred, filling the frame "
       "with a small even margin. Do not draw it twice, no turnaround, no "
       "second view, no inset. Seen exactly SIDE-ON, travelling to the RIGHT. ")

JOBS = {
 'corn_rocket': REFS + MAGENTA + ONE +
   "The vehicle is a giant corn cob built into a rocket: a fat yellow corn cob "
   "body with rows of chunky kernels, a shiny red pointed nose cone at the "
   "RIGHT-HAND end with a silver collar behind it, big green husk leaves "
   "swept back along the body like fins, and two chrome rocket engine nozzles "
   "at the LEFT-HAND end. The chicken sits in an open cockpit cut into the top "
   "of the cob behind a small clear windscreen, both wings on a steering "
   "wheel, leaning forward, grinning. "
   "NO FLAME, NO FIRE, NO EXHAUST, NO SMOKE and no speed lines of any kind -- "
   "the engines are cold and empty. Nothing may come out of the nozzles.",

 'egg_hopper': REFS + GREEN + ONE +
   "The vehicle is a big cracked EGGSHELL with the chicken sitting down inside "
   "it: a smooth cream-white shell with a jagged broken rim around the top and "
   "a few pale brown speckles, the chicken sitting in it with his wings up and "
   "his white trainers sticking out over the front, wearing orange safety "
   "straps across his chest like a fairground ride. "
   "Draw the SHELL AND THE CHICKEN ONLY. There is NO SPRING, NO COIL, NO "
   "yellow base plate and NO ground underneath it -- the bottom of the shell "
   "is the bottom of the picture and nothing is attached to it. The shell is "
   "upright and level.",

 'magnet_spoon': REFS + GREEN + ONE +
   "The vehicle is a giant polished silver SPOON lying flat and level, with "
   "its deep oval bowl at the RIGHT-HAND end and its long handle stretching "
   "away to the LEFT. The chicken is sitting back in the bowl of the spoon "
   "like an armchair with his trainers up on the rim, one wing pointing "
   "forward. Bolted to the spoon are TWO chunky machined magnet discs, in "
   "brushed steel with a glowing blue band around each: one on TOP of the "
   "handle pointing up, marked with a blue letter N, and one UNDERNEATH the "
   "bowl pointing down, marked with a red letter S. "
   "NO lightning, NO electric arcs, NO sparks, NO glowing aura around the "
   "vehicle and no motion streaks -- the coils are switched off.",

 'toaster_jumper': REFS + GREEN +
   "ONE image containing EXACTLY 2 SEPARATE OBJECTS, side by side in a row "
   "with a clear wide band of flat background between them so they do not "
   "touch. "
   "THE FIRST OBJECT, on the left and much the larger: a cream-white two-slot "
   "TOASTER built into a little car, seen exactly SIDE-ON and travelling to "
   "the RIGHT. It has a rounded chrome-edged body with a red and white stripe "
   "on the back, a big red lever on a chrome slide down the back, an orange "
   "chicken-head logo on its side, and four fat black off-road tyres with red "
   "rims. The chicken sits in an open cockpit in the top of it, wings "
   "forward, grinning. THE TOAST SLOTS ON TOP ARE EMPTY -- draw two dark "
   "empty slots and NOTHING sticking out of them, no toast, no bread, no "
   "glow, no heat, no fire. "
   "THE SECOND OBJECT, on the right and much smaller: TWO slices of golden "
   "toasted bread standing upright side by side, slightly overlapping, seen "
   "flat-on, with toasted brown edges and a bold black outline. Just the two "
   "slices on their own -- no toaster, no plate, no crumbs, no sparkle.",
}

REF_FOR = {'corn_rocket':'veh-rocket.png', 'egg_hopper':'veh-hopper.png',
           'magnet_spoon':'veh-spoon.png', 'toaster_jumper':'veh-toaster.png'}


def main():
    s = Studio(TOKEN)
    only = sys.argv[sys.argv.index('--only')+1] if '--only' in sys.argv else None
    names = [n for n in JOBS if not only or only in n]
    print('quota before: %s' % s.usage())
    style = s.upload(os.path.join(GAME, 'art', 'truck_drive.webp'))
    for name in names:
        design = s.upload(need(os.path.join(REF, REF_FOR[name])))
        print('queueing %s ...' % name)
        s.generate(JOBS[name], runs=2, model='Pro', attach=[style, design])
    """The studio is SHARED, so this polls for its OWN renders by a needle in
       the prompt rather than calling s.wait(), which waits for everybody."""
    want = len(names)*2
    t0 = time.time()
    while time.time() - t0 < 2400:
        mine = [i for i in s.library()
                if 'TWO attached pictures' in (i.get('prompt') or '')
                and i.get('createdAt', 0)/1000 > t0 - 60]
        print('  %4ds  %d/%d back' % (time.time()-t0, len(mine), want))
        if len(mine) >= want:
            break
        time.sleep(25)
    for it in mine:
        print('   %s' % s.download(it, OUT))


if __name__ == '__main__':
    main()
