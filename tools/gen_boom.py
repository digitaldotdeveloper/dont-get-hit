# -*- coding: utf-8 -*-
"""A dynamite fireball, as its own cycle.

   The blast has been borrowing the CAGE's explosion -- five frames cut for a
   barn door being kicked out, scaled up three times and hung behind a chicken.
   It reads as a yellow star and it is over in half a second, which is a fifth
   of the flight it is supposed to have caused.

   So: its own strip, asked for the way the exhaust flame was, because that one
   worked. SIX SEPARATE PICTURES IN A ROW is the wording that gets a cuttable
   cycle out of this model; "an explosion animation" gets one picture with
   motion blur on it.

   The truck's own flame goes along as the attachment rather than the mystery
   egg, because this is fire and that is the only fire the game already has --
   the palette and the layering have to match it or the blast looks like it
   came out of a different game than the exhaust does.

     python tools/gen_boom.py           # queue and wait
     python tools/gen_boom.py --fetch   # just pull whatever is ready

   Cut with tools/cut_boom.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import sheets
sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT   = sheets('v6')
TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '4bb94235a6d0b1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8')

STYLE = ("2D mobile game sprite art in the EXACT style of the attached picture: "
         "bold black outlines, flat cel-shaded colours, clean vector cartoon "
         "look, saturated, no gradients, no photorealism, no text, no watermark. ")

GREEN = ("The background is SOLID FLAT PURE GREEN #00FF00, completely empty, "
         "edge to edge, with no shadow, no gradient, no ground and no glow "
         "spilling onto it. Nothing green anywhere in the artwork itself. ")

JOBS = [
    ('boom_strip', STYLE + GREEN +
     "A HORIZONTAL STRIP OF EXACTLY 6 SEPARATE PICTURES of a cartoon dynamite "
     "explosion, evenly spaced in one row with clear green gaps between them, "
     "all in boxes of the same size, all on the same horizontal centre line. "
     "Each picture is CENTRED on the middle of the blast. The 6 pictures are "
     "one explosion at 6 moments, in order left to right: "
     "1 a small tight white-hot core with a few short spikes; "
     "2 a bigger ball of bright yellow fire with orange spikes bursting out; "
     "3 the biggest frame, a full round fireball, pale yellow core, orange "
     "middle, deep red-orange outer edge, with jagged flame spikes all round "
     "and a few chunks of dirt flying off; "
     "4 the fire beginning to break up, the core fading to orange, grey-brown "
     "smoke lobes appearing round the outside; "
     "5 mostly billowing grey-brown smoke with only patches of orange fire "
     "left inside it; "
     "6 a loose ball of grey-brown smoke, no fire. "
     "Every frame has the same thick black outline as the attached picture. "
     "No ground, no shadow, no debris trails, no text, no numbers, no frame "
     "borders and no grid lines."),
]


def main():
    s = Studio(TOKEN)
    os.makedirs(OUT, exist_ok=True)
    if '--fetch' not in sys.argv:
        u = s.usage()
        cur = (u.get('current') or {}).get('percent')
        print('daily window at %s%%' % cur)
        if cur is not None and cur > 92:
            sys.exit('too little of the window left; try after the reset')
        before = len(s.library())
        ref = s.upload(os.path.join(ROOT, 'art', 'fx', 'flame0.webp')
                       if os.path.exists(os.path.join(ROOT, 'art', 'fx', 'flame0.webp'))
                       else os.path.join(ROOT, 'art', 'truck_drive.webp'))
        for name, prompt in JOBS:
            print('queueing %s ...' % name)
            s.generate(prompt, runs=3, model='Pro', attach=[ref])
        s.wait()
        lib = s.library()
        n = max(0, len(lib) - before)
        print('%d new items' % n)
    else:
        lib = s.library(); n = 3
    for item in lib[:n]:
        print('  downloaded %s' % s.download(item, OUT))
    print('now run: python tools/cut_boom.py --list')


if __name__ == '__main__':
    main()
