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
    # THESE FIVE ARE THE USER'S OWN WORDS, pasted in as given on 2026-09-06,
    # one per moment of the truck. Two notes on what was added and why nothing
    # else was:
    #
    # "CARTOON" IS BACK, because the user put it back. It was banned earlier
    # the same day after the truck came back lame, and then they wrote these
    # five themselves and asked for cartoonish, exaggerated, humorous. Their
    # brief wins over an inference drawn from an earlier complaint -- and the
    # complaint was really about a sub-bass hum, which is a different problem
    # and is being solved by measurement instead (see tools/pick_sfx.py).
    #
    # THE LEAD-IN IS NOT DECORATION. Every prompt starts by naming itself a
    # MUSIC STING (or MUSIC BED), because the studio's router only hands a
    # request to the audio model when it reads as one. Without it Gemini
    # replies "I cannot generate the actual audio file for you, but..." and
    # writes a Foley recipe in words. The user's text is otherwise untouched.

    ('sfx_truckget',
     "Short punchy MUSIC STING for an arcade video game. "
     "Create a short, punchy arcade video-game monster truck ignition sound. "
     "The sound starts with a quick mechanical transformation/activation "
     "moment, followed immediately by a powerful chunky engine ignition. Use a "
     "deep low-frequency \"BRR-RR-ROOOM\" engine roar with a playful "
     "exaggerated arcade character. It should feel exciting, satisfying, and "
     "slightly ridiculous, matching the humorous cartoon tone of Don't Get Hit. "
     "Very short: approximately 1-1.5 seconds. Strong impact at the beginning, "
     "then a brief engine roar. No music, no ambience, no voice, no realistic "
     "cinematic effects. Style: polished mobile arcade game SFX, exaggerated, "
     "energetic, cartoonish, punchy, satisfying. Think of the tight, exaggerated "
     "vehicle sound design of classic arcade mobile games, but create an "
     "original sound rather than copying any existing game audio."),

    ('sfx_truckidle',
     "Seamless looping MUSIC BED for an arcade video game. "
     "Create a seamless looping monster truck driving engine sound for a "
     "fast-paced cartoon mobile arcade game. A chunky, powerful engine "
     "continuously running at medium-high RPM. The engine should have a deep "
     "\"BRR-BRR-BRRR\" character with subtle mechanical vibration and rhythmic "
     "exhaust pulses. Make it feel like a ridiculously oversized monster truck, "
     "but keep it playful and exaggerated rather than realistic. The loop must "
     "be seamless with no obvious beginning or ending. Approximately 3-5 "
     "seconds. Consistent RPM and volume so it can loop continuously while the "
     "player drives. No music, no tires squealing, no environment, no voices. "
     "Style: energetic arcade game SFX, cartoonish, punchy, humorous, polished "
     "mobile game audio."),

    ('sfx_truckjump',
     "Short punchy MUSIC STING for an arcade video game. "
     "Create a short arcade video-game sound effect for a monster truck "
     "launching into the air. Start with a quick engine rev and acceleration "
     "\"VRRROOOM\", followed by a powerful upward mechanical surge as the truck "
     "leaves the ground. Add a subtle cartoonish whoosh to emphasize the jump. "
     "The sound should make the jump feel exciting, powerful, and fun rather "
     "than realistic. Approximately 0.7-1.2 seconds. Strong initial engine "
     "burst, fast upward whoosh, clean ending. No landing sound. Style: "
     "exaggerated cartoon arcade game SFX, punchy, energetic, satisfying, "
     "polished mobile game audio."),

    ('sfx_truckboost',
     "Short punchy MUSIC STING for an arcade video game. "
     "Create a short arcade video-game acceleration sound for a monster truck "
     "while it is airborne. Use a rapidly rising engine pitch: \"VRRRRROOOOM!\" "
     "with increasing RPM and a strong feeling of acceleration. Add a subtle "
     "exaggerated air-rush/rocket-like whoosh underneath the engine without "
     "making it sound like a spaceship. The sound should communicate: MORE "
     "SPEED, MORE POWER, GO! Approximately 0.5-1 second. Very energetic, rising "
     "pitch, punchy and satisfying. No music, no voice, no landing sound. "
     "Style: humorous cartoon arcade game, exaggerated monster truck, polished "
     "mobile game SFX."),

    ('sfx_truckland',
     "Short punchy MUSIC STING for an arcade video game. "
     "Create a short, extremely satisfying cartoon monster truck landing sound "
     "for a mobile arcade game. The truck hits the ground with a heavy but "
     "playful \"THUD-BOOM\", followed by a brief suspension bounce and chunky "
     "mechanical rattle. Make the impact feel powerful without sounding like a "
     "crash or destruction. Approximately 0.4-0.8 seconds. Strong low-end "
     "impact followed by a tiny mechanical bounce. No engine loop, no music, no "
     "voice. Style: exaggerated cartoon arcade game SFX, chunky, funny, "
     "powerful, polished and satisfying."),

    ('sfx_kick',
     "A boot KICKING a heavy metal barred door, as a short punchy MUSIC STING. "
     "A rubbery windup whoosh, a huge hollow clang of a foot slamming into "
     "steel bars, and the bars ringing and a chain jangling loose after it. "
     "Exaggerated and oversized, slapstick rather than realistic -- the door is "
     "losing. No speech, no music, no melody. It happens once, lasting about "
     "one second, then silence."),

    ('sfx_megg',
     "A magical PICKUP chime, as a short punchy MUSIC STING. A bright sparkling "
     "twinkle rising quickly through a few happy notes and landing on one warm "
     "ringing bell that fades out. Golden, delighted, rewarding. No speech, no "
     "singing, no words. It happens once, lasting about one and a half seconds, "
     "then silence."),
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
          'truck': _pick('sfx_truckget', 'sfx_truckidle', 'sfx_truckjump',
                         'sfx_truckboost', 'sfx_truckland')}
# ...and one group per sound, so a run can ask for exactly one thing
for _n in ('truckget', 'truckidle', 'truckjump', 'truckboost', 'truckland',
           'kick', 'megg'):
    GROUPS[_n] = _pick('sfx_' + _n)


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
