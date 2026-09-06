# -*- coding: utf-8 -*-
"""Generate the game's sound effects and music through Gemini Studio.

    python tools/gen_sfx.py            # the sfx set
    python tools/gen_sfx.py music      # the ride's riff
    python tools/gen_sfx.py --fetch    # pull what is ready

EVERY SOUND THE USER ASKS FOR IS GENERATED HERE. Two things about the studio
shape everything below, and both cost real time to learn:

  * IT RETURNS A TRACK, NOT A GESTURE -- 30 seconds when this was first written
    up, 175 the last time it ran. tools/cut_sfx.py finds the gesture inside and
    cuts it out; nothing here is usable as it arrives.
  * WORDING DECIDES WHETHER YOU GET AUDIO AT ALL. "sound effect" comes back as
    a written Foley RECIPE. Asking for a short piece of AUDIO with a described
    shape -- attack, body, tail -- comes back as audio.

Capacity failures land on whatever is LAST in a queue, so ask for few things at
a time and check `--list` for what actually arrived rather than trusting the
exit code."""
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

# THE SOUND EFFECTS ARE GENERATED. This reversed on 2026-09-06 at the user's
# instruction -- "all sounds i ask you about should be gemini studio generated"
# -- and the earlier synthesised versions are gone. What that costs and how it
# is paid: the studio hands back a long track, so tools/cut_sfx.py finds the
# gesture inside it and cuts it out, and the game plays the result as a sample
# through the same sfxGain everything else uses.
#
# WORDING IS STILL EVERYTHING. "sound effect" comes back as a written Foley
# RECIPE with no audio at all; asking for a short piece of AUDIO with a
# described shape comes back as audio. So each prompt below describes the
# gesture -- attack, body, tail -- and says cartoon, because that is the note
# that keeps it in the game's world rather than in a film.
JOBS = [
    ('sfx_vroom',
     "Cartoon monster truck engine REV, as a short punchy MUSIC STING for a "
     "kids arcade game. A big heavy V8 catching with a deep chugging idle, then "
     "revving up hard into a loud throaty roar, with the engine lumps clearly "
     "audible as separate beats before they blur together. Comically oversized, "
     "boisterous, fun. Deep and bassy but bright and clear at the top so it cuts "
     "through music. No speech, no music, no melody, no singing. It happens once, "
     "lasting about one and a half seconds, then silence."),

    ('sfx_truckjump',
     "Cartoon monster truck LAUNCH, as a short punchy MUSIC STING for a kids "
     "arcade game. A heavy suspension thump as the wheels unload, a hard stab of "
     "engine throttle revving up, and a springy comic boing underneath as it "
     "leaves the ground. Heavy, bouncy, silly. No speech, no music, no melody. "
     "It happens once, lasting about one second, then silence."),

    ('sfx_kick',
     "Cartoon KICK against a metal barred door, as a short punchy MUSIC STING "
     "for a kids arcade game. A rubbery windup whoosh, then a big comic thud of "
     "a foot hitting metal, with the bars rattling and a chain jangling after "
     "it. Slapstick, springy, funny -- a cartoon character booting a gate, not a "
     "realistic impact. No speech, no music, no melody. It happens once, lasting "
     "about one second, then silence."),

    ('sfx_boom',
     "Cartoon BOOM, as a short punchy MUSIC STING for a kids arcade game. A "
     "bright comic explosion with a deep whump underneath and a puff of debris "
     "clattering after it -- the sort of harmless cartoon blast that makes a "
     "cloud and a few stars, not a realistic detonation. Big, silly, satisfying. "
     "No speech, no music, no melody. It happens once, lasting about one second, "
     "then silence."),

    ('sfx_megg',
     "Cartoon magical PICKUP chime, as a short punchy MUSIC STING for a kids "
     "arcade game. A bright sparkling twinkle rising quickly through a few happy "
     "notes and landing on one warm ringing bell that fades out. Golden, "
     "delighted, rewarding. No speech, no singing, no words. It happens once, "
     "lasting about one and a half seconds, then silence."),
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
def _pick(*names):
    return [j for j in JOBS if j[0] in names]
# small groups on purpose: a capacity failure takes whatever is at the end of
# the queue, so asking for five at once reliably loses the last three
GROUPS = {'sfx': JOBS, 'music': MUSIC,
          'vroom-only': _pick('sfx_vroom'),
          'kick-only':  _pick('sfx_kick'),
          'boom-only':  _pick('sfx_boom')}


def main():
    which = [a for a in sys.argv[1:] if not a.startswith('--')]
    global JOBS
    JOBS = [j for g in (which or ['sfx']) for j in GROUPS.get(g, [])]
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
