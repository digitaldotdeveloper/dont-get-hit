# -*- coding: utf-8 -*-
"""Does the page ask for anything that is not there?

   A MISSING ASSET IS A SILENT FALLBACK IN THIS GAME. That is deliberate and it
   is right -- a prop that has not arrived draws as a flat block, a layer that
   is missing is simply not drawn, and a hat nobody cut leaves the chicken
   bare-headed. Nothing throws, nothing is logged, and the screen looks fine.
   Which means **looking at it proves nothing**, and the only way to know is to
   count the requests.

   It has already cost this project twice. `slotFor()` declared nine layer
   slots nobody had drawn and 404'd on every load until a verify pass caught
   them. `NEAR_SETS` then declared eighteen floor variants across nine zones,
   which 404'd sixteen times a load for as long as the art was outstanding.
   Both were found by accident. This is the script that finds them on purpose.

   It drives the real page and exercises the surfaces that request art LAZILY,
   because those are exactly the ones a casual load never touches: the shop's
   four tabs, the death card, a blast, the ride, and a late zone.

     python tools/assets.py                 # the whole sweep
     python tools/assets.py --quick         # boot and menu only
     python tools/assets.py --url <URL>     # against the live site instead

   Exit code is 1 if anything 404s, fails, or throws -- so it can gate a push.
"""
import json, os, socket, subprocess, sys, threading, time
import http.server, functools
import urllib.request

try:
    import websocket
except ImportError:
    raise SystemExit('pip install websocket-client')

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


def serve(root):
    """A quiet static server on its own port. The game is one HTML file plus
       art, so nothing here needs to be clever -- it only needs to be able to
       say 404, which is the entire point of the script."""
    port = free_port()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        # functools.partial cannot carry an attribute, so silencing the log
        # needs a subclass; without it the report is buried under two thousand
        # lines of 200 OK, which is the one thing nobody needs to read.
        def log_message(self, *a, **k): pass

    h = functools.partial(Quiet, directory=root)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


