# -*- coding: utf-8 -*-
"""Photograph every vehicle at every beat of its own motion, IN THE REAL GAME.

    python tools/veh_board.py URL out_dir [--only rocket]

Point `out_dir` at the Studio archive's `dgh/boards/`, next to the generated
concept boards: neither of these ships, so neither belongs in the game folder.
`tools/paths.py` knows where the archive is.

The other half of the brief's "motion reference" answer. `gen_veh_board.py`
draws the poster; this one is the truth: each panel is the shipping game, at a
state this script put it in on purpose, cropped to the vehicle and captioned
with the number that state actually has.

WHY BOTH EXIST. A generated board is a claim about how a vehicle moves and it
was drawn before the vehicle did -- it cannot know that the rocket's lean tops
out at 0.34, that the hopper's timed bounce reaches 510 and its lazy one 247,
or that the toaster's full charge is worth 0.80 of the play area. This can,
because it asks. And it stays true: re-run it after a tuning pass and the sheet
is the new tuning rather than a picture of the old one.

HOW A FRAME IS PINNED. Not by waiting for the game to happen to be in the state
wanted -- that is how you get six pictures of a vehicle flying level. The clock
is dropped to a crawl (`game.tsTarget`), the state is SET (`player.vy`, the
charge, the polarity, the squash spring), one frame is allowed to draw, and
that is the photograph. Everything a vehicle does is a number somewhere, so
every beat can be dialled in exactly.

The crop comes from `DGH.metrics()` rather than from eyeballing where the
vehicle usually is: SCALE and GROUND live inside the game's closure and
reconstructing them from outside is the kind of guess this project keeps
banning.
"""
import base64, json, os, socket, subprocess, sys, time, urllib.request
import websocket
from PIL import Image, ImageDraw

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H, DPR = 1280, 760, 2

