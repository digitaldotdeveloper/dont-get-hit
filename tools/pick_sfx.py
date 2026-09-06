# -*- coding: utf-8 -*-
"""Find the segment of a generated track that best matches a reference profile.

    python tools/pick_sfx.py vroom
    python tools/pick_sfx.py vroom --write

WHY THIS EXISTS. cut_sfx.py finds the LOUDEST gesture and walks back to its
start, which is the right rule when a track contains one attempt at one sound.
It is the wrong rule when the studio hands back sixty seconds containing five
different attempts, because the loudest is routinely the dullest -- a generator
asked for a monster truck reaches for sub-bass, and sub-bass is loud.

The first take generated for the truck measured 77% of its energy below 100Hz
and 2% above 400Hz. The user's own reference recordings measure 0% and 79%. So
"loudest" picked the one segment that sounded least like the thing it was
asked for, and no amount of re-prompting would have fixed a chooser that is
looking at the wrong quantity.

So this scores every window in the track against the SPECTRUM the reference
actually has, and takes the best. The profile lives in REF; it came out of
tools/ref_analyze.py run over the recordings the user supplied, and nothing
from those recordings ships -- only these five numbers."""
import os
import subprocess
import sys
import wave

import numpy as np

FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'audio', 'sfx')
LIB = r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard\library"

BANDS = [(0, 100), (100, 400), (400, 2000), (2000, 8000), (8000, 22050)]

# What a real one measures like. Anything claiming to be an engine is scored
# against this; the ignition is allowed its weight because a starter motor is
# slow and loaded, and the reference ignition genuinely has some.
ENGINE = [0.02, 0.17, 0.40, 0.36, 0.05]
IGNITION = [0.12, 0.40, 0.35, 0.12, 0.01]

# name -> (prompt needle, seconds, target peak, profile, min seconds in)
JOBS = {
    'vroom':      ('Monster truck IGNITION and REV',    2.00, 0.92, IGNITION),
    'truckaccel': ('Monster truck ACCELERATION',        1.10, 0.92, ENGINE),
    'truckidle':  ('Monster truck IDLING',              2.00, 0.85, ENGINE),
    'kick':       ('KICKING a heavy metal barred door', 0.90, 0.85, None),
    'boom':       ('BOOM',                              1.00, 0.95, None),
    'megg':       ('magical PICKUP chime',              1.40, 0.80, None),
}
LEAD, FADE = 0.030, 0.060


def newest(needle):
    import json
    try:
        idx = json.load(open(os.path.join(LIB, 'index.json'), encoding='utf-8'))
    except Exception:
        return []
    hits = [e for e in idx if needle in (e.get('prompt') or '')]
    hits.sort(key=lambda e: e.get('createdAt', 0), reverse=True)
    out = []
    for e in hits:
        p = os.path.join(LIB, e['file'].replace('/', os.sep))
        if os.path.exists(p):
            out.append(p)
    return out


def mono(src, tmp, sr=22050):
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', src,
                    '-ac', '1', '-ar', str(sr), tmp], check=True)
    with wave.open(tmp, 'rb') as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float)
    return a/32768.0, sr


def bands_of(seg, sr):
    n = 1 << 13
    if len(seg) < n:
        return None
    acc = np.zeros(n//2+1)
    win = np.hanning(n)
    for i in range(0, len(seg)-n, n//2):
        acc += np.abs(np.fft.rfft(seg[i:i+n]*win))**2
    f = np.fft.rfftfreq(n, 1.0/sr)
    tot = acc.sum()
    if tot <= 0:
        return None
    return [acc[(f >= lo) & (f < min(hi, sr/2))].sum()/tot for lo, hi in BANDS]


def main():
    write = '--write' in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith('--')]
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_pick.wav')
    for name, (needle, secs, peak, prof) in JOBS.items():
        if want and name not in want:
            continue
        srcs = newest(needle)
        if not srcs:
            print('  %-11s no render yet' % name)
            continue
        best = None
        for src in srcs[:4]:            # every take, not just the newest
            a, sr = mono(src, tmp)
            W, H = int(secs*sr), int(0.10*sr)
            for i in range(0, max(1, len(a)-W), H):
                seg = a[i:i+W]
                rms = float(np.sqrt((seg**2).mean()))
                if rms < 0.02:
                    continue
                b = bands_of(seg, sr)
                if b is None:
                    continue
                if prof:
                    # distance from the reference's shape, plus a nudge towards
                    # louder takes so a quiet perfect match does not win
                    d = sum(abs(x-y) for x, y in zip(b, prof)) - 0.25*min(rms*4, 1)
                else:
                    d = -rms          # no profile: loudest wins, as before
                if best is None or d < best[0]:
                    best = (d, src, i/float(sr), b, rms)
        if not best:
            print('  %-11s nothing usable' % name)
            continue
        d, src, at, b, rms = best
        print('  %-11s %s  @%5.2fs  score %.3f' % (name, os.path.basename(src)[:34], at, d))
        print('              bands ' + ' '.join('%2.0f%%' % (100*x) for x in b) +
              ('   want ' + ' '.join('%2.0f%%' % (100*x) for x in prof) if prof else ''))
        if not write:
            continue
        start = max(0.0, at - LEAD)
        for ext, args in (('.ogg', ['-c:a', 'libopus', '-b:a', '96k']),
                          ('.mp3', ['-c:a', 'libmp3lame', '-b:a', '128k'])):
            dst = os.path.join(OUT, name + ext)
            subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y',
                            '-ss', '%.3f' % start, '-t', '%.3f' % secs, '-i', src,
                            '-af', 'afade=t=in:st=0:d=0.012,'
                                   'afade=t=out:st=%.3f:d=%.3f,'
                                   'dynaudnorm=p=%.2f:m=1:s=0'
                                   % (max(0, secs-FADE), FADE, peak)]
                           + args + [dst], check=True)
            print('              %-15s %5d KB' % (name+ext, os.path.getsize(dst)//1024))
    if not write:
        print('  dry run: pass --write')


if __name__ == '__main__':
    main()