class Page(object):
    def __init__(self):
        self.port = free_port()
        prof = os.path.join(os.environ.get('TEMP', '/tmp'), 'dgh-assets-%d' % self.port)
        self.proc = subprocess.Popen(
            [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox', '--mute-audio',
             '--hide-scrollbars', '--remote-debugging-port=%d' % self.port,
             '--remote-allow-origins=*', '--user-data-dir=' + prof, 'about:blank'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tgt = None
        for _ in range(80):
            try:
                tabs = json.load(urllib.request.urlopen(
                    'http://127.0.0.1:%d/json' % self.port, timeout=2))
                tgt = next((t for t in tabs if t['type'] == 'page'), None)
                if tgt: break
            except Exception:
                pass
            time.sleep(0.25)
        if not tgt:
            raise SystemExit('devtools never came up')
        self.ws = websocket.create_connection(tgt['webSocketDebuggerUrl'], timeout=60)
        self.n = 0
        self.bad, self.exc, self.req = [], [], []
        self.wanted = {}          # requestId -> (url, initiator)

    def cmd(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': method, 'params': params}))
        while True:
            m = json.loads(self.ws.recv())
            self._note(m)
            if m.get('id') == self.n:
                if 'error' in m:
                    raise RuntimeError(method + ': ' + json.dumps(m['error']))
                return m.get('result', {})

    def _note(self, m):
        meth = m.get('method')
        if meth == 'Network.requestWillBeSent':
            p = m['params']
            # the initiator's top frame is what turns "art/bg/near2.webp is
            # missing" into "line 9948 asked for it"
            init = p.get('initiator') or {}
            where = ''
            st = (init.get('stack') or {}).get('callFrames') or []
            if st:
                f = st[0]
                where = '%s:%s' % (f.get('functionName') or '(top level)', f.get('lineNumber'))
            elif init.get('url'):
                where = '%s:%s' % (init['url'].split('/')[-1], init.get('lineNumber', '?'))
            else:
                # A CSS background has no JS stack and no url of its own -- it
                # comes off the parser -- so the type is all there is. Saying
                # "parser" is still worth more than saying nothing: it points
                # at markup or a style attribute rather than at a loader.
                where = init.get('type') or '?'
            self.wanted[p['requestId']] = (p['request']['url'], where)
            self.req.append(p['request']['url'])
        elif meth == 'Network.responseReceived':
            st = m['params']['response']['status']
            if st >= 400:
                u, w = self.wanted.get(m['params']['requestId'], (m['params']['response']['url'], ''))
                self.bad.append((st, u, w))
        elif meth == 'Network.loadingFailed':
            p = m['params']
            if p.get('type') != 'Preflight' and not p.get('canceled'):
                u, w = self.wanted.get(p['requestId'], ('?', ''))
                self.bad.append((p.get('errorText', 'FAILED'), u, w))
        elif meth == 'Runtime.exceptionThrown':
            d = m['params']['exceptionDetails']
            t = (d.get('exception') or {}).get('description') or d.get('text')
            self.exc.append((t or '').split('\n')[0])

    def pump(self, secs):
        end = time.time() + secs
        self.ws.settimeout(0.25)
        while time.time() < end:
            try:
                self._note(json.loads(self.ws.recv()))
            except Exception:
                pass
        self.ws.settimeout(60)

    def ev(self, expr):
        r = self.cmd('Runtime.evaluate', expression=expr, returnByValue=True,
                     awaitPromise=True)
        return (r.get('result') or {}).get('value')

    def close(self):
        try: self.ws.close()
        except Exception: pass
        self.proc.kill()


def main():
    quick = '--quick' in sys.argv
    url = None
    if '--url' in sys.argv:
        url = sys.argv[sys.argv.index('--url') + 1]

    srv = None
    if not url:
        srv, port = serve(ROOT)
        url = 'http://127.0.0.1:%d/index.html' % port

    p = Page()
    p.cmd('Emulation.setDeviceMetricsOverride', width=900, height=420,
          deviceScaleFactor=2, mobile=True)
    p.cmd('Page.enable'); p.cmd('Network.enable'); p.cmd('Runtime.enable')

    def go(q, wait=3.0):
        p.cmd('Page.navigate', url=url + '?' + q + '&cb=%d' % (time.time()*1000))
        p.pump(wait)

    def gate():
        for _ in range(160):
            if 'gone' in str(p.ev("document.getElementById('boot').className")):
                return
            p.pump(0.3)

    # ---- a cold load, all the way through the gate
    go('dbg=1', 1.0); gate(); p.pump(2.5)
    print('  boot + menu           %4d requests' % len(p.req))

    if not quick:
        p.ev("localStorage.setItem('dgh.played','1');"
             "localStorage.setItem('dgh_eggs','90000');"
             "localStorage.setItem('dgh.best.v2','4000')")
        go('dbg=1', 1.0); gate(); p.pump(2.0)

        # THE SHOP'S TABS ARE THE POINT. Everything in them is a CSS background
        # on a display:none pane, so a cold load never asks for any of it --
        # which is exactly how a missing icon hides.
        for tab in ('veh', 'pow', 'app', 'store'):
            p.ev("document.querySelector('.door[data-tab=\"%s\"],.tab[data-tab=\"%s\"]')"
                 "?.click()" % (tab, tab))
            p.pump(1.2)
        print('  the four shop tabs    %4d requests' % len(p.req))

        # a run, the death card, and a blast -- the card warms art nothing else does
        p.ev("document.getElementById('shopBack')?.click()")
        p.pump(0.4)
        p.ev("DGH.startQuick()"); p.pump(2.0)
        p.ev("DGH.game.spawnT=1e9;DGH.game.crowT=1e9;DGH.game.obstacles.length=0;"
             "DGH.game.invuln=0;DGH.game.softLeft=0;DGH.game.dist=900*60;DGH.die(null)")
        p.pump(2.6)
        p.ev("document.querySelector('[data-tnt=\"2\"]')?.click()")
        p.pump(4.5)
        print('  a run, death, a blast %4d requests' % len(p.req))

        # every vehicle, and a late zone -- these load their own art on pickup
        for z in ('terr', 'empire', 'deep', 'lab'):
            go('dbg=1&noboot=1&auto=1&demo=1&zone=' + z, 3.2)
        p.ev("DGH.startQuick()"); p.pump(0.6)
        for v in ('trolley', 'ufo', 'rocket', 'hopper', 'spoon', 'toaster'):
            p.ev("DGH.startRide && DGH.startRide('%s')" % v); p.pump(0.9)
        print('  zones + every vehicle %4d requests' % len(p.req))

    seen = sorted(set(p.req))
    print()
    print('  %d requests, %d distinct' % (len(p.req), len(seen)))
    ok = True
    if p.bad:
        ok = False
        print('  %d MISSING:' % len(p.bad))
        for st, u, w in sorted(set(p.bad)):
            print('    %-4s %-58s asked for by %s' % (st, u.split('?')[0][-58:], w or '?'))
    else:
        print('  nothing missing')
    if p.exc:
        ok = False
        print('  %d EXCEPTIONS:' % len(p.exc))
        for e in sorted(set(p.exc))[:8]:
            print('    ' + e[:110])
    else:
        print('  no exceptions')
    p.close()
    if srv: srv.shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
