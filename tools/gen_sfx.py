# -*- coding: utf-8 -*-
"""Generate the pickup and vehicle stings through Gemini Studio.

    python tools/gen_sfx.py            # queue and wait
    python tools/gen_sfx.py --fetch    # pull what is ready

READ THIS BEFORE ASSUMING IT WILL WORK.

Every other sound in this game is SYNTHESISED in WebAudio -- a few oscillators
and a noise burst per entry in `S` -- which is why the whole game is one HTML
file with no audio assets and why every sound starts on the exact frame it is
asked for. These three are generated instead, on request, and that is a real
trade:

  * Gemini's audio mode returns roughly THIRTY SECONDS whatever you ask for
    (see project-gemini-studio). A game sting is a fifth of a second, so the
    attack has to be found and cut out of the front of a track -- tools/cut_sfx.py
    does that, and what it finds is a fragment of music, not a designed effect.
  * WORDING IS EVERYTHING. "sound effect" comes back as a written Foley RECIPE
    with no audio at all; "music sting" and "loop" come back as audio. So these
    prompts all say sting, and they describe the SHAPE of the sound -- attack,
    body, tail -- because that is the part a music model can actually hit.
  * A sample costs a fetch, a decode and a buffer the synth version does not.

So this is worth doing for the three BIG moments -- a mystery pickup, a vehicle
arriving, a vehicle launching -- where a richer sound earns its bytes, and is
not worth doing for a footstep."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import sheets                                    # noqa: E402

sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio                                   # noqa: E402

TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '1a64c4bc884692a41e0bf84ed3fb4729a4a650484f264530')
OUT = sheets('sfx')

SHAPE = ("Cartoon mobile game audio. Bright, clean, punchy, arcade. No speech, no "
         "voice, no singing, no lyrics. ")

JOBS = [
    ('mystery_egg',
     SHAPE +
     "A short magical REWARD STING for collecting a rare glowing mystery egg in a "
     "cartoon game. It starts with a soft bright chime, rises quickly through a "
     "sparkling arpeggio, and lands on one warm triumphant bell note that rings "
     "out and fades. Golden, magical, surprising, delighted. The whole gesture is "
     "over in about one second and then there is silence."),

    ('truck_get',
     SHAPE +
     "A short POWER-UP STING for climbing into a monster truck in a cartoon game. "
     "It starts with a heavy mechanical clunk, then a rising engine growl that "
     "revs up and settles into a confident low rumble, with a bright brass-like "
     "fanfare stab on top. Big, heavy, comedic, exciting. The whole gesture is "
     "over in about one and a half seconds and then there is silence."),

    ('truck_jump',
     SHAPE +
     "A short LAUNCH STING for a monster truck leaping off the ground in a cartoon "
     "game. It starts with a deep suspension thump, then a fast upward whoosh with "
     "a springy boing in it, ending on a light airborne shimmer. Bouncy, heavy but "
     "comic, full of lift. The whole gesture is over in about one second and then "
     "there is silence."),
]


# The ride's own music. This one plays to the generator's actual strength --
# it returns ~30 seconds of music whatever you ask for, which is a nuisance for
# a sting and exactly right for a loop.
#
# The user's reference is a specific commercial track (Godsmack, "Cryin' Like a
# Bitch") and it is used the same way the art references were: as DIRECTION,
# never to reproduce. So the prompt asks for the qualities -- the tempo, the
# palm-muted riff, the drum feel, the swagger -- and names no artist and no
# song, because the point is that the truck sounds enormous, not that it sounds
# like somebody else's record.
MUSIC = [
    ('truck_ride_metal',
     "An original instrumental HEAVY METAL riff loop for a cartoon game power-up "
     "sequence. Down-tuned palm-muted electric guitar chugging in a tight "
     "syncopated groove, big punchy rock drums with a driving kick and a cracking "
     "snare backbeat, heavy bass locked to the guitar. Mid-tempo, around 100 BPM, "
     "swaggering and confident rather than angry or dark. Bold, fun, arcade, "
     "larger than life -- the sound of a chicken driving a monster truck through "
     "an ant city. Instrumental only: no vocals, no singing, no speech. It should "
     "loop cleanly and keep the same riff throughout."),
]
# STINGS ARE NOT GENERATED ANY MORE -- see "How a sound gets made" in
# _CONTINUE-HERE.md. The prompts above are kept because they are an accurate
# record of what was tried and why it lost, not because they should be run:
# the studio returns a track, a game wants a gesture, and every entry in `S` is
# synthesised. `music` is the exception, and the only group run by default.
GROUPS = {'music': MUSIC, 'stings-DEPRECATED': JOBS}


def main():
    which = [a for a in sys.argv[1:] if not a.startswith('--')]
    global JOBS
    JOBS = [j for g in (which or ['music']) for j in GROUPS.get(g, [])]
    if not JOBS:
        raise SystemExit('groups: ' + ', '.join(GROUPS))
    s = Studio(TOKEN)
    os.makedirs(OUT, exist_ok=True)
    if '--fetch' not in sys.argv:
        for name, prompt in JOBS:
            print('queueing %s ...' % name)
            # 2 takes: audio jobs are slow (minutes each) and a sting either has
            # the shape or it does not -- there is less to pick between than
            # with a picture.
            s.generate(prompt, runs=2, mode='music')
        print('queued %d prompts x2. audio takes minutes each; waiting...' % len(JOBS))
        s.wait()
    lib = s.library(kind='audio')
    print('library has %d audio items; newest first' % len(lib))
    for item in lib[:len(JOBS) * 2]:
        print('  downloaded %s' % s.download(item, OUT))


if __name__ == '__main__':
    main()
