# -*- coding: utf-8 -*-
"""A contact sheet of the crow attack, shot in the running game.

    python tools/crowshot.py URL out.png [--hit]

Four moments off ?crowshot=1 -- the badge tracking, the badge locked, the bird
crossing, and the bird a frame from him -- each staged by window.__crow and
photographed with the clock frozen. `--hit` draws the lethal box over the art,
which is how "the box is smaller than the wingspan" gets checked rather than
asserted.
"""
import base64, io, json, os, socket, subprocess, sys, time, urllib.request
import websocket
from PIL import Image, ImageDraw

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 1280, 620
STAGES = ["track", "lock", "fly", "close"]


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def main():
    url, out = sys.argv[1], sys.argv[2]
    url += ("&" if "?" in url else "?") + "crowshot=1"
    if "--hit" in sys.argv:
        url += "&hit=1"
    port = free_port()
    prof = os.path.join(os.environ.get("TEMP", "."), "cdp-crow-%d" % port)
    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
         "--mute-audio", "--remote-debugging-port=%d" % port, "--remote-allow-origins=*",
         "--user-data-dir=" + prof, "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tgt = None
        for _ in range(80):
            try:
                tabs = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % port, timeout=2))
                tgt = next((t for t in tabs if t["type"] == "page"), None)
                if tgt:
                    break
            except Exception:
                pass
            time.sleep(0.25)
        if not tgt:
            raise RuntimeError("devtools never came up")
        ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=40)
        n = [0]

        def cmd(method, **params):
            n[0] += 1
            ws.send(json.dumps({"id": n[0], "method": method, "params": params}))
            while True:
                m = json.loads(ws.recv())
                if m.get("id") == n[0]:
                    if "error" in m:
                        raise RuntimeError(method + ": " + json.dumps(m["error"]))
                    return m.get("result", {})

        cmd("Emulation.setDeviceMetricsOverride", width=W, height=H,
            deviceScaleFactor=1, mobile=False)
        cmd("Page.enable")
        cmd("Page.navigate", url=url)
        time.sleep(6.0)                       # the art queue has to drain
        shots = []
        for st in STAGES:
            r = cmd("Runtime.evaluate", expression="window.__crow(%r)" % st,
                    returnByValue=True)
            print("  %-6s %s" % (st, r.get("result", {}).get("value")))
            time.sleep(1.2)
            d = cmd("Page.captureScreenshot", format="png")
            shots.append(Image.open(io.BytesIO(base64.b64decode(d["data"]))).convert("RGB"))
        sheet = Image.new("RGB", (W, (H + 26) * len(shots)), (28, 12, 48))
        d = ImageDraw.Draw(sheet)
        for i, (im, st) in enumerate(zip(shots, STAGES)):
            sheet.paste(im, (0, i * (H + 26)))
            d.text((8, i * (H + 26) + H + 6), st, fill=(255, 242, 222))
        sheet.save(out)
        print("wrote", out, sheet.size)
    finally:
        proc.kill()


if __name__ == "__main__":
    main()
