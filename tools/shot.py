# -*- coding: utf-8 -*-
"""Screenshot through the DevTools protocol with real device emulation.

   Chrome's --screenshot flag ignores --window-size for layout: the page is laid
   out at 500px regardless and the image is then cropped to the window, which
   chops the right-hand side off and looks exactly like a layout bug. Setting
   the metrics over CDP actually resizes the viewport."""
import base64, json, subprocess, sys, time, urllib.request, socket, os
import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def shot(url, out, w=420, h=900, dpr=2, wait=3.0, full=False):
    port = free_port()
    prof = os.environ['CLAUDE_JOB_DIR'] + '/tmp/cdp-profile-%d' % port
    proc = subprocess.Popen([CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
        '--hide-scrollbars', '--mute-audio', '--remote-debugging-port=%d' % port, '--remote-allow-origins=*',
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
        if not tgt: raise RuntimeError('devtools never came up')

        ws = websocket.create_connection(tgt['webSocketDebuggerUrl'], timeout=30)
        n = [0]
        def cmd(method, **params):
            n[0] += 1
            ws.send(json.dumps({'id': n[0], 'method': method, 'params': params}))
            while True:
                m = json.loads(ws.recv())
                if m.get('id') == n[0]:
                    if 'error' in m: raise RuntimeError(method + ': ' + json.dumps(m['error']))
                    return m.get('result', {})

        cmd('Emulation.setDeviceMetricsOverride', width=w, height=h,
            deviceScaleFactor=dpr, mobile=True)
        cmd('Page.enable')
        # Collect every distinct error the page throws, installed BEFORE the
        # game's own script runs. Worth having by default: the game's
        # window.onerror keeps only the FIRST error and only in a DOM panel, and
        # an exception thrown from inside an update fires every frame without
        # ever showing up in a screenshot. Read window.__errs afterwards.
        cmd('Page.addScriptToEvaluateOnNewDocument', source="""
            window.__errs = [];
            addEventListener('error', e => {
              const k = (e.message||'') + '@' + (e.lineno||0) + ':' + (e.colno||0);
              if(!window.__errs.some(x => x.k === k))
                window.__errs.push({k, m:e.message, l:e.lineno, c:e.colno});
            });
            addEventListener('unhandledrejection', e => {
              const m = 'PROMISE ' + (e.reason && e.reason.message || e.reason);
              if(!window.__errs.some(x => x.k === m)) window.__errs.push({k:m, m});
            });
        """)
        cmd('Page.navigate', url=url)
        time.sleep(wait)
        args = {'format': 'png'}
        if full: args['captureBeyondViewport'] = True
        res = cmd('Page.captureScreenshot', **args)
        open(out, 'wb').write(base64.b64decode(res['data']))
        errs = cmd('Runtime.evaluate',
                   expression='JSON.stringify((window.__errs||[]).map('
                              'e=>e.m+" @"+e.l+":"+e.c))',
                   returnByValue=True)['result'].get('value')
        if errs and errs != '[]': print('ERRORS:', errs[:600])
        m = cmd('Runtime.evaluate', expression=
            "innerWidth+'x'+innerHeight+' scroll='+document.documentElement.scrollWidth"
            "+'x'+document.documentElement.scrollHeight", returnByValue=True)
        print('%-22s %s' % (os.path.basename(out), m['result']['value']))
        ws.close()
    finally:
        proc.terminate()

if __name__ == '__main__':
    a = sys.argv[1:]
    shot(a[0], a[1],
         int(a[2]) if len(a) > 2 else 420,
         int(a[3]) if len(a) > 3 else 900,
         2, float(a[4]) if len(a) > 4 else 3.0,
         full=(len(a) > 5 and a[5] == 'full'))
