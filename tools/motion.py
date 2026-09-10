# -*- coding: utf-8 -*-
"""Two frames from ONE run, so you can see what changes while it is on screen.

    python tools/motion.py 1700

mapshot.py restarts the run for every distance, which makes it useless for this:
the settle drift between two runs is tens of metres and swamps whatever you were
trying to compare. A panel that keeps its identity should appear SHIFTED between
two frames of the same run; a panel that swaps picture under the player's eye
appears REPLACED. Telling those apart needs both frames from one continuous run,
and the gap between them measured rather than assumed -- the game reports its own
odometer, so it is read off the screen rather than computed from the delay."""
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


def main():
    dist = sys.argv[1] if len(sys.argv) > 1 else '1700'
    gap = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    os.makedirs(OUT, exist_ok=True)
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    prof = os.path.join(os.environ.get('TEMP', '.'), 'cdp-motion-%d' % port)
    p = subprocess.Popen(
        [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox', '--mute-audio',
         '--hide-scrollbars', '--disable-background-timer-throttling',
         '--remote-debugging-port=%d' % port, '--remote-allow-origins=*',
         '--user-data-dir=' + prof, 'about:blank'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        ws = websocket.create_connection(tgt['webSocketDebuggerUrl'], timeout=60)
        n = [0]

        def call(method, params=None):
            n[0] += 1
            ws.send(json.dumps({'id': n[0], 'method': method, 'params': params or {}}))
            end = time.time() + 25
            while time.time() < end:
                m = json.loads(ws.recv())
                if m.get('id') == n[0]:
                    return m.get('result', {})
            raise SystemExit('timed out: ' + method)

        call('Emulation.setDeviceMetricsOverride',
             {'width': 900, 'height': 420, 'deviceScaleFactor': 2, 'mobile': True})
        call('Page.enable')
        call('Page.navigate',
             {'url': 'http://127.0.0.1:8899/index.html?noboot=1&dist=%s' % dist})
        time.sleep(10)
        for kind in ('mousePressed', 'mouseReleased'):
            call('Input.dispatchMouseEvent', {'type': kind, 'x': 450, 'y': 210,
                                              'button': 'left', 'clickCount': 1,
                                              'buttons': 1 if kind == 'mousePressed' else 0})
            time.sleep(0.05)
        time.sleep(1.6)
        made = []
        for i in (0, 1):
            r = call('Page.captureScreenshot', {'format': 'png'})
            f = os.path.join(OUT, 'motion%d.png' % i)
            open(f, 'wb').write(base64.b64decode(r['data']))
            made.append(f)
            if i == 0:
                time.sleep(gap)
        print('  wrote %s' % ', '.join(os.path.relpath(f, ROOT) for f in made))
    finally:
        p.kill()


if __name__ == '__main__':
    main()
