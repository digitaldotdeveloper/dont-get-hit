# -*- coding: utf-8 -*-
"""Photograph the map from inside the running game, at any distance.

    python -m http.server 8899          # from the project root
    python tools/mapshot.py 120 600 1100 1700 2200 2700 3200 3700 4200

Every fault found so far was found by a person playing to a spot and taking a
screenshot on their phone, which is slow, misses most of the map, and only ever
catches the places somebody happened to fly past. This flies to each distance
and takes the picture.

TWO FLAGS MAKE IT WORK, and both are already in the game:

  ?noboot   removes the loading gate. The gate advances on requestAnimationFrame
            and headless Chrome throttles that, so without this every shot is
            the loading screen frozen at 97% -- which is what fifty captured
            copies of the title screen looked like the last time this was tried.
  ?dist=N   starts the odometer at N metres. It also needs the run STARTED:
            the preset only takes effect through startQuick(), so the title
            screen is skipped by calling it rather than by faking a tap."""
import base64
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tools', '_mapshots')
BASE = 'http://127.0.0.1:8899/index.html'


def shoot(dists, w=900, h=420, dpr=2, settle=2.4, load=3.0):
    os.makedirs(OUT, exist_ok=True)
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    prof = os.path.join(os.environ.get('TEMP', '.'), 'cdp-mapshot-%d' % port)
    p = subprocess.Popen(
        [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox', '--mute-audio',
         '--hide-scrollbars', '--disable-background-timer-throttling',
         '--remote-debugging-port=%d' % port, '--remote-allow-origins=*',
         '--user-data-dir=' + prof, 'about:blank'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    made = []
    try:
        tgt = None
        for _ in range(80):
            try:
                tabs = json.load(urllib.request.urlopen(
                    'http://127.0.0.1:%d/json' % port, timeout=2))
                tgt = next((t for t in tabs if t['type'] == 'page'), None)
                if tgt:
                    break
            except Exception:
                pass
            time.sleep(0.25)
        if not tgt:
            raise SystemExit('devtools never came up')
        ws = websocket.create_connection(tgt['webSocketDebuggerUrl'], timeout=60)
        n = [0]

        def call(method, params=None, patience=25):
            n[0] += 1
            ws.send(json.dumps({'id': n[0], 'method': method, 'params': params or {}}))
            end = time.time() + patience
            while time.time() < end:
                try:
                    m = json.loads(ws.recv())
                except Exception:
                    break
                if m.get('id') == n[0]:
                    return m.get('result', {})
            raise SystemExit('CDP call timed out: %s' % method)

        call('Emulation.setDeviceMetricsOverride',
             {'width': w, 'height': h, 'deviceScaleFactor': dpr, 'mobile': True})
        call('Page.enable')
        for d in dists:
            call('Page.navigate', {'url': '%s?noboot=1&dist=%s' % (BASE, d)})
            time.sleep(load)
            for kind in ('mousePressed', 'mouseReleased'):
                call('Input.dispatchMouseEvent',
                     {'type': kind, 'x': w // 2, 'y': h // 2, 'button': 'left',
                      'clickCount': 1, 'buttons': 1 if kind == 'mousePressed' else 0})
                time.sleep(0.05)
            time.sleep(settle)
            r = call('Page.captureScreenshot', {'format': 'png'})
            f = os.path.join(OUT, 'm%s.png' % d)
            open(f, 'wb').write(base64.b64decode(r['data']))
            made.append(f)
            print('  %5sm -> %s' % (d, os.path.relpath(f, ROOT)))
    finally:
        p.kill()
    return made


if __name__ == '__main__':
    ds = [a for a in sys.argv[1:] if not a.startswith('-')]
    shoot(ds or ['120', '600', '1100', '1700', '2200', '2700', '3200', '3700', '4200'])
