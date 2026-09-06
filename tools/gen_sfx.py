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

# THE SOUND EFFECTS ARE GENERATED. This reversed on 2026-09-06 at the user's
# instruction -- "all sounds i ask you about should be gemini studio generated"
# -- and the earlier synthesised versions are gone. What that costs and how it
# is paid: the studio hands back a long track, so tools/cut_sfx.py finds the
# gesture inside it and cuts it out, and the game plays the result as a sample
# through the same sfxGain everything else uses.
#
# TWO PHRASES DECIDE WHETHER YOU GET AUDIO AT ALL, and they are not optional:
# every prompt says "MUSIC STING" (or "MUSIC BED" for a loop), because the
# studio's router only hands a request to the audio model when it reads as a
# music request. Drop it and Gemini replies "I cannot generate the actual audio
# file for you, but..." -- in words, as a Foley recipe. This was learned, then
# lost during the 2026-09-06 rewrite that stripped "cartoon", then learned
# again from the failure log. Strip the genre words, keep the routing words.
#
# WORDING IS STILL EVERYTHING. "sound effect" comes back as a written Foley
# RECIPE with no audio at all; asking for a short piece of AUDIO with a
# described shape comes back as audio. So each prompt below describes the
# gesture -- attack, body, tail -- and then the MACHINE or the material making
# it, in physical terms. What it must never do is name the genre: see the note
# on "cartoon" below.
JOBS = [
    # THE REFERENCES WERE MEASURED, NOT GUESSED AT. The user supplied three
    # recordings of a real monster truck; tools/ref_profile.json holds what
    # came out of them, and the single most useful fact is that a big engine
    # heard from outside has ALMOST NO BASS -- 0% of its energy below 100Hz,
    # 40% in 400-2000 and another 38% above that. Its fundamental is nearly
    # absent and its FIFTH HARMONIC is the loudest thing in it. So the prompts
    # ask for raspy, cracking, midrange bark rather than the deep rumble that
    # the word "monster" pulls a generator towards, because deep rumble is
    # exactly the wrong answer and is what made the first attempt lame.
    # NO "CARTOON", NO "KIDS". The user cut both words on 2026-09-06 after the
    # truck came back lame, and they were the cause rather than a detail: ask a
    # generator for a cartoon engine and it hands you a comedy parp, because
    # that is what the word means to it. The game IS stylised, but the SOUND
    # has to be real -- an enormous, genuinely frightening engine is what makes
    # a chicken driving one funny. Describe the machine, not the genre.
    #
    # THE REFERENCES WERE MEASURED, NOT COPIED. The user supplied three
    # recordings of a real monster truck as direction; nothing from them ships.
    # The single most useful fact out of them is that a big engine heard from
    # outside has ALMOST NO BASS: 0% of its energy below 100Hz, ~40% in
    # 400-2000 and another ~38% above that, its fundamental nearly absent and
    # its FIFTH HARMONIC the loudest thing in it. So these ask for raspy,
    # cracking, midrange bark -- and explicitly rule out the deep smooth rumble
    # that "monster" otherwise pulls a generator straight towards.
    ('sfx_vroom',
     "Monster truck IGNITION and REV, as a short punchy MUSIC STING. A huge V8 "
     "starter motor cranking a couple "
     "of heavy slow turns, the engine CATCHING with a hard bark, then revving up "
     "into a loud raspy roar that holds. Close outside recording: raw, violent, "
     "cracking, midrange-forward with a savage exhaust rasp -- NOT a deep smooth "
     "bass rumble, the bite is in the middle and the top. Individual cylinder "
     "beats clearly audible while it is slow, blurring into a snarl as it opens "
     "up. "
     "Recorded on a phone from about ten feet away outdoors, so it is thin and "
     "bright and cutting with NO deep sub-bass at all -- all the energy is in "
     "the midrange and the treble. "
     "Tuned low, in the key of D, so it sits under a down-tuned heavy metal "
     "guitar riff. No speech, no music, no melody, no singing. It happens once, "
     "lasting about two seconds, then silence."),

    ('sfx_truckaccel',
     "Monster truck ACCELERATION, as a short punchy MUSIC STING. A running V8 "
     "with the throttle stamped flat to "
     "the floor: revs climbing fast and hard, exhaust cracking and tearing as it "
     "opens up, ending high and snarling. "
     "Recorded on a phone from about ten feet away outdoors, so it is thin and "
     "bright and cutting with NO deep sub-bass at all -- all the energy is in "
     "the midrange and the treble. "
     "Close outside recording, raw and "
     "midrange-forward with heavy grit and bite -- NOT a deep smooth rumble. In "
     "the key of D so it sits under a down-tuned heavy metal riff. No speech, no "
     "music, no melody. It happens once, lasting about one second, then silence."),

    ('sfx_truckidle',
     "Monster truck IDLING and driving steadily, as a looping MUSIC BED. A huge "
     "V8 turning over at a low "
     "steady rate, lumpy and uneven, each cylinder beat audible and cracking, "
     "with a raspy exhaust note over it. Close outside recording, raw and "
     "midrange-forward rather than a deep smooth rumble. Completely steady in "
     "level and speed throughout with no revving up or down, so it can loop. In "
     "the key of D. No speech, no music, no melody."),

    ('sfx_kick',
     "A boot KICKING a heavy metal barred door, as a short punchy MUSIC STING. A "
     "rubbery windup whoosh, a huge "
     "hollow clang of a foot slamming into steel bars, and the bars ringing and "
     "a chain jangling loose after it. Exaggerated and oversized, slapstick "
     "rather than realistic -- the door is losing. No speech, no music, no "
     "melody. It happens once, lasting about one second, then silence."),

    ('sfx_boom',
     "A big BOOM, as a short punchy MUSIC STING. A bright cracking explosion with "
     "a deep whump under it "
     "and debris clattering down after -- the harmless oversized kind that makes "
     "a cloud and a few stars, not a realistic detonation. Big, silly, "
     "satisfying. No speech, no music, no melody. It happens once, lasting about "
     "one second, then silence."),

    ('sfx_megg',
     "A magical PICKUP chime, as a short punchy MUSIC STING. A bright sparkling "
     "twinkle rising quickly through "
     "a few happy notes and landing on one warm ringing bell that fades out. "
     "Golden, delighted, rewarding. No speech, no singing, no words. It happens "
     "once, lasting about one and a half seconds, then silence."),
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
     "An original instrumental HEAVY METAL riff loop for a game power-up "
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
          'accel-only': _pick('sfx_truckaccel'),
          'idle-only':  _pick('sfx_truckidle'),
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
