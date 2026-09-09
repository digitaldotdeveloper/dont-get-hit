# -*- coding: utf-8 -*-
"""Turn one of the generated alien takes into the saucer's looping track.

    python tools/cut_ufo_music.py             # measure all three takes
    python tools/cut_ufo_music.py --write     # ...and ship the best-looping one
    python tools/cut_ufo_music.py --take 2 --write

THE SEAM IS THE ONLY THING THAT MATTERS, and it is the lesson the menu track
taught the hard way: it shipped with ~100ms of digital silence at the front and
looped every 24 seconds, so every time round you heard music -> gap -> music.
"Cut on the loop period" sounds like it implies gapless and does not.

So: trim the leading and trailing silence by finding the first and last samples
that carry level, cut LEN seconds from there, and then MEASURE the join -- the
RMS of the first 60ms against the last 60ms of the slice. A take that fades out
at the end or creeps in at the front shows up as a lopsided ratio, and that is
exactly the breath the menu track had.

Which take ships is chosen on that number rather than on taste, because taste
cannot be applied to three files nobody can listen to from here. `--take` is
there for when somebody can.

Encoding matches tools/opt_audio.py and tools/cut_ride_music.py -- Opus 64k,
MP3 96k for Safari older than 17.4 -- because a third format is a third thing
to keep in sync and MUS_EXT only knows about two.
"""
import array
import json
import os
import subprocess
import sys
import wave

FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(ROOT, 'audio')
LIB = r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard\library"
NEEDLE = 'FLYING SAUCER ABDUCTION LOOP'
NAME = 'music_ufo'
HEAD_DB = 0.02          # level that counts as "the music has started"
LEN = 30.0              # a ride is short; a loop that repeats is the right shape
TMP = os.environ.get('TEMP', '.')
"""LEVELLED AGAINST THE TRACK IT REPLACES, not against nothing.

   Cut raw, this take came out at RMS 6051 where music_ride and music_ride_b
   sit at 5512 and 5261 -- about a decibel hot. That is small, and it is
   exactly the size of error that makes one vehicle feel louder than the other
   without anybody being able to say why, because both play through the SAME
   element at the SAME 0.60. So it is measured off the mean of the two tracks
   it shares that slot with and applied here, at the cut, rather than by
   re-encoding the finished file into a second generation of artefacts."""
GAIN = 0.89             # 5387 / 6051


def takes():
    idx = json.load(open(os.path.join(LIB, 'index.json'), encoding='utf-8'))
    hits = [e for e in idx if NEEDLE.lower() in (e.get('prompt') or '').lower()]
    if not hits:
        raise SystemExit('no alien takes found -- run tools/gen_ufo_music.py')
    hits.sort(key=lambda e: e.get('createdAt', 0))
    return [os.path.join(LIB, e['file'].replace('/', os.sep)) for e in hits]


def to_wav(src, dst, sr=22050):
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', src,
                    '-ac', '1', '-ar', str(sr), dst], check=True)


def samples(path):
    with wave.open(path, 'rb') as w:
        sr, n = w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    a = array.array('h')
    a.frombytes(raw)
    return a, sr


def live_span(path):
    """First and last moment that actually carries level, as float seconds."""
    a, sr = samples(path)
    win = sr // 40                                   # 25ms
    peak = max(abs(v) for v in a) or 1
    first = last = None
    for i in range(0, len(a) - win, win):
        if max(abs(v) for v in a[i:i+win]) / float(peak) > HEAD_DB:
            if first is None:
                first = i / float(sr)
            last = (i + win) / float(sr)
    return (first or 0.0), (last or (len(a) / float(sr))), len(a) / float(sr)


def rms(xs):
    return (sum(v*v for v in xs) / max(1, len(xs))) ** 0.5


def measure(src, n):
    tmp = os.path.join(TMP, '_ufo%d.wav' % n)
    to_wav(src, tmp)
    a, b, total = live_span(tmp)
    dur = min(LEN, b - a)
    seam = os.path.join(TMP, '_ufo%d_slice.wav' % n)
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y',
                    '-ss', '%.3f' % a, '-t', '%.3f' % dur, '-i', src,
                    '-ac', '1', '-ar', '22050', seam], check=True)
    sl, sr = samples(seam)
    win = int(sr*0.06)
    head, tail = rms(sl[:win]), rms(sl[-win:])
    ratio = (tail/head) if head else 0.0
    # 1.0 is a perfect join; score how far off it is in either direction
    off = abs(1.0 - ratio) if ratio else 9.9
    print('  take %d  %s' % (n, os.path.basename(src)[:52]))
    print('           total %5.2fs   music %5.2f..%5.2f   loop %5.2fs' % (total, a, b, dur))
    print('           level RMS %5.0f   seam head %5.0f tail %5.0f  ratio %.2f%s'
          % (rms(sl), head, tail, ratio, '' if 0.45 < ratio < 2.2 else '   <-- BREATHES'))
    return {'src': src, 'a': a, 'dur': dur, 'off': off, 'n': n}


def main():
    write = '--write' in sys.argv
    pick = None
    if '--take' in sys.argv:
        pick = int(sys.argv[sys.argv.index('--take') + 1])
    found = takes()
    print('%d takes' % len(found))
    got = [measure(s, i + 1) for i, s in enumerate(found)]
    best = next((g for g in got if g['n'] == pick), None) or min(got, key=lambda g: g['off'])
    print('  -> take %d loops closest (off by %.2f)' % (best['n'], best['off']))
    if not write:
        print('  dry run: pass --write')
        return
    os.makedirs(AUD, exist_ok=True)
    for ext, args in (('.ogg', ['-c:a', 'libopus', '-b:a', '64k']),
                      ('.mp3', ['-c:a', 'libmp3lame', '-b:a', '96k'])):
        out = os.path.join(AUD, NAME + ext)
        subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y',
                        '-ss', '%.3f' % best['a'], '-t', '%.3f' % best['dur'],
                        '-i', best['src'], '-af', 'volume=%.3f' % GAIN]
                       + args + [out], check=True)
        print('  wrote    %-22s %5d KB' % (NAME + ext, os.path.getsize(out) // 1024))


if __name__ == '__main__':
    main()
