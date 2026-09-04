# -*- coding: utf-8 -*-
"""Re-encode the music small, in two formats, and check nothing got truncated.

    python tools/opt_audio.py --write

The masters were 192 kbps joint-stereo MP3 -- CD-ish rates for music that
plays under sound effects on a phone speaker. Two outputs replace them:

  audio/*.ogg   Opus 64k   the one Android and every current browser gets
  audio/*.mp3   MP3  96k   the fallback, for Safari older than 17.4

Opus at 64k is roughly a 128k MP3, and it came out 62% smaller than the
master. Opus at 96k was measured too and is actually LARGER than MP3 96k on
this material -- its VBR overshoots on dense mixes -- so 96 buys nothing here.

The 192k originals move to audio/src/ rather than being deleted. They are the
only masters there are, and re-encoding a 96k MP3 later to chase another 20%
would be a third generation of the same artefacts.
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(ROOT, "audio")
SRC = os.path.join(AUD, "src")
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()


def dur(path):
    """Seconds, off the decoder rather than off the header."""
    out = subprocess.run([FF, "-hide_banner", "-nostats", "-i", path,
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    for line in out.splitlines()[::-1]:
        if "time=" in line:
            t = line.split("time=")[1].split(" ")[0]
            h, m, s = t.split(":")
            return int(h)*3600 + int(m)*60 + float(s)
    return 0.0


def enc(src, dst, args):
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", src]
                   + args + [dst], check=True)


def main():
    write = "--write" in sys.argv
    files = sorted(f for f in os.listdir(AUD) if f.lower().endswith(".mp3"))
    if not files:
        print("  nothing to do (already moved?)"); return
    os.makedirs(SRC, exist_ok=True)
    tot_b = tot_o = tot_m = 0
    print("  %-24s %9s %9s %9s   %s" % ("file", "was KB", "opus KB", "mp3 KB", "duration"))
    for f in files:
        s = os.path.join(AUD, f)
        stem = os.path.splitext(f)[0]
        ogg = os.path.join(AUD, stem + ".ogg")
        tmp = os.path.join(AUD, stem + ".new.mp3")
        enc(s, ogg, ["-c:a", "libopus", "-b:a", "64k", "-vbr", "on", "-application", "audio"])
        enc(s, tmp, ["-c:a", "libmp3lame", "-b:a", "96k"])
        d0, d1, d2 = dur(s), dur(ogg), dur(tmp)
        ok = abs(d1 - d0) < 0.35 and abs(d2 - d0) < 0.35
        b, o, m = os.path.getsize(s), os.path.getsize(ogg), os.path.getsize(tmp)
        tot_b += b; tot_o += o; tot_m += m
        print("  %-24s %9.1f %9.1f %9.1f   %.1fs %s" %
              (f, b/1024.0, o/1024.0, m/1024.0, d0, "OK" if ok else
               "LENGTH DRIFT %.2f/%.2f" % (d1-d0, d2-d0)))
        if not ok:
            os.remove(ogg); os.remove(tmp); continue
        if write:
            os.replace(s, os.path.join(SRC, f))     # master out of the way
            os.replace(tmp, s)                      # 96k takes the .mp3 name
        else:
            os.remove(ogg); os.remove(tmp)
    print("  %-24s %9.1f %9.1f %9.1f" % ("TOTAL", tot_b/1024.0, tot_o/1024.0, tot_m/1024.0))
    print("  opus set is %.1f%% of the masters, mp3 set %.1f%%" %
          (tot_o*100.0/tot_b, tot_m*100.0/tot_b))
    print("  " + ("written; masters in audio/src/" if write else "dry run: --write to keep"))


if __name__ == "__main__":
    main()