# label, javascript that puts the game in that state, what to report
BEATS = {
 'trolley': [
   ("DRIVING",    "P.y=0;P.vy=0;P.onGround=true;G.tSquash=0;P.rideKick=0;P.rideLand=0", "wheels turning, exhaust lit"),
   ("LAUNCH",     "P.onGround=false;P.y=40;P.vy=-2400;P.rideKick=1;G.tSquash=-0.45;P.rideJumps=1", "front end up, suspension extended"),
   ("APEX",       "P.onGround=false;P.y=560;P.vy=-30;P.rideKick=0;G.tSquash=0;P.rideJumps=1", "top of the arc"),
   ("DESCENT",    "P.onGround=false;P.y=300;P.vy=900;P.rideKick=0;G.tSquash=0;P.rideJumps=1", "nose down, flame easing"),
   ("SLAM",       "P.y=0;P.vy=0;P.onGround=true;G.tSquash=1.05;P.rideLand=0.26", "suspension crushed, fire out the back"),
   ("REBOUND",    "P.y=0;P.vy=0;P.onGround=true;G.tSquash=-0.30;P.rideLand=0.10", "spring overshoots the other way"),
 ],
 'ufo': [
   ("HOVER",      "P.y=380;P.vy=0;G.ufoLamp=0.28;G.ufoWob=0;G.ufoRot=0", "released: lamps low, beams short"),
   ("CLIMB",      "P.y=380;P.vy=-760;G.ufoLamp=1;G.ufoWob=0.95;G.ufoRot=-0.26", "beams at full reach, white lip stretched down"),
   ("SINK",       "P.y=380;P.vy=640;G.ufoLamp=0.28;G.ufoWob=-0.85;G.ufoRot=0.26", "lip wobbles back up, lamps nearly out"),
   ("LOW PASS",   "P.y=40;P.vy=0;G.ufoLamp=1;G.ufoWob=0.2;G.ufoRot=0", "beam standing on the road"),
   ("ROOF",       "P.y=D.ufoCeil();P.vy=-20;G.ufoLamp=1;G.ufoWob=0.5;G.ufoRot=-0.1", "at its ceiling"),
   ("SETTLED",    "P.y=30;P.vy=0;G.ufoLamp=0.28;G.ufoWob=-1.2;G.ufoRot=0", "squished on the hover floor"),
 ],
 # The rocket is set by ANGLE now, not by velocity: `feel` derives vy from the
 # nose, so writing vy would be overwritten on the next tick. rocSpin is how
 # fast the nose is still swinging, which is the half of this vehicle that a
 # single frame cannot show -- hence the captions.
 'rocket': [
   ("LEVEL",      "P.y=340;G.rocRot=0;G.rocSpin=0", "nose flat: it flies dead level"),
   ("NOSE UP",    "P.y=340;G.rocRot=-0.62;G.rocSpin=0", "full deflection, ~1200/s of climb"),
   ("NOSE DOWN",  "P.y=340;G.rocRot=0.62;G.rocSpin=0", "full deflection the other way"),
   ("SWINGING",   "P.y=340;G.rocRot=-0.08;G.rocSpin=-1.5", "button just let go -- the nose has NOT stopped"),
   ("OVERSHOOT",  "P.y=430;G.rocRot=-0.46;G.rocSpin=-0.7", "released at level and it kept coming round"),
   ("ROOF",       "P.y=D.ufoCeil();G.rocRot=-0.30;G.rocSpin=0", "pinned, and the nose bleeds off"),
 ],
 'hopper': [
   ("FALL",       "P.onGround=false;P.y=300;P.vy=900;G.hopSq=-0.35", "coming down, spring extended"),
   ("CONTACT",    "P.y=0;P.vy=0;P.onGround=false;G.hopSq=1.10", "spring crushed flat"),
   ("LAUNCH",     "P.onGround=false;P.y=60;P.vy=-1500;G.hopSq=0.30", "snapping back out"),
   ("LAZY BOUNCE","P.onGround=false;P.y=247;P.vy=-20;G.hopSq=-0.20", "no press: apex 247"),
   ("TIMED",      "P.onGround=false;P.y=510;P.vy=-20;G.hopSq=-0.20", "pressed on contact: apex 510"),
   ("ARMED",      "P.onGround=false;P.y=140;P.vy=780;G.hopSq=-0.1;P.hopArm=0.26", "press banked, about to land"),
 ],
 'spoon': [
   # spnFlipA is set explicitly as well as pol: the roll is EASED in `feel`,
   # and the clock is nearly stopped for the photograph, so leaving it to
   # settle would photograph six frames of the same half-turn.
   ("FLOOR",      "G.pol=1;G.spnFlipA=0;P.y=0;P.vy=0;P.onGround=true;G.spnT=0;G.spnRot=0", "riding the road, coils quiet"),
   ("RELEASE",    "G.pol=-1;G.spnFlipA=0.42;P.y=40;P.vy=-500;P.onGround=false;G.spnT=0.5;G.spnRot=-0.10", "poles flipped, arc crackling, starting to roll"),
   ("CROSSING",   "G.pol=-1;G.spnFlipA=1.95;P.y=330;P.vy=-1600;P.onGround=false;G.spnT=0.34;G.spnRot=-0.18", "half way, past the roll, committed"),
   ("CEILING",    "G.pol=-1;G.spnFlipA=Math.PI;P.y=D.spnRoof();P.vy=0;P.onGround=true;G.spnT=0;G.spnRot=0", "stuck upside down"),
   ("BACK DOWN",  "G.pol=1;G.spnFlipA=2.30;P.y=D.spnRoof()-140;P.vy=900;P.onGround=false;G.spnT=0.45;G.spnRot=0.14", "flipped again, rolling back"),
   ("SNAP",       "G.pol=1;G.spnFlipA=0;P.y=0;P.vy=0;P.onGround=true;G.spnT=0.12;G.spnRot=0", "back on the floor"),
 ],
 'toaster': [
   ("DRIVE",      "P.y=0;P.vy=0;P.onGround=true;G.tstChg=0;G.tstPop=0", "slots empty, element cold"),
   ("CHARGING",   "P.y=0;P.vy=0;P.onGround=true;G.tstChg=0.45;G.tstPop=0", "toast half out, element warming"),
   ("FULL",       "P.y=0;P.vy=0;P.onGround=true;G.tstChg=1;G.tstPop=0", "charge 1.00 -- hunkered and glowing"),
   ("POP",        "P.onGround=false;P.y=30;P.vy=-2100;G.tstChg=0;G.tstPop=0.22", "toast flung, launching"),
   ("ARC",        "P.onGround=false;P.y=640;P.vy=-40;G.tstChg=0;G.tstPop=0", "apex of a full charge"),
   ("LANDING",    "P.y=0;P.vy=0;P.onGround=true;G.tstChg=0;G.tstPop=0", "down, and charging again"),
 ],
}


