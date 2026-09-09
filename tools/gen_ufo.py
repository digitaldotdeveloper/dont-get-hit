# -*- coding: utf-8 -*-
"""Generate the FRIED EGG UFO -- the second vehicle -- through Gemini Studio.

   The trolley is a GROUND vehicle whose whole control is a jump. This one is
   the opposite half of the same idea: it flies, so the level under it changes
   rather than the roster of things standing on the road.

   Two attachments, and which is which is stated in the prompt, because with
   one reference "in the EXACT style of the attached picture" is unambiguous
   and with two it is not:

     1  art/truck_drive.webp   the GAME'S style and the PILOT -- bold black
                               outline, flat cel shade, and the same chicken in
                               the same teal cap and the same shades. Without
                               it the craft comes back in somebody else's
                               game's style with somebody else's bird in it.
     2  dgh/ref/ufo-ref.png    the DESIGN -- the user's fried-egg saucer. It is
                               a soft 3D render, so the prompt has to say
                               redraw rather than match.

   Three poses, one sheet, because a sheet is one craft drawn three times and
   three jobs are three craft. They are cut apart by connected component
   (`tools/cut_ufo.py`), never by column: the poses are tilted and overlap in x.

     level   flying straight, lights steady      -- the frame everything scales off
     climb   right-hand edge lifted, lights hot  -- holding
     sink    nosed down, lights nearly out       -- released

   NO BEAMS. The three light shafts in the reference are drawn in code
   (`drawBeams`), for the same reason the trolley's exhaust is: they have to
   answer the button on the frame it is pressed, and a painted beam cannot.

     python tools/gen_ufo.py           # queue and wait
     python tools/gen_ufo.py --fetch   # just pull whatever is ready
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import SHEETS, REF, ROOT as GAME, sheets, need
sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio

OUT = sheets('v2')
TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '4bb94235c42a41f4eab766c1c8a33de9357d5b60c2164caf')

REFS = ("There are TWO attached pictures and they are used for different "
        "things. The FIRST attached picture is the ART STYLE and the PILOT: "
        "copy its bold black outlines, its flat cel-shaded colours, its clean "
        "vector cartoon look, and draw THE SAME chicken -- the same cream "
        "chicken in the same teal baseball cap and the same black sunglasses "
        "with the same orange beak. The SECOND attached picture is the "
        "VEHICLE DESIGN: a flying-saucer built out of a fried egg. REDRAW that "
        "design in the first picture's flat cartoon style -- it must NOT be a "
        "3D render, no soft gradients, no glossy photoreal shading, no "
        "airbrush. Flat colours with a bold black outline, like the first "
        "picture. ")

CRAFT = ("The craft, in every picture: a flying saucer whose hull is a FRIED "
         "EGG. The wide flat body is the egg WHITE -- pure white, with a soft "
         "wavy uneven rim like a fried egg's edge, and a couple of pale grey "
         "shading shapes on it. Sitting on top of it, in the middle, is the "
         "YOLK: a big smooth dome of saturated egg-yolk orange with one flat "
         "pale-yellow highlight shape on it. Under the white body is a "
         "dark grey metal underside with THREE round lamps in a row set into "
         "it, each a bright yellow-white lens in a chrome ring. Set into the "
         "FRONT of the yolk dome, facing right, is a round clear glass cockpit "
         "bubble, and the chicken from the first picture is sitting inside it "
         "-- head, shoulders and both wings clearly visible and fully drawn in "
         "full colour through the glass, gripping a small control stick, cap "
         "and sunglasses on. He is small but unmistakably the same bird. ")

VIEW = ("Seen side-on from very slightly below and slightly in front, "
        "travelling to the RIGHT, so the yolk dome, the pilot and the row of "
        "lamps underneath are all visible. ")

GREEN = ("The background is SOLID FLAT PURE GREEN #00FF00, completely empty, "
         "edge to edge, with NO shadow, NO gradient, NO ground, NO stars, NO "
         "sky and NO glow spilling onto it. Nothing green anywhere in the "
         "artwork itself. NO light beams, NO tractor beam, NO shafts of light "
         "coming out of the lamps -- the lamps glow but nothing leaves them. "
         "No text, no watermark, no logo, no border, no frame, no grid lines. ")

SHEET = ("ONE image containing EXACTLY 3 SEPARATE PICTURES of that same "
         "flying saucer, laid out in a single horizontal row, evenly spaced, "
         "with a clear wide band of flat green between them so they do not "
         "touch or overlap. It is the SAME craft in all three -- identical "
         "size, identical shape, identical colours, identical pilot -- and "
         "they differ ONLY in the tilt of the craft and how bright the three "
         "lamps underneath are. Left to right: "
         "(1) LEVEL -- flying dead level, the lamps glowing a steady medium "
         "yellow. "
         "(2) CLIMBING -- the whole saucer tilted back about 25 degrees so its "
         "RIGHT-HAND edge is lifted up and its left-hand edge is down, the "
         "three lamps blazing bright white-hot and wider. "
         "(3) DESCENDING -- the whole saucer tilted forward about 20 degrees "
         "so its RIGHT-HAND edge is dipped down, the three lamps dim and "
         "small, almost out. "
         "The pilot stays upright in his bubble in all three and looks "
         "pleased with himself.")

JOBS = [('ufo_ride', REFS + CRAFT + VIEW + GREEN + SHEET)]


def main():
    """The library is GLOBAL and other sessions queue into the same studio, so
       what comes back is filtered by the JOB IDS this run created rather than
       taken off the top -- `library()[:N]` has quietly pulled another
       session's renders into a repo before."""
    s = Studio(TOKEN)
    ids = []
    if '--fetch' not in sys.argv:
        style  = s.upload(os.path.join(GAME, 'art', 'truck_drive.webp'))
        design = s.upload(need(os.path.join(REF, 'ufo-ref.png')))
        for name, prompt in JOBS:
            print('queueing %s ...' % name)
            r = s.generate(prompt, runs=3, model='Pro', attach=[style, design])
            ids += [j['id'] if isinstance(j, dict) else j
                    for j in (r.get('jobs') or r.get('ids') or [])] or [r.get('id')]
        print('queued as %s -- waiting (a few minutes)' % ids)
        s.wait()
    mine = [i for i in s.library() if not ids or i.get('jobId') in ids]
    print('%d of mine in the library' % len(mine))
    for item in mine[:3]:
        print('  downloaded %s' % s.download(item, OUT))


if __name__ == '__main__':
    main()
