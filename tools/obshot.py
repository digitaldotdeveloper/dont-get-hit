# -*- coding: utf-8 -*-
"""A contact sheet of the obstacle set, shot in the running game.

    python tools/obshot.py URL out.png key,key,key [--hit]

Each hazard is spawned into a real run, parked in the middle of the screen
with the chicken in front of it for scale, and photographed. `--hit` turns on
?hit=1 so the lethal shapes are drawn over the art -- which is the only way to
see whether "the sprite fills its hitbox" is actually true of a new prop.

The scene is held still with game.freeze, which drops the clock to 6% rather
than stopping it. Nothing here stops the loop: a paused game does not draw,
and a screenshot of a game that is not drawing is a screenshot of nothing.
"""
import base64, io, json, os, socket, subprocess, sys, time, urllib.request
import websocket
from PIL import Image, ImageDraw

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 1280, 620

# The game lives inside an IIFE, so there is nothing to reach in from out
# here. ?ob=KEY hangs its own setup on window for exactly this.
SETUP = """window.__ob(__KEY__)"""


def main():
    url, out, keys = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    url += ("&" if "?" in url else "?") + "ob=" + keys[0]
    if "--hit" in sys.argv:
        url += "&hit=1"
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    prof = (os.environ.get("CLAUDE_JOB_DIR") or os.environ["TEMP"]) + "/obshot-%d" % port
    proc = subprocess.Popen([CHROME, "--headless=new", "--no-sandbox", "--mute-audio",
        "--hide-scrollbars", "--remote-debugging-port=%d" % port,
        "--remote-allow-origins=*", "--user-data-dir=" + prof, "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tgt = None
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen(
                    "http://127.0.0.1:%d/json" % port, timeout=2))
                tgt = next((t for t in tabs if t["type"] == "page"), None)
                if tgt: break
            except Exception: pass
            time.sleep(0.25)
        ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=30)
        n = [0]
        def cmd(method, **params):
            n[0] += 1
            ws.send(json.dumps({"id": n[0], "method": method, "params": params}))
            while True:
                m = json.loads(ws.recv())
                if m.get("id") == n[0]:
                    if "error" in m: raise RuntimeError(method + ": " + json.dumps(m["error"]))
                    return m.get("result", {})

        cmd("Emulation.setDeviceMetricsOverride", width=W, height=H,
            deviceScaleFactor=2, mobile=True)
        cmd("Page.enable"); cmd("Page.navigate", url=url)
        time.sleep(6.0)                      # every prop through the load queue

        shots = []
        for k in keys:
            r = cmd("Runtime.evaluate", expression=SETUP.replace("__KEY__", json.dumps(k)),
                    returnByValue=True)
            info = r["result"].get("value") or ""
            time.sleep(0.45)
            png = cmd("Page.captureScreenshot", format="png")["data"]
            im = Image.open(io.BytesIO(base64.b64decode(png))).convert("RGB")
            shots.append((k, info, im))
            print("  %-12s %s" % (k, info))
        ws.close()
    finally:
        proc.terminate()

    cols = 2
    tw = 900
    th = int(shots[0][2].height * tw / shots[0][2].width)
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new("RGB", (cols*tw, rows*(th+26)), (18, 8, 34))
    d = ImageDraw.Draw(sheet)
    for i, (k, info, im) in enumerate(shots):
        x, y = (i % cols)*tw, (i // cols)*(th+26)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y))
        d.text((x+8, y+th+7), "%s   %s" % (k, info), fill=(255, 242, 222))
    sheet.save(out)
    print("->", out, sheet.size)


if __name__ == "__main__":
    main()
