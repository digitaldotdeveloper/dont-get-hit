# -*- coding: utf-8 -*-
"""Cut a game sound out of the track Gemini hands back.

    python tools/cut_sfx.py            # report what it found
    python tools/cut_sfx.py --write    # -> audio/sfx/<name>.ogg + .mp3

THE STUDIO RETURNS A TRACK AND A GAME WANTS A GESTURE. Every one of these
prompts asks for "one thing, about a second, then silence" and what comes back
is tens of seconds long with the thing somewhere inside it, usually after a
lead-in and often repeated. So the gesture has to be FOUND, not assumed to be
at the front.

How it is found, and why not more cleverly: take the energy envelope at 5ms,
find the single loudest sample, and walk BACKWARDS to where the sound actually
starts -- the last point before it that was quiet. That start is what matters,
because a sound effect that begins a fifth of a second late reads as lag on
every press. Walking back from the peak beats detecting the first onset,
because the first onset is often a quiet false start the model wandered
through before committing.

Then it is trimmed to `secs`, given a short fade so it cannot click, and
normalised to a target peak -- the takes come back at wildly different levels
and a game needs them to sit together."""
import os
import subprocess
import sys
import wave
import array

FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'audio', 'sfx')
LIB = r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard\library"

# name -> (words that must appear in the prompt, seconds to keep, target peak)
# name -> (words that must appear in the prompt, seconds to keep, target peak)
#
# THE NEEDLES HAVE TO TRACK THE PROMPTS. They are how a render is found again
# in the library, so a prompt rewrite silently orphans every take unless these
# move with it -- which is exactly what happened when "cartoon" came out.
JOBS = {
    'vroom':      ('Monster truck IGNITION and REV',  2.00, 0.92),
    'truckaccel': ('Monster truck ACCELERATION',      1.10, 0.92),
    'truckjump':  ('monster truck LAUNCH',            1.00, 0.90),
    'kick':       ('KICKING a heavy metal barred door', 0.90, 0.85),
    'boom':       ('BOOM',                            1.00, 0.95),
    'megg':       ('magical PICKUP chime',            1.40, 0.80),
}
LEAD = 0.030          # keep this much before the start, so the attack is whole
FADE = 0.060          # out, so the cut cannot click


def newest(needle):
    import json
    try:
        idx = json.load(open(os.path.join(LIB, 'index.json'), encoding='utf-8'))
    except Exception:
        return None
    hits = [e for e in idx if needle in (e.get('prompt') or '')]
    if not hits:
        return None
    hits.sort(key=lambda e: e.get('createdAt', 0), reverse=True)
    for e in hits:
        p = os.path.join(LIB, e['file'].replace('/', os.sep))
        if os.path.exists(p):
            return p
    return None


def envelope(src, tmp):
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', src,
                    '-ac', '1', '-ar', '22050', tmp], check=True)
    with wave.open(tmp, 'rb') as w:
        sr, raw = w.getframerate(), w.readframes(w.getnframes())
    a = array.array('h'); a.frombytes(raw)
    hop = max(1, sr // 200)                      # 5ms
    env = [max(abs(v) for v in a[i:i+hop]) for i in range(0, len(a) - hop, hop)]
    return env, 1.0/200, len(a)/float(sr)


def find_start(env, step):
    """Walk back from the loudest point to where the sound begins."""
    if not env:
        return 0.0
    pk = max(env)
    i = env.index(pk)
    floor = pk*0.06
    j = i
    while j > 0 and env[j] > floor:
        j -= 1
    return max(0.0, j*step)


def main():
    write = '--write' in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith('--')]
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_sfx.wav')
    for name, (needle, secs, peak) in JOBS.items():
        if want and name not in want:
            continue
        src = newest(needle)
        if not src:
            print('  %-10s no render yet' % name)
            continue
        env, step, total = envelope(src, tmp)
        at = find_start(env, step)
        print('  %-10s %5.1fs track, gesture starts %5.2fs, keeping %.2fs'
              % (name, total, at, secs))
        if not write:
            continue
        start = max(0.0, at - LEAD)
        for ext, args in (('.ogg', ['-c:a', 'libopus', '-b:a', '96k']),
                          ('.mp3', ['-c:a', 'libmp3lame', '-b:a', '128k'])):
            dst = os.path.join(OUT, name + ext)
            # loudnorm would pump a one-shot; a peak normalise is what a game
            # wants, so the set sits together without changing any shape
            subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y',
                            '-ss', '%.3f' % start, '-t', '%.3f' % secs, '-i', src,
                            '-af', 'afade=t=out:st=%.3f:d=%.3f,dynaudnorm=p=%.2f:m=1:s=0'
                                   % (max(0, secs - FADE), FADE, peak)]
                           + args + [dst], check=True)
            print('             %-14s %5d KB' % (name + ext, os.path.getsize(dst)//1024))
    if not write:
        print('  dry run: pass --write')


if __name__ == '__main__':
    main()
