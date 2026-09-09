# -*- coding: utf-8 -*-
"""The death card's icons, through Gemini Studio.

   The card offers three sticks of dynamite and an extra life, and until now the
   dynamite tiers were three identical text buttons and the heart was an inline
   SVG path. Both are fine as placeholders and neither reads as this game: the
   whole point of the card is a decision made in eight seconds, and a decision
   made in eight seconds is made on silhouettes.

   ONE STICK, TWO STICKS, THREE STICKS -- deliberately three separate prompts
   rather than one strip of three. A strip is what the flame wanted, because
   every cell there is the same object at a different moment; here the cells are
   the ESCALATION, and asking one image for "1, then 2, then 3 of the same
   thing" is exactly the "sheet of props" failure PIPELINE.md warns about: the
   model duplicates and varies, and the pieces cannot be cut apart. Three
   prompts cost three times the quota and come back cuttable.

   The mystery egg goes along as the attachment. It is the closest thing the
   game already has to an ICON -- a single shiny object, drawn to read small,
   in the palette and line weight everything else uses -- so it anchors the
   style far better than a piece of scenery would.

     python tools/gen_icons.py           # queue and wait
     python tools/gen_icons.py --fetch   # just pull whatever is ready

   Cut them with tools/cut_icons.py, which is where the choosing happens.
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

# verbatim from the rest of the pipeline, so these cannot drift off-style
STYLE = ("2D mobile game sprite art in the EXACT style of the attached picture: "
         "bold black outlines, flat cel-shaded colours, clean vector cartoon "
         "look, saturated, no gradients, no photorealism, no text, no watermark. ")

GREEN = ("The background is SOLID FLAT PURE GREEN #00FF00, completely empty, "
         "edge to edge, with no shadow, no gradient, no ground and no glow "
         "spilling onto it. Nothing green anywhere in the artwork itself. ")

# Every one of these is drawn at about 26 CSS pixels on the card, so the brief
# is the silhouette and nothing else: big shapes, thick outline, no small parts.
ICON = ("The object is CENTRED and fills the frame with a small even green "
        "margin all round. It is an ICON: it has to read instantly at the size "
        "of a thumbnail, so keep the shapes big and simple, the black outline "
        "thick, and leave out any detail smaller than the outline is wide. "
        "One single object, nothing else in the picture, no shadow, no ground, "
        "no sparkles, no background scenery, no text and no numbers. ")

STICK = ("Each stick is a fat cylinder of red dynamite with a wide cream band "
         "wrapped round its middle, drawn straight-on and slightly tilted, with "
         "a thick black outline. ")

JOBS = [
    ('tnt1', STYLE + GREEN + ICON + STICK +
     "ONE single stick of cartoon dynamite standing almost upright and tilted a "
     "little to the right, with a short curly fuse coming out of the top and a "
     "bright yellow-white spark burning at the tip of the fuse. Just the one "
     "stick."),

    ('tnt2', STYLE + GREEN + ICON + STICK +
     "EXACTLY TWO sticks of cartoon dynamite bound together side by side into a "
     "small bundle with one dark strap across the middle, the pair tilted a "
     "little to the right, with two short curly fuses coming out of the top "
     "joining into one bright yellow-white spark. Two sticks, not three."),

    ('tnt3', STYLE + GREEN + ICON + STICK +
     "EXACTLY THREE sticks of cartoon dynamite bound together into a bundle "
     "with one dark strap across the middle -- two sticks side by side at the "
     "front and one behind -- tilted a little to the right, with the fuses "
     "coming out of the top joining into one big bright yellow-white spark. "
     "Three sticks, not two and not four."),

    ('heart', STYLE + GREEN + ICON +
     "ONE plump cartoon heart, symmetrical, seen straight on, filling the "
     "frame. Bright warm red with a slightly darker red on the lower right for "
     "the cel shade, a single soft pale-pink highlight up on the top left, and "
     "a thick black outline all the way round. A simple solid heart shape -- no "
     "arrow, no wings, no ribbon, no glow, no cracks, no smaller hearts."),
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
        ref = s.upload(os.path.join(ROOT, 'art', 'mystery_egg.webp'))
        # TWO AT A TIME. Gemini at volume fails on CAPACITY rather than quota
        # and it lands on the END of the queue, so a group of four comes back
        # with the last one empty. Two, drained, then two.
        for i in range(0, len(JOBS), 2):
            for name, prompt in JOBS[i:i+2]:
                print('queueing %s ...' % name)
                s.generate(prompt, runs=3, model='Pro', attach=[ref])
            print('  waiting for that pair')
            s.wait()
        lib = s.library()
        n = max(0, len(lib) - before)
        print('%d new items' % n)
    else:
        lib = s.library(); n = 12
    # ONLY WHAT THIS RUN MADE. The library is shared with whatever else is
    # using the Studio, and lib[:12] once dragged down fifteen files of another
    # session's music. Newest first, so the new ones are exactly the front.
    for item in lib[:n]:
        print('  downloaded %s' % s.download(item, OUT))
    print('now run: python tools/cut_icons.py --list')


if __name__ == '__main__':
    main()
