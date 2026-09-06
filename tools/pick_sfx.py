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

# WHAT TO AIM AT, AND WHY IT MOVED. These started as the profile measured off
# the user's real reference recordings -- which have essentially NO bass, 0%
# under 100Hz -- and that was right while the brief was "sound like this truck".
# The brief then changed: the user wrote five prompts of their own asking for a
# deep low-frequency BRR-RR-ROOOM, exaggerated and cartoonish and arcade. A
# real truck and an arcade truck are not the same target, and scoring the
# second against the first would throw away exactly the takes they asked for.
#
# So ARCADE keeps the part of the measurement that was actually diagnostic --
# a take must have real presence between 400Hz and 8kHz, because that is what
# separates an engine from a hum -- while allowing the weight underneath that
# the user explicitly wants. It still rejects the two failure modes that have
# actually come back: the 77%-sub hum with nothing above 400Hz, and the window
# that is 70% hiss.
ARCADE  = [0.25, 0.30, 0.28, 0.15, 0.02]   # punchy: weight AND definition
HEAVY   = [0.40, 0.28, 0.20, 0.10, 0.02]   # a landing may be bottom-heavy
REALISM = [0.02, 0.17, 0.40, 0.36, 0.05]   # what the reference recordings are

# name -> (prompt needle, seconds, target peak, profile)
JOBS = {
    'truckget':   ('monster truck ignition sound',            1.50, 0.94, ARCADE),
    'truckidle':  ('seamless looping monster truck driving',  3.50, 0.85, ARCADE),
    'truckjump':  ('monster truck launching into the air',    1.10, 0.94, ARCADE),
    'truckboost': ('monster truck while it is airborne',      0.90, 0.94, ARCADE),
    'truckland':  ('monster truck landing sound',             0.70, 0.95, HEAVY),
    'kick':       ('KICKING a heavy metal barred door',       0.90, 0.85, None),
    'boom':       ('BOOM',                                    1.00, 0.95, None),
    'megg':       ('magical PICKUP chime',                    1.40, 0.80, None),
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


def mono(src, tmp, sr=44100):
    """44.1k, NOT 22k. At 22050 the spectrum stops at 11kHz, so every band's
    share is computed against a smaller total and the 2-8kHz band reads far
    higher than it is -- a window that scored 42% here measured 70% once cut
    at full rate. Scoring has to be done in the same units as the reference or
    it is not scoring anything."""
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
            W = int(secs*sr)
            # SCORE THE WINDOW THAT WILL BE CUT, exactly. There used to be a
            # 30ms LEAD subtracted at cut time so an attack could not be
            # clipped, and it silently invalidated every score: on the winning
            # take those 30ms pulled a bass transient into the clip and moved
            # it from 32/29/29 to 47/18/26. Thirty milliseconds is nothing to
            # look at and an enormous amount of low end.
            #   The hop is finer than the old 100ms for the same reason -- the
            # scan should be able to land ON an attack rather than near one,
            # which is what LEAD was really compensating for.
            H = max(1, int(0.02*sr))
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
                    best = (d, src, i/float(sr), b, rms, a, sr)
        if not best:
            print('  %-11s nothing usable' % name)
            continue
        d, src, at, b, rms, a, sr = best
        print('  %-11s %s  @%5.2fs  score %.3f' % (name, os.path.basename(src)[:34], at, d))
        print('              bands ' + ' '.join('%2.0f%%' % (100*x) for x in b) +
              ('   want ' + ' '.join('%2.0f%%' % (100*x) for x in prof) if prof else ''))
        if not write:
            continue
        start = at              # exactly the window that was scored -- see above
        # THE WINDOW SCORED MUST BE THE WINDOW SHIPPED. Three separate things
        # were quietly breaking that, each showing up as a cut file measuring
        # nothing like the segment the picker chose:
        #
        #   * -ss BEFORE -i is a fast seek to the nearest packet, which on a
        #     long mp3 lands somewhere else entirely -- and on one 107s take it
        #     landed on silence and wrote a 414-byte file without complaining.
        #     The cut is done with atrim now, in the filter graph, where it
        #     cannot miss.
        #   * dynaudnorm is a DYNAMIC normaliser: it rides the level across the
        #     clip and reshapes the very balance being scored. A one-shot wants
        #     one number applied to the whole thing, so the peak is measured
        #     here and a fixed gain applied.
        #   * the 30ms LEAD, which moved the winning clip from 32/29/29 to
        #     47/18/26 all by itself. Now the scan hops finely enough to land
        #     on the attack instead of being nudged back onto it.
        pk = float(np.abs(a[int(start*sr):int((start+secs)*sr)]).max()) or 1.0
        gain = min(12.0, peak/pk)
        for ext, args in (('.ogg', ['-c:a', 'libopus', '-b:a', '96k']),
                          ('.mp3', ['-c:a', 'libmp3lame', '-b:a', '128k'])):
            dst = os.path.join(OUT, name + ext)
            # atrim, NOT -ss. Accurate seek returned pure silence on a 107s
            # take whose audio at that offset measures rms 0.18 -- the seek
            # simply failed past some point in the file, and failed quietly,
            # writing a 414-byte ogg. A filter cannot miss: the whole stream is
            # decoded and the window is cut out of it in the graph.
            subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y',
                            '-i', src,
                            '-af', 'atrim=start=%.3f:duration=%.3f,asetpts=N/SR/TB,'
                                   'volume=%.4f,afade=t=in:st=0:d=0.012,'
                                   'afade=t=out:st=%.3f:d=%.3f'
                                   % (start, secs, gain, max(0, secs-FADE), FADE)]
                           + args + [dst], check=True)
            print('              %-15s %5d KB  (x%.2f)'
                  % (name+ext, os.path.getsize(dst)//1024, gain))
    if not write:
        print('  dry run: pass --write')


if __name__ == '__main__':
    main()
