# -*- coding: utf-8 -*-
"""Find the lowest bitrate each sound survives, and encode it there.

    python tools/opt_audio_sfx.py            # report
    python tools/opt_audio_sfx.py --write    # re-encode

WHY A SCRIPT AND NOT A GUESS. The truck sounds went in at whatever the encoder
defaults were near -- 129 kbps for a MONO engine recording with 96% of its
energy below 400Hz, which is paying for bandwidth that is not there. But the
opposite guess is worse: pick a number too low and the artefacts land on a
sound nobody re-checks.

So each candidate bitrate is encoded, decoded and COMPARED to the source in
eleven bands, and the error is reported in dB. The rule used here is that a
mean band error under 0.5dB is inaudible for material like this, and the
smallest file meeting it wins. That is a measurement rather than an opinion,
and it is repeatable when a new sound arrives.

Sources are the ORIGINALS -- the user's wavs and the untouched download -- so
this is a re-encode from master, not a transcode of a transcode. Doing it the
other way would stack generation loss on top of the saving."""
import os
import subprocess
import sys
import wave

import numpy as np

FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESK = r"C:\Users\it\Desktop"
TMP = os.environ.get('TEMP', '.')

# dst (no extension), source, ffmpeg filter chain, channels, opus/mp3 candidates
JOBS = [
    ('audio/sfx/truckget',  os.path.join(DESK, 'engine-ignition.wav'),
     'afade=t=out:st=3.480:d=0.055', 1, 'sfx'),
    ('audio/sfx/truckidle', os.path.join(DESK, 'engine-idle-loop (1).wav'),
     'atrim=start=1.0,asetpts=N/SR/TB', 1, 'loop'),
    ('audio/sfx/truckland', os.path.join(DESK, 'truck-land-14.wav'),
     'atrim=start=0.009,asetpts=N/SR/TB', 1, 'sfx'),
    # THE FOOTSTEP IS TRIMMED HARD, and not to save the 8KB. The recording runs
    # a full second, but it is down to 5% of its peak by 0.21s and the rest is
    # a room tail -- and at a sprint the game asks for a step every 0.17s. Left
    # whole, three of them would be overlapping at all times and a run would
    # turn to porridge. 0.24s with a fade keeps the whole body of it and lets
    # each step end before the next two arrive.
    ('audio/sfx/step', os.path.join(DESK, 'step-4.wav'),
     'atrim=start=0:duration=0.24,asetpts=N/SR/TB,afade=t=out:st=0.195:d=0.045',
     1, 'sfx'),
    ('audio/music_ride_b',
     os.path.join(DESK, 'monster-truck-ignition-and-rev-as-a-short-punc-1788718695372-1.mp3'),
     'atrim=start=6.0:duration=36.0,asetpts=N/SR/TB,volume=0.865', 2, 'music'),
]
OPUS = [24, 32, 40, 48, 64, 80]
MP3 = [48, 56, 64, 80, 96]
LIMIT_DB = 0.5          # mean band error we treat as inaudible

# FLOORS, BECAUSE THE METRIC HAS A KNOWN BLIND SPOT. Band energy is exactly
# what a codec works hardest to preserve; it can hold the spectrum together
# while throwing away the detail underneath it. Run without a floor, this
# script cheerfully passed a 36-SECOND STEREO MUSIC TRACK at 24kbps Opus with
# a 0.38dB error, which is not a transparent encode, it is a measurement
# looking the wrong way.
# So the number picked is the larger of what was measured and what the
# material deserves: music matches what the rest of the soundtrack already
# ships at (music_ride is 63k opus / 96k mp3), and effects get a floor too,
# with a loop treated as music because an artefact you hear once is a texture
# and an artefact you hear every second is a fault.
FLOOR = {'music': {'.ogg': 64, '.mp3': 96},
         'sfx':   {'.ogg': 32, '.mp3': 64},
         'loop':  {'.ogg': 64, '.mp3': 64}}


