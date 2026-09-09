# -*- coding: utf-8 -*-
"""Turn a generated vehicle take into that vehicle's looping track.

    python tools/cut_veh_music.py             # measure every take there is
    python tools/cut_veh_music.py --write     # ...and ship the best of each

The generalised `cut_ufo_music.py`: same measurements, six vehicles, and one
extra thing it had to learn.

MUSIC MODE SOMETIMES HANDS BACK THE VIDEO. A generated track is a
`<generated-music>` block wrapping a `<video>`, and the MP3 only exists behind
its own "Audio only" download entry -- so when that entry is slow or missing,
what lands in the library is a 1.4 MB .mp4 of the cover art with the music in
it. Which is fine: ffmpeg is already here for the encode, and pulling a stream
out of a container is the one thing it is unambiguously good at. Three of the
four takes arrived that way and nothing about the audio is different.

THE SEAM IS STILL THE ONLY THING THAT MATTERS, and it is still measured rather
than hoped for -- see the note in cut_ufo_music.py about the menu track that
breathed every 24 seconds because "cut on the loop period" sounds like it
implies gapless and does not.

Each track is also LEVELLED against `music_ride`, because every vehicle plays
through the same element at the same 0.60 and a decibel of difference would
make one vehicle feel louder than another with nobody able to say why.
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
TMP = os.environ.get('TEMP', '.')
HEAD_DB = 0.02
LEN = 30.0
# The reference the whole set is levelled to: the trolley's first riff, which
# every vehicle's music sits beside in the same slot.
TARGET_RMS = 5400.0

VEHICLES = ['rocket', 'hopper', 'spoon', 'toaster']


def takes(veh):
    idx = json.load(open(os.path.join(LIB, 'index.json'), encoding='utf-8'))
    needle = ('DGH VEHICLE LOOP %s' % veh).lower()
    hits = [e for e in idx if needle in (e.get('prompt') or '').lower()]
    hits.sort(key=lambda e: e.get('createdAt', 0))
    return [os.path.join(LIB, e['file'].replace('/', os.sep)) for e in hits]


def to_wav(src, dst, sr=22050):
    """`-vn` because half of these are videos. Everything else is identical."""
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', src,
                    '-vn', '-ac', '1', '-ar', str(sr), dst], check=True)


def samples(path):
    with wave.open(path, 'rb') as w:
        sr, n = w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    a = array.array('h')
    a.frombytes(raw)
    return a, sr


def rms(xs):
    return (sum(v*v for v in xs)/max(1, len(xs))) ** 0.5


def live_span(path):
    a, sr = samples(path)
    win = sr // 40
    peak = max(abs(v) for v in a) or 1
    first = last = None
    for i in range(0, len(a) - win, win):
        if max(abs(v) for v in a[i:i+win])/float(peak) > HEAD_DB:
            if first is None:
                first = i/float(sr)
            last = (i + win)/float(sr)
    return (first or 0.0), (last or (len(a)/float(sr))), len(a)/float(sr)


def measure(veh, src, n):
    """THE START OF THE LOOP IS SEARCHED FOR, not assumed to be the start of
       the music. Cutting the first 30 seconds gave the rocket a seam ratio of
       2.30 -- the slice happened to open quiet and close loud, so every time
       round it fell off a cliff. The generator hands back a minute or more, so
       there is a whole track's worth of other places to start.

       Decode ONCE and slide the window over the samples: 60ms of head against
       60ms of tail at every half-second offset, best ratio wins. Doing it by
       re-encoding each candidate would be a hundred ffmpeg runs; doing it in
       the array is instant and answers exactly the same question."""
    tmp = os.path.join(TMP, '_vm%s%d.wav' % (veh, n))
    to_wav(src, tmp)
    a, b, total = live_span(tmp)
    sl, sr = samples(tmp)
    win = int(sr*0.06)
    dur = min(LEN, b - a)
    best = None
    step = int(sr*0.5)
    for st in range(int(a*sr), max(int(a*sr) + 1, int((b - dur)*sr)), step):
        en = st + int(dur*sr)
        if en > len(sl): break
        head, tail = rms(sl[st:st+win]), rms(sl[en-win:en])
        if not head: continue
        off = abs(1.0 - tail/head)
        if best is None or off < best['off']:
            best = {'off': off, 'at': st/float(sr), 'ratio': tail/head,
                    'rms': rms(sl[st:en])}
    if best is None:
        best = {'off': 9.9, 'at': a, 'ratio': 0.0, 'rms': rms(sl)}
    print('  %-8s take %d  %s' % (veh, n, os.path.basename(src)[-26:]))
    print('           total %5.2fs  loop %5.2fs from %5.2fs  RMS %5.0f  seam %.2f%s'
          % (total, dur, best['at'], best['rms'], best['ratio'],
             '' if 0.45 < best['ratio'] < 2.2 else '   <-- BREATHES'))
    return {'src': src, 'a': best['at'], 'dur': dur, 'rms': best['rms'],
            'off': best['off'], 'n': n}


def main():
    write = '--write' in sys.argv
    only = sys.argv[sys.argv.index('--only')+1] if '--only' in sys.argv else None
    for veh in VEHICLES:
        if only and only != veh:
            continue
        found = takes(veh)
        if not found:
            print('  %-8s NO TAKES -- run tools/gen_veh_music.py --only %s' % (veh, veh))
            continue
        got = [measure(veh, s, i+1) for i, s in enumerate(found)]
        best = min(got, key=lambda g: g['off'])
        gain = min(2.0, TARGET_RMS/max(1.0, best['rms']))
        print('  -> %-8s take %d, gain %.3f (RMS %.0f -> %.0f)'
              % (veh, best['n'], gain, best['rms'], best['rms']*gain))
        if not write:
            continue
        os.makedirs(AUD, exist_ok=True)
        for ext, args in (('.ogg', ['-c:a', 'libopus', '-b:a', '64k']),
                          ('.mp3', ['-c:a', 'libmp3lame', '-b:a', '96k'])):
            out = os.path.join(AUD, 'music_%s%s' % (veh, ext))
            subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y',
                            '-ss', '%.3f' % best['a'], '-t', '%.3f' % best['dur'],
                            '-i', best['src'], '-vn',
                            '-af', 'volume=%.3f' % gain] + args + [out], check=True)
            print('     wrote %-22s %5d KB' % ('music_%s%s' % (veh, ext),
                                               os.path.getsize(out)//1024))
    if not write:
        print('  dry run: pass --write')


if __name__ == '__main__':
    main()
