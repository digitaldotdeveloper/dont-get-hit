# -*- coding: utf-8 -*-
"""Render the game's own sounds to WAV, through ?sfx=1.

    python tools/sfx.py URL out_dir

Sound is the one part of this game that cannot be checked by looking at it, and
"it plays without throwing" is not the same as "it sounds like a footstep". So
each entry in S is rendered offline by the game itself -- `__sfx` swaps
A.ctx/master/sfxGain for an OfflineAudioContext and calls the REAL function, so
what comes out is the synthesis that ships -- and written next to a peak level.

It also joins the runs that only make sense as runs: eight footsteps at a walk
and at a sprint, the alert tracking then locking, and a twelve-egg streak, which
is the only way to hear whether the pentatonic ladder actually lands anywhere.
There is no wingbeat here -- the flap is silent by design, so the flight montage
is the glide and the two ends of it -- takeoff, the roof, and the landing. The
wind bed that used to sit under all of it is gone.
"""
import base64, io, json, os, socket, struct, subprocess, sys, time, urllib.request
import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SR = 44100

# name, argument, seconds
ONE = [
    ("step",     0.0,  0.35), ("step",  1.0, 0.35),
    ("scuff",    0.8,  0.60),
    ("glide",    None, 0.80), ("ceiling", None, 0.50),
    ("takeoff",  None, 0.60), ("land",  None, 0.55),
    ("alert",    False, 0.35), ("alert", True, 0.35),
    ("caw",      None, 0.70), ("crowpass", False, 0.55),
    ("crowpass", True, 0.55), ("crowhit", None, 0.90),
    ("hit",      None, 1.00), ("egg", 1, 0.35),
    ("eggrun",   5,    0.60), ("near", None, 0.50),
    # the three pickups, synthesised like the rest
    ("gatebreach", None, 2.00),
    ("truckget", None, 2.00),   # no megg: the mystery egg is silent now
    # truckboost RENDERS SILENT ON PURPOSE and the report will flag it. It is
    # the synthesised airborne surge, and it stands down whenever a real engine
    # recording is carrying the jump -- which it is. Two engines, one of them
    # fake, is not a boost. It comes back if truckget is ever missing.
    ("powerdown", None, 1.20),
    ("truckjump", None, 1.00), ("truckboost", None, 0.90),
    ("truckland", None, 0.90),
    # the saucer, which has no recording behind it -- the synth IS the sound,
    # so this is the only place its level can be set against anything
    ("ufoget",   None, 1.40),
    ("abduct",   None, 0.70),
]
# name, [args], gap between them, seconds each
RUNS = [
    ("run_slow",  "step",  [0.05]*8,          0.30, 0.35),
    ("run_fast",  "step",  [0.95]*8,          0.17, 0.35),
    ("egg_streak","egg",   list(range(1,13)), 0.17, 0.35),
]

# The four things worth listening to as a whole, because none of them is one
# sound: (label, [(at_seconds, name, arg, secs)], total_seconds).
#
# THE FLIGHT MONTAGE LOST ITS BED. It used to be a wind layer with everything
# else over the top, and the bed is gone; what is left is the glide and the two
# ends. Rendering it is how you check that a flight still has a shape without a
# layer holding it together -- which is a real question, and the answer is that
# the glide is now carrying the middle on its own.
MONTAGE = [
    ("montage_running", 6.0, [(0.15 + i*0.30, "step", 0.05, 0.35) for i in range(8)] +
                             [(3.2 + i*0.17, "step", 0.95, 0.35) for i in range(9)] +
                             [(5.1, "scuff", 0.8, 0.6)]),
    # no flap and no bed -- both are deliberately silent -- so a flight is
    # takeoff, the glide carrying the drop, the roof, and the landing
    ("montage_flying",  7.5, [(0.30, "takeoff", None, 0.6),
                              (1.9, "glide", None, 0.8), (2.8, "glide", None, 0.8),
                              (4.0, "ceiling", None, 0.5),
                              (5.0, "glide", None, 0.8),
                              (6.2, "land", None, 0.6)]),
    ("montage_crow",    7.0, [(0.0 + i*0.27, "alert", False, 0.35) for i in range(7)] +
                             [(1.95 + i*0.13, "alert", True, 0.35) for i in range(4)] +
                             [(2.55, "caw", None, 0.7), (3.5, "crowpass", True, 0.6),
                              (5.0, "crowhit", None, 0.9), (5.0, "hit", None, 1.0)]),
    ("montage_eggs",    5.0, [(0.2, "egg", 1, 0.35), (0.9, "egg", 1, 0.35)] +
                             [(1.7 + i*0.17, "egg", i+1, 0.35) for i in range(12)] +
                             [(3.75, "eggrun", 5, 0.6)]),
]


def wav_bytes(samples):
    d = b"".join(struct.pack("<h", int(max(-1, min(1, x)) * 32000)) for x in samples)
    return (b"RIFF" + struct.pack("<I", 36 + len(d)) + b"WAVEfmt " +
            struct.pack("<IHHIIHH", 16, 1, 1, SR, SR * 2, 2, 16) +
            b"data" + struct.pack("<I", len(d)) + d)


