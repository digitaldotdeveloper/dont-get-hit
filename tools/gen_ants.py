# -*- coding: utf-8 -*-
"""Generate the Ant Territory / Ant Empire art through Gemini Studio.

    python tools/gen_ants.py           # queue everything and wait
    python tools/gen_ants.py --fetch   # just pull what is ready
    python tools/gen_ants.py layers    # only that group

Same contract as gen_bg.py and gen_crow.py, and the same two key colours:

  * PARALLAX LAYERS come back on flat MAGENTA #FF00FF, because the game draws
    ONE background wash behind everything and no layer may carry its own. It is
    also why the empire can share a sky-slot with the farm at all: the wash
    changes from blue daylight to warm underground amber across the transition
    while the layers stay exactly what they are.
  * PROPS AND ACTORS come back on flat GREEN #00FF00, cut by connected
    component like every other prop sheet.

THE ONE RULE THAT OVERRIDES THE REFERENCE ART: **the top of the screen stays
open.** Every reference for this world is drawn as a tunnel with a heavy solid
ceiling filling the upper third, and Nugget can fly to the top of the screen --
a roof drawn across it says "you cannot go here" about the exact space the whole
control scheme is about. So the layers are asked for as WALLS AND FLOOR with
roots and structures HANGING INTO frame from above, never closing it. Hanging
things frame the play area; a ceiling forbids it.

Second rule: these are the middle distance, not the foreground. Nothing here is
an obstacle and nothing here should read as one -- the hazards are separate
pieces on their own sheet, and a background that looks solid is a background
that gets flown into."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import sheets                                    # noqa: E402

sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio                                   # noqa: E402

TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '1a64c4bc884692a41e0bf84ed3fb4729a4a650484f264530')
OUT = sheets('v5')

STYLE_BG = ("2D side-scrolling mobile game background art, bold black outlines, flat "
            "cel-shaded colours, clean vector cartoon look, warm and inviting, wide "
            "banner composition, no text, no watermark, no UI, no characters in the "
            "foreground. ")

STYLE_SP = ("2D side-scrolling mobile game sprite art, bold black outlines, flat "
            "cel-shaded colours, clean vector cartoon look, bright and saturated, no "
            "text, no watermark, no logo, no border, no frame, no grid lines. ")

MAGENTA = ("Everything that is not the subject is SOLID FLAT MAGENTA #FF00FF, "
           "completely empty -- no sky, no cave roof, no gradient, no shading, no "
           "shadow and no glow anywhere in the magenta. ")

GREEN = ("The background is SOLID FLAT PURE GREEN #00FF00, completely empty, edge to "
         "edge, with no shadow, no gradient, no ground and no glow spilling onto it. "
         "Nothing green anywhere in the artwork itself. ")

# Said on every layer prompt. The reference art breaks this on every frame.
OPEN_TOP = ("CRITICAL COMPOSITION RULE: the TOP THIRD of the image must be completely "
            "EMPTY MAGENTA. Do NOT draw a cave roof, a ceiling, a rock overhang or a "
            "band of earth across the top. Roots and hanging lanterns may drop DOWN "
            "into the frame from the top edge as separate dangling shapes with clear "
            "empty magenta between and around them, but nothing may close the top "
            "across the width. The player flies through the upper part of this image. ")

LOOPS = ("The left edge and the right edge must match in height and content so the "
         "image can repeat seamlessly side by side, forever. ")

SEPARATE = ("The pictures are clearly separated by wide empty gaps of the flat "
            "background colour and must never touch or overlap each other. ")

GROUPS = {
    # ---------------------------------------------------------------- layers
    'layers': [
        ('ant_far',
         STYLE_BG +
         "FAR DISTANCE LAYER of a huge underground ant city, seen from a long way off. "
         "Rounded earth chambers and arched tunnel mouths at several different heights, "
         "faint warm lantern dots glowing inside them, a few slender bridges strung "
         "between them, all in HAZY DARK BROWN SILHOUETTE with very low contrast and "
         "almost no detail -- this sits far behind everything. The chambers occupy only "
         "the BOTTOM HALF of the image. " + OPEN_TOP + LOOPS + MAGENTA),

        ('ant_mid',
         STYLE_BG +
         "MIDDLE LAYER of a busy underground ant city built in packed earth. A row of "
         "big rounded chambers standing side by side along the bottom edge with clear "
         "gaps between them: a store room stacked with white sugar cubes, a store room "
         "stacked with golden biscuit crumbs, a workshop with a small wooden crane, and "
         "a chamber with a little wooden lift on ropes. Wooden beams and props supporting "
         "the earth, plank walkways at two different heights, warm hanging lanterns. "
         "Saturated warm browns and ambers, clear readable shapes. The buildings occupy "
         "the BOTTOM TWO THIRDS only. " + OPEN_TOP + LOOPS + MAGENTA),

        ('ant_near',
         STYLE_BG +
         "NEAR FOREGROUND LAYER: a bank of rich brown packed earth running along the "
         "BOTTOM of the image only, about one quarter of the image height, with a few "
         "round ant tunnel holes bored into it, pale tree roots threading through it, "
         "small clusters of glowing cyan mushrooms and a few loose pebbles. Strong "
         "saturated colour and heavy black outlines -- this is the closest layer and it "
         "moves fastest. Above the earth bank, a few thick pale tree roots hang straight "
         "DOWN from the top edge of the image as separate dangling shapes with wide empty "
         "gaps between them. " + OPEN_TOP + LOOPS + MAGENTA),
    ],

    # ------------------------------------------------------------ transition
    # The set-piece. This is the thing that makes the change of world read as a
    # PLACE you travelled through rather than a crossfade you sat through.
    'gate': [
        ('ant_gate',
         STYLE_SP +
         "ONE enormous ancient tree-root and earth mound with a huge dark tunnel mouth "
         "opening in the middle of it at ground level, wide enough to run into. Massive "
         "gnarled pale-brown roots wrap over and around the opening like a natural arch; "
         "packed red-brown earth between them; a few green leafy sprigs on the roots at "
         "the top. Deep inside the tunnel mouth a WARM GOLDEN GLOW and the tiny "
         "silhouettes of distant towers and lanterns, suggesting a big lit city further "
         "in. The mound is WIDER THAN IT IS TALL and its top does not reach the top of "
         "the image. Seen straight on from the side. " + GREEN),

        ('ant_mound',
         STYLE_SP +
         "THREE separate drawings of an ant hill in a row, all the same style and all "
         "standing on flat ground, differing only in size: a small loose cone of crumbly "
         "earth with one tiny hole, a medium one with two holes and a few pebbles, and a "
         "large one the height of a barn door with several holes and small root threads. "
         + SEPARATE + GREEN),

        ('ant_signs',
         STYLE_SP +
         "FOUR separate weathered wooden signboards nailed to short wooden posts, in a "
         "row, all the same style and size, each with a plain empty blank board face and "
         "NO text and NO letters written on it at all -- the boards must be completely "
         "blank. One rectangular, one arrow-shaped pointing right, one square, one wide "
         "and low. Rough sawn planks, visible nails, slightly crooked. " + SEPARATE + GREEN),
    ],

    # ---------------------------------------------------------------- actors
    # Background life. Small, side-on, facing right, on one ground line, so the
    # same cutter that does the cow and the goat can do these.
    'ants': [
        ('ant_walk',
         STYLE_SP +
         "SIX separate drawings of THE SAME single cartoon worker ant in a horizontal "
         "row, strict side view facing RIGHT, all exactly the same size and the same "
         "distance away, all standing on the SAME horizontal ground line at the bottom. "
         "A friendly rounded red-brown ant with three body segments, six legs, two bent "
         "antennae, big white eyes with small dark pupils and a cheerful expression. The "
         "six are the six steps of one walk cycle and differ ONLY in the legs and the "
         "tilt of the body -- same ant, same colours, same face throughout. Nothing on "
         "the ant is green. " + SEPARATE + GREEN),

        ('ant_carry',
         STYLE_SP +
         "FOUR separate drawings of cartoon worker ants in a row, strict side view facing "
         "RIGHT, all the same size and on the SAME horizontal ground line, each carrying "
         "one big object balanced above its head with its front legs: the first a white "
         "sugar cube, the second a golden biscuit crumb, the third a green leaf, the "
         "fourth a single red berry. The load is BIG compared to the ant -- comically "
         "oversized cargo. Same friendly red-brown ant with big white eyes in all four. "
         + SEPARATE + GREEN),

        ('ant_guard',
         STYLE_SP +
         "TWO separate drawings of the same cartoon guard ant in a row, strict side view "
         "facing LEFT, on the same ground line, same size: the first standing at "
         "attention holding a small wooden spear upright, looking bored; the second "
         "startled with the spear tilted and both antennae shot straight up in alarm. A "
         "sturdy dark red-brown ant with a small grey helmet and big white eyes. "
         + SEPARATE + GREEN),
    ],
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    want = args or list(GROUPS)
    jobs = [j for g in want for j in GROUPS.get(g, [])]
    if not jobs:
        raise SystemExit('nothing to do; groups are: %s' % ', '.join(GROUPS))

    s = Studio(TOKEN)
    os.makedirs(OUT, exist_ok=True)

    if '--fetch' not in sys.argv:
        for name, prompt in jobs:
            print('queueing %s ...' % name)
            # 3 takes: a layer that does not loop or a sheet whose cells touch is
            # the normal outcome, not the exception, and picking is cheaper than
            # re-prompting.
            s.generate(prompt, runs=3, model='Pro')
        print('queued %d prompts x3. waiting for the queue to drain...' % len(jobs))
        s.wait()

    lib = s.library()
    print('library has %d items; newest first' % len(lib))
    for item in lib[:len(jobs) * 3]:
        print('  downloaded %s' % s.download(item, OUT))


if __name__ == '__main__':
    main()
