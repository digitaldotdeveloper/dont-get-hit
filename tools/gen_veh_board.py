# -*- coding: utf-8 -*-
"""One MOTION REFERENCE BOARD per vehicle, through Gemini Studio.

   The brief in `dgh/ref/veh-brief.txt` asked for "animated image references /
   motion concept outputs that help us see how each vehicle behaves visually in
   motion" -- key poses, progressions, animation beats, motion states.

   These are the PRESENTATION half of that answer. The other half is
   `tools/veh_board.py`, which photographs the vehicles actually moving in the
   real game; between them you get the polished board and the truth, and they
   are different jobs. A generated board cannot know what the physics turned
   out to be, and a screenshot cannot be laid out like a poster.

   THREE THINGS ARE DIFFERENT FROM EVERY OTHER PROMPT IN THIS FOLDER:

   1. **Text is wanted.** Every sprite prompt in this project ends "no text, no
      watermark, no captions" because a caption baked into a sprite is a
      caption in the game. A concept board is not a sprite -- the user's own
      four reference boards are covered in labels -- so this asks for specific
      short ones instead of banning them.
   2. **No key colour.** Nothing here gets cut out, so there is no green screen
      to protect and the board may have a background.
   3. **The vehicle reference is the SHIPPED SPRITE**, not the concept sheet.
      The vehicles exist now; a board drawn off the original concept art would
      illustrate a vehicle that is no longer quite the one in the game.

     python tools/gen_veh_board.py            # all six
     python tools/gen_veh_board.py --only rocket
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import REF, ROOT as GAME, need
sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio

TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '4bb94235c42a41f4eab766c1c8a33de9357d5b60c2164caf')
# THE BOARDS DO NOT SHIP, so they do not live in the game folder. This repo
# holds what the game loads plus the scripts that rebuild it; 5 MB of PNG that
# nothing ever fetches belongs in the Studio archive with every other raw
# generation, which is what `paths.ARCHIVE` is for. `tools/veh_board.py` writes
# its captured sheets alongside them.
OUT = os.path.join(os.path.dirname(REF), 'boards')
NEEDLE = 'DGH MOTION BOARD'

COMMON = (
  "There are TWO attached pictures. The FIRST is the ART STYLE and the PILOT: "
  "copy its bold black outlines, its flat cel-shaded colours and its clean "
  "vector cartoon look, and draw THE SAME chicken throughout -- the same "
  "cream-white chicken in the same teal-green baseball cap, the same black "
  "sunglasses, the same orange beak and the same red comb. Do NOT redesign the "
  "chicken. The SECOND attached picture is THE VEHICLE, exactly as it is: draw "
  "that vehicle and no other, keeping its shape, its colours and every part of "
  "it. "
  "Make a MOTION REFERENCE BOARD for a game studio: one tall portrait poster "
  "on a clean pale background with a subtle grid, laid out as FOUR panels in a "
  "2x2 grid, each panel a rounded card with the vehicle drawn large inside it "
  "and a short bold heading. Between the panels draw curved motion arrows and "
  "speed lines showing the order they happen in. Use big clear cartoon motion "
  "cues -- arcs, trailing swooshes, impact stars, little puffs -- so the "
  "movement reads instantly. Bright, energetic, professional game-concept "
  "presentation art. The only words on the poster are the panel headings and "
  "the title, spelled exactly as given and nothing else. ")


def board(title, panels):
    return (COMMON + 'The title across the top is "' + title + '". ' +
            'The four panels, in reading order, are: ' + panels)

JOBS = {
 'rocket': board("CORN ROCKET - MOTION", (
   "(1) CRUISE -- flying dead level at enormous speed, both engine nozzles "
   "burning long straight jets of orange flame behind it, long horizontal "
   "speed lines. (2) CLIMB -- the whole rocket tilted nose-up about 30 "
   "degrees, flames blazing bigger, a wide curved arc trailing behind showing "
   "it swinging upward slowly. (3) DIVE -- tilted nose-down about 30 degrees, "
   "flames smaller, a long shallow curve behind it. (4) COMMITTED -- the same "
   "rocket drawn small three times in a row along one enormous sweeping curve, "
   "getting further away, showing that it takes a long distance to change "
   "direction. Ghosted faded copies behind the rocket in panels 2 and 3 to "
   "show where it just was.")),

 # THE FIRST TAKE CAME BACK WITH THE TROLLEY IN IT -- right title, right
 # panels, wrong vehicle: the model leaned on the FIRST attachment (which is
 # the style reference, and the style reference IS the trolley) instead of the
 # second. The other five were fine, so it is not the shape of the prompt, it
 # is that this one vehicle is easy to lose. Naming what it is NOT is the
 # cheapest fix, and it is the same trick that keeps Nugget from drifting.
 'hopper': board("EGGSHELL HOPPER - BOUNCE", (
   "IMPORTANT: the vehicle in every panel is the SECOND attached picture -- a "
   "big cracked cream-white EGGSHELL with the chicken sitting inside it, "
   "mounted on top of a grey coil spring on a yellow base plate. It is NOT a "
   "shopping trolley, NOT a car, and it has NO wheels of any kind. "
   
   "(1) FALL -- the eggshell high in the air coming down, the coil spring "
   "underneath stretched long and thin, the chicken's arms up. (2) SQUASH -- "
   "landed, the spring crushed almost flat, the eggshell squashed wide and low, "
   "impact stars and dust puffs at the base. (3) LAUNCH -- the spring snapped "
   "out to full length, the eggshell stretched tall and narrow, flying "
   "upwards, a big puff of dust left on the ground below. (4) PERFECT -- the "
   "same bounce drawn twice side by side for comparison: a small low arc "
   "labelled nothing on the left and a much bigger higher arc on the right, "
   "with a bright starburst on the taller one.")),

 'spoon': board("MAGNET SPOON - FLIP", (
   "(1) FLOOR -- the spoon skimming along the ground the right way up, dust "
   "trailing behind it, its top magnet coil glowing blue. (2) RELEASE -- the "
   "spoon just leaving the ground, crackling blue electric arcs between its "
   "two magnet coils, a big up arrow. (3) CROSSING -- the spoon halfway "
   "between the ground and a ceiling, tilted, drawn along a smooth curved arc "
   "with ghosted faded copies of itself behind it showing the path. (4) "
   "CEILING -- the spoon stuck UPSIDE DOWN to a wooden ceiling at the top of "
   "the panel with the chicken hanging happily underneath it, blue sparks at "
   "the point of contact.")),

 'toaster': board("TOASTER JUMPER - CHARGE", (
   "(1) DRIVE -- the toaster car rolling along the ground, toast slots empty, "
   "small dust puffs behind the tyres. (2) CHARGE -- still on the ground, "
   "hunkered down low and wide, two slices of toast rising halfway out of the "
   "slots, the heating element underneath glowing hot orange, little heat "
   "wiggle lines. (3) POP -- the toast flung high above the machine with a "
   "bright yellow starburst, the whole toaster leaving the ground. (4) ARC -- "
   "the toaster car high in the air along a big curved jump arc with a dashed "
   "trajectory line under it, landing dust drawn at the far end.")),

 'trolley': board("MONSTER TROLLEY - POWER", (
   "(1) DRIVE -- the monster shopping trolley charging along the ground, big "
   "tyres spinning with motion blur arcs, flames spitting from its exhaust "
   "pipes, dust behind. (2) LAUNCH -- front wheels lifted first in a wheelie, "
   "the whole rig nose-up leaving the ground, the chicken's cap flying off, a "
   "wall of dust below. (3) AIR -- at the top of a big jump, drawn along an "
   "arc with a dashed trajectory line. (4) SLAM -- landed hard, suspension "
   "springs crushed flat, the body squashed wide and low, impact stars, a "
   "huge skirt of dust and a burst of flame from the exhaust.")),

 'ufo': board("FRIED EGG UFO - CONTROL", (
   "(1) HOVER -- the flying-saucer hanging level in the air, three short "
   "yellow cone beams pointing down from its underside. (2) RISE -- climbing, "
   "the three beams much longer and brighter, the soft white egg-white rim of "
   "the saucer stretched downward like it is being pulled. (3) SINK -- "
   "descending, the beams short and dim, the white rim wobbling upward. (4) "
   "BEAM -- flying low over a field with a cartoon cow lifted off the ground "
   "inside the yellow beam, legs still running in mid air, small sparkles "
   "rising up the beam.")),
}

SPRITE = {'rocket':'veh_rocket.webp', 'hopper':'veh_hopper.webp',
          'spoon':'veh_spoon.webp', 'toaster':'veh_toaster.webp',
          'trolley':'truck_drive.webp', 'ufo':'ufo.webp'}


def main():
    s = Studio(TOKEN)
    only = sys.argv[sys.argv.index('--only')+1] if '--only' in sys.argv else None
    names = [n for n in JOBS if not only or only == n]
    os.makedirs(OUT, exist_ok=True)
    print('quota before: %s' % s.usage()['current'])
    style = s.upload(os.path.join(GAME, 'art', 'truck_drive.webp'))
    t0 = time.time()
    for n in names:
        veh = s.upload(os.path.join(GAME, 'art', SPRITE[n]))
        print('queueing %s ...' % n)
        s.generate(NEEDLE + ' ' + n.upper() + '. ' + JOBS[n],
                   runs=1, model='Pro', attach=[style, veh])
    while time.time() - t0 < 2400:
        mine = [i for i in s.library()
                if NEEDLE in (i.get('prompt') or '')
                and i.get('createdAt', 0)/1000 > t0 - 60]
        print('  %4ds  %d/%d back' % (time.time()-t0, len(mine), len(names)))
        if len(mine) >= len(names):
            break
        time.sleep(25)
    for it in mine:
        p = s.download(it, OUT)
        which = next((n for n in names
                      if (NEEDLE + ' ' + n.upper()) in (it.get('prompt') or '')), None)
        if which:
            dst = os.path.join(OUT, 'board_%s%s' % (which, os.path.splitext(p)[1]))
            os.replace(p, dst)
            print('   %s' % dst)
        else:
            print('   %s  (unmatched)' % p)


if __name__ == '__main__':
    main()
