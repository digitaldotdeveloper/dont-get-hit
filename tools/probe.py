# -*- coding: utf-8 -*-
"""Run the built-in test flags and report what the page says.

   The game installs an on-screen panel (#selftest) that the ?selftest,
   ?obtest, ?audiotest and ?musictest flags write their results into, plus an
   error handler that writes into the same panel. A syntax error means the
   script never runs at all, so an empty panel is a FAILURE, not a pass.

     python tools/probe.py "http://127.0.0.1:8899/index.html?selftest=1" [wait]
"""
import json, os, socket, subprocess, sys, time, urllib.request
import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def probe(url, wait=6.0, w=420, h=900, dpr=2):
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    prof = (os.environ.get('CLAUDE_JOB_DIR') or os.environ['TEMP']) + '/probe-%d' % port
    proc = subprocess.Popen([CHROME, '--headless=new', '--no-sandbox', '--mute-audio',
        '--hide-scrollbars', '--remote-debugging-port=%d' % port, '--remote-allow-origins=*',
        '--user-data-dir=' + prof, 'about:blank'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tgt = None
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json' % port, timeout=2))
                tgt = next((t for t in tabs if t['type'] == 'page'), None)
                if tgt: break
            except Exception: pass
            time.sleep(0.25)
        ws = websocket.create_connection(tgt['webSocketDebuggerUrl'], timeout=60)
        n = [0]
        def cmd(m, **kw):
            n[0] += 1
            ws.send(json.dumps({'id': n[0], 'method': m, 'params': kw}))
            while True:
                r = json.loads(ws.recv())
                if r.get('id') == n[0]:
                    if 'error' in r: raise RuntimeError(json.dumps(r['error']))
                    return r.get('result', {})
        cmd('Emulation.setDeviceMetricsOverride', width=w, height=h, deviceScaleFactor=dpr, mobile=True)
        cmd('Page.enable'); cmd('Page.navigate', url=url)
        time.sleep(wait)
        r = cmd('Runtime.evaluate', returnByValue=True, expression=
                "(document.getElementById('selftest')||{}).textContent || '(panel empty)'")
        ws.close()
        return r['result']['value']
    finally:
        proc.terminate()


if __name__ == '__main__':
    a = sys.argv[1:]
    print(probe(a[0], float(a[1]) if len(a) > 1 else 6.0))