def cdp(url, out_dir, only=None):
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    prof = os.path.join(os.environ.get("TEMP", "."), "vboard-%d" % port)
    proc = subprocess.Popen([CHROME, "--headless=new", "--no-sandbox", "--mute-audio",
        "--hide-scrollbars", "--remote-debugging-port=%d" % port,
        "--remote-allow-origins=*", "--user-data-dir=" + prof, "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tgt = None
        for _ in range(80):
            try:
                tabs = json.load(urllib.request.urlopen(
                    "http://127.0.0.1:%d/json" % port, timeout=2))
                tgt = next((t for t in tabs if t["type"] == "page"), None)
                if tgt: break
            except Exception: pass
            time.sleep(0.25)
        ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=40)
        n = [0]
        def cmd(m, **kw):
            n[0] += 1
            ws.send(json.dumps({"id": n[0], "method": m, "params": kw}))
            while True:
                r = json.loads(ws.recv())
                if r.get("id") == n[0]:
                    if "error" in r: raise RuntimeError(json.dumps(r["error"]))
                    return r.get("result", {})
        def ev(e):
            r = cmd("Runtime.evaluate", expression=e, returnByValue=True)
            if r.get("exceptionDetails"):
                raise RuntimeError(json.dumps(r["exceptionDetails"])[:400])
            return r["result"].get("value")

        cmd("Emulation.setDeviceMetricsOverride", width=W, height=H,
            deviceScaleFactor=DPR, mobile=True)
        cmd("Page.enable"); cmd("Page.navigate", url=url)
        for _ in range(80):
            if ev("!!(window.DGH && DGH.LOAD && DGH.LOAD.ready)"): break
            time.sleep(0.5)
        """?dbg=1 is what puts DGH on the window, and it also parks a green
           readout over the top-left of the canvas and a READY/GO title over the
           middle -- both of which landed in panels. Hiding the readout once was
           not enough: the game re-sets `display='block'` on it every frame, so
           an inline `!important` is simply overwritten on the next tick. It is
           turned off at the source instead (`game.dbg=false`, after DGH is
           already on the window) and re-hidden by the keep-alive tick, and
           `game.goT=0` retires the countdown. The panel wants the game, not the
           instrumentation."""
        ev("var tut=document.getElementById('tut');if(tut)tut.style.display='none';"
           "var hud=document.getElementById('hud');if(hud)hud.style.opacity=0;")
        os.makedirs(out_dir, exist_ok=True)
        shots = {}
        for veh, beats in BEATS.items():
            if only and only != veh: continue
            ev("var D=DGH,G=D.game,P=D.player;"
               "G.forceRide=true;G.forceVeh=%r;D.startQuick();"
               "clearInterval(window.__k);"
               "window.__k=setInterval(function(){var D=DGH,G=D.game;"
               "G.obstacles.length=0;G.crows.length=0;G.eggs.length=0;"
               "G.spawnT=9;G.crowT=9;G.dropT=99;G.ride=1;G.tsTarget=0.02;"
               "G.pops.length=0;G.goT=0;G.dbg=false;"
               "var st=document.getElementById('selftest');"
               "if(st)st.style.display='none';},16)" % veh)
            time.sleep(1.2)
            shots[veh] = []
            for label, setup, note in beats:
                ev("(function(){var D=DGH,G=D.game,P=D.player;%s;})()" % setup)
                time.sleep(0.45)
                m = ev("DGH.metrics()")
                png = cmd("Page.captureScreenshot", format="png")["data"]
                p = os.path.join(out_dir, "raw_%s_%s.png" % (veh, label.replace(' ', '_')))
                open(p, "wb").write(base64.b64decode(png))
                shots[veh].append((label, note, p, m))
                print("  %-8s %-12s y=%4d" % (veh, label, ev("Math.round(DGH.player.y)")))
        ws.close()
        return shots
    finally:
        proc.terminate()


CROP_W, CROP_H = 620, 460     # world units, so every panel is the same window
def crop_to_vehicle(path, m):
    """A FIXED WINDOW in world units, centred on the vehicle -- not a box
       sized from the vehicle. The first version padded the collision box, and
       since the box is a different shape for every vehicle (and for the spoon,
       for every polarity) every panel came out a different size and the sheet
       was a ransom note. Same window every time means the six panels are
       comparable, which is the entire point of a reference sheet.

       `metrics()` reports CSS pixels; the screenshot is DPR times that."""
    im = Image.open(path).convert("RGB")
    S, G, box = m["SCALE"], m["GROUND"], m["box"]
    k = S * DPR
    cx = m["PX"] * k
    cy = (G - (box["b"] + box["t"]) * 0.5) * k
    hw, hh = CROP_W * 0.5 * k, CROP_H * 0.5 * k
    l, t = cx - hw, cy - hh
    # slide rather than shrink, so the window never changes size at the edges
    l = min(max(0, l), max(0, im.width - hw*2))
    t = min(max(0, t), max(0, im.height - hh*2))
    return im.crop((int(l), int(t), int(l + hw*2), int(t + hh*2)))


def sheet(veh, panels, out_dir):
    CW_, PAD, LBL = 520, 14, 54
    cells = []
    for label, note, path, m in panels:
        im = crop_to_vehicle(path, m)
        h = round(im.height * CW_ / im.width)
        cells.append((label, note, im.resize((CW_, h), Image.LANCZOS)))
    rows, cols = 2, 3
    ch = max(c[2].height for c in cells)
    W_ = PAD + cols * (CW_ + PAD)
    H_ = 74 + rows * (LBL + ch + PAD)
    sh = Image.new("RGB", (W_, H_), (17, 18, 23))
    d = ImageDraw.Draw(sh)
    d.rectangle([0, 0, W_, 58], fill=(28, 30, 38))
    d.text((PAD + 4, 22), "%s  -  MOTION REFERENCE (captured from the running game)"
           % veh.upper(), fill=(150, 230, 120))
    for i, (label, note, im) in enumerate(cells):
        x = PAD + (i % cols) * (CW_ + PAD)
        y = 74 + (i // cols) * (LBL + ch + PAD)
        d.text((x + 2, y + 4), label, fill=(255, 214, 71))
        d.text((x + 2, y + 24), note, fill=(150, 158, 172))
        sh.paste(im, (x, y + LBL))
    p = os.path.join(out_dir, "motion_%s.png" % veh)
    sh.save(p)
    print("  wrote %s  %dx%d" % (p, sh.width, sh.height))
    return p


def main():
    url = sys.argv[1]
    out_dir = sys.argv[2]
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    shots = cdp(url, out_dir, only)
    for veh, panels in shots.items():
        sheet(veh, panels, out_dir)


if __name__ == "__main__":
    main()
