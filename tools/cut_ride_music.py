# -*- coding: utf-8 -*-
"""Turn the generated metal riff into the ride's looping track.

    python tools/cut_ride_music.py            # report
    python tools/cut_ride_music.py --write    # -> audio/music_ride.ogg/.mp3

THE ONE THING THAT MATTERS HERE IS THE SEAM. The menu track shipped with ~100ms
of digital silence at the front and looped every 24 seconds, so every time round
you heard music -> gap -> music, and it took a measurement to find because
"cut on the loop period" sounds like it implies gapless and does not.

So this trims the LEADING AND TRAILING SILENCE first, by finding the first and
last samples that actually carry level, and only then encodes. A riff that
starts on the downbeat loops on the downbeat.

Encoding matches tools/opt_audio.py -- Opus 64k for everything current, MP3 96k
for Safari older than 17.4 -- because a third format is a third thing to keep
in sync and MUS_EXT only knows about two."""
import os
import subprocess
import sys
import wave

FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(ROOT, 'audio')
LIB = r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard\library"
NEEDLE = 'instrumental HEAVY METAL riff loop'
NAME = 'music_ride'
HEAD_DB = 0.02          # level that counts as "the music has started"
# The generator returned 175 SECONDS, not the ~30 the studio used to give. A
# ride lasts until you are hit -- often ten or twenty seconds -- so shipping
# three minutes would be a megabyte of audio nobody hears the end of. Cut a
# slice and let it repeat.
LEN = 32.0


def source():
    import json
    idx = json.load(open(os.path.join(LIB, 'index.json'), encoding='utf-8'))
    hits = [e for e in idx if NEEDLE in (e.get('prompt') or '')]
    if not hits:
        raise SystemExit('no metal riff render found -- run tools/gen_sfx.py music')
    hits.sort(key=lambda e: e.get('createdAt', 0), reverse=True)
    return os.path.join(LIB, hits[0]['file'].replace('/', os.sep))


def to_wav(src, dst):
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', src,
                    '-ac', '1', '-ar', '22050', dst], check=True)


def live_span(path):
    """First and last second that actually carries level, as float seconds."""
    with wave.open(path, 'rb') as w:
        n, sr = w.getnframes(), w.getframerate()
        raw = w.readframes(n)
    import array
    a = array.array('h')
    a.frombytes(raw)
    win = sr // 40                                   # 25ms
    peak = max(abs(v) for v in a) or 1
    first = last = None
    for i in range(0, len(a) - win, win):
        lvl = max(abs(v) for v in a[i:i+win]) / float(peak)
        if lvl > HEAD_DB:
            if first is None:
                first = i / float(sr)
            last = (i + win) / float(sr)
    return (first or 0.0), (last or (len(a) / float(sr))), len(a) / float(sr)


def main():
    write = '--write' in sys.argv
    src = source()
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_ride.wav')
    to_wav(src, tmp)
    a, b, total = live_span(tmp)
    print('  source   %s' % os.path.basename(src)[:56])
    print('  total    %.2fs' % total)
    print('  music    %.2fs .. %.2fs   (%.2fs of silence at the front, %.2fs at the end)'
          % (a, b, a, total - b))
    dur = min(LEN, b - a)
    print('  loop     %.2fs  (of %.2fs available)' % (dur, b - a))
    # THE SEAM, measured rather than hoped for: decode the slice and compare the
    # level of its first and last 60ms. A riff that fades out at the end or
    # starts from nothing will show up here as a big ratio, and that is exactly
    # what made the menu track breathe once every 24 seconds.
    seam = os.path.join(os.environ.get('TEMP', '.'), '_ride_slice.wav')
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y',
                    '-ss', '%.3f' % a, '-t', '%.3f' % dur, '-i', src,
                    '-ac', '1', '-ar', '22050', seam], check=True)
    import array, wave as _w
    with _w.open(seam, 'rb') as w:
        sr = w.getframerate(); raw = w.readframes(w.getnframes())
    sl = array.array('h'); sl.frombytes(raw)
    win = int(sr*0.06)
    rms = lambda xs: (sum(v*v for v in xs)/max(1, len(xs)))**0.5
    h, t = rms(sl[:win]), rms(sl[-win:])
    print('  seam     head RMS %.0f  tail RMS %.0f  ratio %.2f%s'
          % (h, t, (t/h if h else 0),
             '' if h and 0.45 < t/h < 2.2 else '   <-- LOOK AT THIS'))
    if not write:
        print('  dry run: pass --write')
        return
    os.makedirs(AUD, exist_ok=True)
    for ext, args in (('.ogg', ['-c:a', 'libopus', '-b:a', '64k']),
                      ('.mp3', ['-c:a', 'libmp3lame', '-b:a', '96k'])):
        out = os.path.join(AUD, NAME + ext)
        subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y',
                        '-ss', '%.3f' % a, '-t', '%.3f' % dur, '-i', src]
                       + args + [out], check=True)
        print('  wrote    %-22s %5d KB' % (NAME + ext, os.path.getsize(out) // 1024))


if __name__ == '__main__':
    main()