def decode(p, out):
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', p,
                    '-ac', '1', '-ar', '44100', out], check=True)
    with wave.open(out, 'rb') as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float)/32768.


def bands(a, sr=44100, n=11):
    """Energy per band on a log scale, in dB. Compared band by band this is
    insensitive to the phase and delay a codec introduces, which is what makes
    sample-wise subtraction useless here."""
    N = 1 << 14
    if len(a) < N:
        a = np.pad(a, (0, N - len(a)))
    acc = np.zeros(N//2+1)
    win = np.hanning(N)
    cnt = 0
    for i in range(0, max(1, len(a)-N), N//2):
        if i+N > len(a):
            break
        acc += np.abs(np.fft.rfft(a[i:i+N]*win))**2
        cnt += 1
    if not cnt:
        acc = np.abs(np.fft.rfft(a[:N]*win))**2
    f = np.fft.rfftfreq(N, 1.0/sr)
    edges = np.geomspace(60, 16000, n+1)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (f >= lo) & (f < hi)
        out.append(10*np.log10(acc[m].sum() + 1e-12))
    return np.array(out)


def main():
    write = '--write' in sys.argv
    total_before = total_after = 0
    for dst, src, filt, ch, kind in JOBS:
        if not os.path.exists(src):
            print('  %-26s SOURCE MISSING %s' % (dst, src))
            continue
        ref_wav = os.path.join(TMP, '_opt_ref.wav')
        subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', src,
                        '-af', filt, '-ac', str(ch), '-ar', '48000', ref_wav], check=True)
        ref = decode(ref_wav, os.path.join(TMP, '_opt_refd.wav'))
        rb = bands(ref)
        for p in (dst + '.ogg', dst + '.mp3'):
            if os.path.exists(p):
                total_before += os.path.getsize(p)
        print('  %s' % dst)
        picked = {}
        for ext, cands, args in (('.ogg', OPUS, ['-c:a', 'libopus']),
                                 ('.mp3', MP3, ['-c:a', 'libmp3lame'])):
            for kb in cands:
                trial = os.path.join(TMP, '_opt_try' + ext)
                subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y',
                                '-i', ref_wav] + args + ['-b:a', '%dk' % kb, trial],
                               check=True)
                got = decode(trial, os.path.join(TMP, '_opt_got.wav'))
                n = min(len(ref), len(got))
                err = float(np.abs(bands(got[:n]) - bands(ref[:n])).mean())
                sz = os.path.getsize(trial)
                ok = err < LIMIT_DB
                print('      %s %3dk  %6.1f KB  band error %4.2f dB %s'
                      % (ext, kb, sz/1024., err, 'ok' if ok else ''))
                if ok:
                    picked[ext] = (kb, sz)
                    break
            if ext not in picked:
                picked[ext] = (cands[-1], 0)
                print('      %s: nothing met %.1fdB, using %dk' % (ext, LIMIT_DB, cands[-1]))
            fl = FLOOR[kind][ext]
            if picked[ext][0] < fl:
                print('      %s measured %dk, floored to %dk (%s)'
                      % (ext, picked[ext][0], fl, kind))
                picked[ext] = (fl, 0)
        for ext, args in (('.ogg', ['-c:a', 'libopus']), ('.mp3', ['-c:a', 'libmp3lame'])):
            kb = picked[ext][0]
            out = os.path.join(ROOT, dst + ext)
            if write:
                subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y',
                                '-i', ref_wav] + args + ['-b:a', '%dk' % kb, out],
                               check=True)
                total_after += os.path.getsize(out)
            else:
                total_after += picked[ext][1]
    print('  ---')
    print('  before %.1f KB   after %.1f KB   saved %.1f KB (%.0f%%)'
          % (total_before/1024., total_after/1024.,
             (total_before-total_after)/1024.,
             100*(total_before-total_after)/(total_before or 1)))
    if not write:
        print('  dry run: pass --write')


if __name__ == '__main__':
    main()
