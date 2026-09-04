# -*- coding: utf-8 -*-
"""What is actually inside the music, without ffmpeg.

    python tools/audio_report.py

Parses the ID3v2 header and the first MPEG audio frame directly, so it can
report bitrate, channel mode, sample rate and duration on a machine with no
audio tooling installed at all. Also reports how many bytes are tag rather
than sound -- embedded cover art in an ID3 tag is pure download weight for a
game that never shows it.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(ROOT, "audio")

# MPEG1 Layer III, then MPEG2/2.5 Layer III
BR1 = [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0]
BR2 = [0,8,16,24,32,40,48,56,64,80,96,112,128,144,160,0]
SR = {3:{0:44100,1:48000,2:32000}, 2:{0:22050,1:24000,2:16000}, 0:{0:11025,1:12000,2:8000}}
MODE = {0:"stereo", 1:"joint-stereo", 2:"dual-mono", 3:"mono"}


def id3_size(b):
    if b[:3] != b"ID3":
        return 0
    # synchsafe 28-bit size, plus the 10-byte header
    n = (b[6] & 0x7F) << 21 | (b[7] & 0x7F) << 14 | (b[8] & 0x7F) << 7 | (b[9] & 0x7F)
    return n + 10


def first_frame(b, off):
    for i in range(off, min(len(b) - 4, off + 400000)):
        if b[i] == 0xFF and (b[i+1] & 0xE0) == 0xE0:
            ver = (b[i+1] >> 3) & 3           # 3=MPEG1, 2=MPEG2, 0=MPEG2.5
            layer = (b[i+1] >> 1) & 3         # 1 = Layer III
            bri = (b[i+2] >> 4) & 0xF
            sri = (b[i+2] >> 2) & 3
            if layer != 1 or bri in (0, 15) or sri == 3 or ver == 1:
                continue
            br = (BR1 if ver == 3 else BR2)[bri]
            sr = SR[ver][sri]
            return i, br, sr, MODE[(b[i+3] >> 6) & 3], ver
    return None


def main():
    rows, total = [], 0
    for f in sorted(os.listdir(AUD)):
        if not f.lower().endswith(".mp3"):
            continue
        p = os.path.join(AUD, f)
        b = open(p, "rb").read()
        size = len(b); total += size
        tag = id3_size(b)
        ff = first_frame(b, tag)
        if not ff:
            rows.append((f, size, tag, 0, 0, "?", 0)); continue
        off, br, sr, mode, ver = ff
        audio_bytes = size - off
        # VBR files carry a Xing/Info header in the first frame; if present the
        # nominal bitrate above is only the first frame's, so fall back to the
        # average, which is what actually costs the download.
        vbr = (b[off:off+200].find(b"Xing") >= 0) or (b[off:off+200].find(b"Info") >= 0)
        secs = audio_bytes * 8.0 / (br * 1000.0) if br else 0
        rows.append((f, size, tag, br, sr, mode + ("/VBR" if vbr else ""), secs))
    print("  %-24s %8s %7s %6s %7s %-16s %7s" %
          ("file", "size KB", "tag KB", "kbps", "kHz", "channels", "approx s"))
    for f, size, tag, br, sr, mode, secs in rows:
        print("  %-24s %8.1f %7.1f %6d %7.1f %-16s %7.1f" %
              (f, size/1024.0, tag/1024.0, br, sr/1000.0, mode, secs))
    print("  %-24s %8.1f KB  = %.2f MB" % ("TOTAL", total/1024.0, total/1048576.0))
    tags = sum(r[2] for r in rows)
    print("  ID3 tag bytes across all files: %.1f KB" % (tags/1024.0))


if __name__ == "__main__":
    main()
