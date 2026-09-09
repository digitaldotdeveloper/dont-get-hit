# -*- coding: utf-8 -*-
"""The saucer's own track, through Gemini Studio's music mode.

   THE TROLLEY HAS TWO RIFFS AND THE SAUCER HAD NEITHER. Taking a vehicle
   changes the whole board, and the one thing this one did not change was the
   soundtrack -- it borrowed the trolley's metal, which is the wrong music by
   the width of the galaxy.

   Three things about this mode cost real probing and are written up in the
   Studio's own `_CONTINUE-HERE.md`; this script obeys all three:

     - **Every track comes back about 30 seconds** whatever length is asked
       for. Fine here: `cut_ufo_music.py` trims it to one clean loop.
     - **The wording is what routes it.** "sound effect" returns a written
       Foley recipe; "loop" and "music" return audio. So: say loop.
     - **`model='auto'`.** Image work pins Pro because Flash will not draw;
       music is the one mode deliberately left alone.

   Three takes, because a loop that plays under a vehicle you meet several
   times a session is worth choosing rather than accepting.

     python tools/gen_ufo_music.py           # queue and wait
     python tools/gen_ufo_music.py --list    # what is already in the library
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio

TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '4bb94235c42a41f4eab766c1c8a33de9357d5b60c2164caf')

# The needle `cut_ufo_music.py` finds these by. It has to appear verbatim in
# every prompt below, and it has to be unique in a library shared with several
# other projects -- "loop" on its own would match the comedy packs.
NEEDLE = 'FLYING SAUCER ABDUCTION LOOP'

JOBS = [
    NEEDLE + ": a 30 second retro sci-fi music loop for a cartoon arcade game. "
    "An eerie wavering theremin lead over a driving surf-rock drum beat and a "
    "bubbling analogue synth arpeggio, with a walking electric bass under it. "
    "Playful and comic rather than frightening -- this is a chicken in a flying "
    "saucer, not a horror film. Upbeat, energetic, instrumental, no vocals, "
    "and it must loop seamlessly.",

    NEEDLE + ": a 30 second 1950s B-movie flying saucer music loop, "
    "instrumental. Theremin and vibraphone trading a spooky melody over "
    "brushed drums and an upright bass walking fast, with little bursts of "
    "analogue bleeps. Comic, bouncy, cartoonish, no vocals, seamless loop.",

    NEEDLE + ": a 30 second alien spaceship chase music loop for a mobile "
    "game. Fast retro synthwave: a wobbling theremin-style lead, a pulsing "
    "arpeggiated bassline, handclaps and a four-on-the-floor kick, plus laser "
    "zaps used as percussion. Energetic and fun, instrumental, no vocals, "
    "loops cleanly.",
]


def main():
    s = Studio(TOKEN)
    if '--list' in sys.argv:
        for it in s.library():
            if NEEDLE.lower() in (it.get('prompt') or '').lower():
                print('  %-46s %s' % (it.get('file'), it.get('jobId')))
        return
    print('quota before: %s' % s.usage())
    for i, prompt in enumerate(JOBS):
        print('queueing take %d ...' % (i + 1))
        s.generate(prompt, mode='music', model='auto', runs=1)
    """The studio is SHARED -- other sessions queue into it -- and `s.wait()`
       waits for the whole queue rather than for these three. So this polls for
       its own renders by the needle instead, and reports rather than blocks
       forever if the tool is having one of its prose-answer days."""
    want, t0 = len(JOBS), time.time()
    while time.time() - t0 < 1500:
        mine = [it for it in s.library()
                if NEEDLE.lower() in (it.get('prompt') or '').lower()]
        print('  %3ds  %d/%d back' % (time.time() - t0, len(mine), want))
        if len(mine) >= want:
            for it in mine[:want]:
                print('   %s' % it.get('file'))
            return
        time.sleep(20)
    print('gave up waiting; --list to see what did arrive')


if __name__ == '__main__':
    main()
