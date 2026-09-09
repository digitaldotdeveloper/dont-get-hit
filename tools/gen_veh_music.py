# -*- coding: utf-8 -*-
"""One track per vehicle, through Gemini Studio's music mode.

   Six vehicles now, and the point of giving each one a track is the point of
   giving each one a physics: taking a vehicle changes the whole board, and a
   board that changes while the music does not is telling the player it is the
   same reward wearing a hat. The trolley has two riffs and the saucer has its
   alien loop; these are the other four.

   Every prompt names an INSTRUMENT and a TEMPO rather than a mood, for the
   same reason the art prompts say what the shape is rather than what the mood
   is: "exciting" gets you anything, "fast twangy surf guitar over a shuffle"
   gets you the thing. And every one says "loop", because the wording is what
   routes this mode -- "sound effect" comes back as a written Foley recipe.

     python tools/gen_veh_music.py            # queue all four and wait
     python tools/gen_veh_music.py --only rocket
     python tools/gen_veh_music.py --list
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio

TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '4bb94235c42a41f4eab766c1c8a33de9357d5b60c2164caf')

# The needle each cut script finds its own takes by. It has to be verbatim in
# the prompt and unique in a library shared with several other projects.
def needle(k):
    return 'DGH VEHICLE LOOP %s' % k.upper()

JOBS = {
 'rocket': needle('rocket') + ": a 30 second instrumental music loop for an "
   "arcade game, very fast. Hot-rod surf rock: a loud twangy reverb-drenched "
   "electric guitar playing a fast descending riff, a driving shuffle drum "
   "beat with a heavy tom roll, an upright bass running underneath, and a "
   "banjo doubling the riff so it still sounds like a farm. Relentless "
   "forward momentum, no let-up, no vocals, seamless loop.",

 'hopper': needle('hopper') + ": a 30 second instrumental music loop for a "
   "cartoon game, all about BOUNCE. A tuba playing a springy oom-pah bassline, "
   "pizzicato strings plucking on the offbeat, a woodblock and a slide whistle "
   "marking every bounce, and a xylophone melody hopping up and down in big "
   "intervals. Rhythmic, comic, elastic, medium tempo so the bounces are "
   "countable, no vocals, seamless loop.",

 'spoon': needle('spoon') + ": a 30 second instrumental electronic music loop "
   "for an arcade game. Clean retro electro: a bright pulsing analogue "
   "arpeggio that runs up and then runs down, a fat filtered synth bass, "
   "crisp electronic drums with a rimshot snare, and a short zapping "
   "sweep every few bars like a switch being thrown. Precise, cool, "
   "weightless, no vocals, seamless loop.",

 'toaster': needle('toaster') + ": a 30 second instrumental music loop for a "
   "comedy cartoon. Honky-tonk ragtime piano playing a bouncy stride pattern, "
   "a muted trumpet answering it, brushed snare, a tuba on the downbeats, and "
   "a comic cymbal choke and a spring-pop sound as punctuation. Cheerful, "
   "silly, vaudeville, medium-fast, no vocals, seamless loop.",
}


def main():
    s = Studio(TOKEN)
    only = sys.argv[sys.argv.index('--only')+1] if '--only' in sys.argv else None
    names = [n for n in JOBS if not only or only == n]
    if '--list' in sys.argv:
        for it in s.library():
            p = (it.get('prompt') or '')
            if 'DGH VEHICLE LOOP' in p:
                print('  %-52s %s' % (it.get('file'), p[:40]))
        return
    print('quota before: %s' % s.usage())
    t0 = time.time()
    for n in names:
        print('queueing %s ...' % n)
        s.generate(JOBS[n], mode='music', model='auto', runs=1)
    while time.time() - t0 < 2400:
        mine = [i for i in s.library()
                if 'DGH VEHICLE LOOP' in (i.get('prompt') or '')
                and i.get('createdAt', 0)/1000 > t0 - 60]
        print('  %4ds  %d/%d back' % (time.time()-t0, len(mine), len(names)))
        if len(mine) >= len(names):
            for it in mine:
                print('   %s' % it.get('file'))
            return
        time.sleep(25)
    print('gave up waiting; --list to see what arrived')


if __name__ == '__main__':
    main()
