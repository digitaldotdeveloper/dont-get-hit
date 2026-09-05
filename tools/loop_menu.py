# -*- coding: utf-8 -*-
"""Cut the menu music down to one loop of itself.

    python tools/loop_menu.py            # report only
    python tools/loop_menu.py --write    # cut and re-encode

The menu track was written as a three-minute piece and it plays behind a screen
nobody looks at for more than a few seconds, on a loop. Bitrate was already
taken as far as it goes by tools/opt_audio.py, so the only thing left to remove
is the two and a half minutes nobody hears.

Where to cut is measured, not guessed. The track is decoded to a coarse energy
envelope and autocorrelated against itself: music that repeats every N seconds
has a peak at N, and cutting on that period means the end of the file runs back
into the start on the same beat. Cutting at a round number instead lands
mid-phrase and the loop clicks every time it comes round.

Mono, and lower rates than the run tracks, for the one place in the game where
the music is the only thing playing: no sound effects to sit under, a phone
speaker that is mono anyway, and it is the first thing every player downloads.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import SHEETS, REF, AUDIOSRC, ROOT as GAME, sheets, need
import os, struct, subprocess, sys, wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD  = os.path.join(ROOT, "audio")
SRC  = os.path.join(AUDIOSRC, "music_menu.mp3")
FF   = __import__("imageio_ffmpeg").get_ffmpeg_exe()

HOP = 0.05                 # envelope resolution, seconds
LO, HI = 18.0, 95.0        # the loop we are looking for, in seconds
TMP = os.path.join(os.environ.get("TEMP", "."), "_menu_env.wav")


def envelope(path):
    """RMS per 50ms of a mono 8kHz decode -- enough to see structure, small
       enough to autocorrelate in pure Python."""
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", path,
                    "-ac", "1", "-ar", "8000", TMP], check=True)
    with wave.open(TMP, "rb") as w:
        n, sr = w.getnframes(), w.getframerate()
        raw = w.readframes(n)
    step = int(sr*HOP)
    env = []
    for i in range(0, len(raw)//2 - step, step):
        chunk = struct.unpack_from("<%dh" % step, raw, i*2)
        env.append((sum(v*v for v in chunk)/step) ** 0.5)
    return env, sr


def best_period(env):
    """How long one time round is: the lag that correlates best, tie-broken
       by which cut point the loop can actually come back to."""
    mean = sum(env)/len(env)
    e = [v - mean for v in env]
    lo, hi = int(LO/HOP), min(int(HI/HOP), len(e)//2)
    norm = sum(v*v for v in e) or 1.0
    best, scores = None, []
    for lag in range(lo, hi):
        n = len(e) - lag
        c = sum(e[i]*e[i+lag] for i in range(n)) / norm
        scores.append((c, lag))
        if best is None or c > best[0]: best = (c, lag)
    scores.sort(reverse=True)
    # The strongest peak is usually a PHRASE, not a section -- here 21.35s at
    # 0.424, with 24.0 and 48.0 just behind it. Looping on the phrase would be
    # correct and maddening, so among the peaks that score nearly as well the
    # longest one wins: it is still a boundary the music lands on, and the
    # player hears the tune go round half as often.
    good = [(c, l) for c, l in scores if c >= best[0]*0.90]
    # ...and among those, the cut has to LAND somewhere the loop can come back
    # to. A lag can correlate well over the whole track and still end on a
    # held note while the start is a downbeat: the first cut of this file was
    # 8661 RMS at the head against 2357 at the tail, which is an audible drop
    # every 48 seconds. So the seam is scored too -- how close the energy at
    # the cut is to the energy at the start -- and that breaks the tie.
    head = sum(env[:int(0.5/HOP)])/max(1, int(0.5/HOP))
    def seam(l):
        a, b = max(0, l - int(0.5/HOP)), l
        tail = sum(env[a:b])/max(1, b-a)
        return abs(tail - head)/(head or 1)
    pick = min(good, key=lambda cl: seam(cl[1]) - 0.20*(cl[1]*HOP)/HI)
    return pick[1]*HOP, pick[0], [(round(l*HOP, 2), round(c, 3), round(seam(l), 2))
                                  for c, l in scores[:5]]


def main():
    env, sr = envelope(SRC)
    total = len(env)*HOP
    period, score, top = best_period(env)
    print("source      %s  %.1fs  %d KB" % (os.path.basename(SRC), total,
                                            os.path.getsize(SRC)//1024))
    print("loop period %.2fs  (correlation %.3f)" % (period, score))
    print("runners-up  %s" % top[1:])
    if "--write" not in sys.argv:
        print("\n(report only -- pass --write to cut)")
        return
    mp3 = os.path.join(AUD, "music_menu.mp3")
    ogg = os.path.join(AUD, "music_menu.ogg")
    for dst, args in ((ogg, ["-c:a", "libopus", "-b:a", "48k", "-vbr", "on",
                             "-application", "audio"]),
                      (mp3, ["-c:a", "libmp3lame", "-b:a", "72k"])):
        subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", SRC, "-t", "%.3f" % period, "-ac", "1"] + args + [dst],
                       check=True)
        print("wrote %-28s %5d KB" % (os.path.basename(dst), os.path.getsize(dst)//1024))


if __name__ == "__main__":
    main()