def wav_read(raw):
    n = struct.unpack("<I", raw[40:44])[0]
    return [struct.unpack("<h", raw[44 + i*2:46 + i*2])[0] / 32768.0 for i in range(n // 2)]


def main():
    url, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    url += ("&" if "?" in url else "?") + "sfx=1"
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    prof = os.path.join(os.environ.get("TEMP", "."), "cdp-sfx-%d" % port)
    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--mute-audio",
         "--autoplay-policy=no-user-gesture-required",
         "--remote-debugging-port=%d" % port, "--remote-allow-origins=*",
         "--user-data-dir=" + prof, "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tgt = None
        for _ in range(80):
            try:
                tabs = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % port, timeout=2))
                tgt = next((t for t in tabs if t["type"] == "page"), None)
                if tgt: break
            except Exception: pass
            time.sleep(0.25)
        ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=120)
        n = [0]
        def cmd(m, **kw):
            n[0] += 1
            ws.send(json.dumps({"id": n[0], "method": m, "params": kw}))
            while True:
                r = json.loads(ws.recv())
                if r.get("id") == n[0]:
                    if "error" in r: raise RuntimeError(m + ": " + json.dumps(r["error"]))
                    return r.get("result", {})
        cmd("Page.enable"); cmd("Page.navigate", url=url)
        # WAIT FOR THE HOOK, DO NOT SLEEP AT IT. This was `time.sleep(4.0)`,
        # which was true when the page had nothing to wait for; the loading
        # gate now holds boot until the art is decoded, so a fixed wait
        # started reporting "__sfx is not a function" as though the game were
        # broken. Poll for the thing we actually need.
        for _ in range(120):
            r = cmd("Runtime.evaluate",
                    expression="typeof window.__sfx === 'function'",
                    returnByValue=True)
            if r.get("result", {}).get("value"):
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("__sfx never appeared -- is ?sfx in the URL?")
        # ...and wait for the SAMPLES, not just the hook. Rendering before they
        # decode gives the first sound that wants one its synth fallback and
        # every later one the real file, which reads as a level bug that is not
        # there. Not fatal if they never arrive: the fallbacks are the point.
        for _ in range(80):
            r = cmd("Runtime.evaluate", expression="window.__warm && window.__warm()",
                    returnByValue=True)
            if r.get("result", {}).get("value") is True:
                break
            time.sleep(0.25)

        def render(name, arg, secs):
            r = cmd("Runtime.evaluate",
                    expression="window.__sfx(%s,%s,%s)" % (json.dumps(name), json.dumps(arg), secs),
                    returnByValue=True, awaitPromise=True)
            if "exceptionDetails" in r:
                raise RuntimeError(name + ": " + json.dumps(r["exceptionDetails"])[:300])
            d = json.loads(r["result"]["value"])
            return d["peak"], base64.b64decode(d["wav"])

        print("%-22s %6s  %s" % ("sound", "peak", "file"))
        for name, arg, secs in ONE:
            peak, raw = render(name, arg, secs)
            f = "%s%s.wav" % (name, "" if arg is None else "_" + str(arg))
            open(os.path.join(out, f), "wb").write(raw)
            flag = "  <-- SILENT" if peak < 0.001 else ("  <-- CLIPPING" if peak > 0.99 else "")
            print("%-22s %6.3f  %s%s" % (name + ("" if arg is None else " " + str(arg)), peak, f, flag))

        for label, name, args, gap, secs in RUNS:
            buf = []
            for i, a in enumerate(args):          # each clip laid down gap seconds apart
                _, raw = render(name, a, secs)
                pcm = wav_read(raw)
                start = int(i * gap * SR)
                if start + len(pcm) > len(buf): buf += [0.0] * (start + len(pcm) - len(buf))
                for j, x in enumerate(pcm): buf[start + j] += x
            peak = max(abs(x) for x in buf) or 1
            if peak > 0.95: buf = [x * 0.95 / peak for x in buf]
            open(os.path.join(out, label + ".wav"), "wb").write(wav_bytes(buf))
            print("%-22s %6.3f  %s.wav" % (label, peak, label))

        cache = {}
        for label, total, items in MONTAGE:
            buf = [0.0] * int(total * SR)
            for at, name, arg, secs in items:
                key = (name, str(arg), secs)
                if key not in cache: cache[key] = wav_read(render(name, arg, secs)[1])
                pcm, start = cache[key], int(at * SR)
                for j, x in enumerate(pcm):
                    if start + j < len(buf): buf[start + j] += x
            peak = max(abs(x) for x in buf) or 1
            # normalised, because these are for listening to, not for shipping
            buf = [x * 0.90 / peak for x in buf]
            open(os.path.join(out, label + ".wav"), "wb").write(wav_bytes(buf))
            print("%-22s %6.3f  %s.wav  (normalised for listening)" % (label, peak, label))
        ws.close()
    finally:
        proc.kill()


if __name__ == "__main__":
    main()
