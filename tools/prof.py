# -*- coding: utf-8 -*-
"""Frame profiler over CDP.

   Wraps the top-level draw functions (they are plain function declarations, so
   they are globals) and reports ms/frame per section plus the frame-time
   distribution, so 'it feels laggy' can be measured instead of guessed.

     python tools/prof.py [url] [seconds]
"""
import json, subprocess, sys, time, urllib.request, socket, os
import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SECTIONS = ['drawSky','drawLayers','drawStreetProps','drawGround','drawObstacles',
            'drawEggs','drawChicken','drawCellBack','drawCellFront','drawParticles',
            'drawTitle','drawPops','drawSpectators','update','render','drawBlockProps',
            'buildPlayerPose','buildLayers','makeLayer','applyTheme','swapTick']

HOOK = """
(function(){
  window.__prof = {n:0, t:{}, frames:[], long:0};
  var P = window.__prof;
  var X = window.__X;
  %NAMES%.forEach(function(name){
    var slot = X && X.fns[name];
    if(!slot){ P.t[name] = 'MISSING'; return; }
    var f = slot.get();
    if(typeof f !== 'function'){ P.t[name] = 'MISSING'; return; }
    P.t[name] = 0;
    slot.set(function(){
      var a = performance.now();
      try { return f.apply(this, arguments); }
      finally { P.t[name] += performance.now() - a; }
    });
  });
  if(X && X.fns.die){ X.fns.die.set(function(){}); }   // survive, so the run is profiled
  %OFF%.forEach(function(name){ if(X.fns[name]) X.fns[name].set(function(){}); });
  var raf = window.requestAnimationFrame.bind(window);
  var prev = performance.now();
  (function tick(){
    var now = performance.now();
    var d = now - prev; prev = now;
    if(P.n > 5){ P.frames.push(d); if(d > 24) P.long++; }
    P.n++;
    raf(tick);
  })();
})();
"""

def run(url, secs=8.0, w=420, h=900, dpr=2, cpu=1, off=()):
    port = socket.socket(); port.bind(('127.0.0.1', 0)); p = port.getsockname()[1]; port.close()
    prof = (os.environ.get('CLAUDE_JOB_DIR') or os.environ.get('TEMP')) + '/tmp/prof-%d' % p
    proc = subprocess.Popen([CHROME, '--headless=new', '--no-sandbox', '--hide-scrollbars',
        '--mute-audio', '--remote-debugging-port=%d' % p, '--remote-allow-origins=*',
        '--user-data-dir=' + prof, 'about:blank'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tgt = None
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json' % p, timeout=2))
                tgt = next((t for t in tabs if t['type'] == 'page'), None)
                if tgt: break
            except Exception: pass
            time.sleep(0.25)
        ws = websocket.create_connection(tgt['webSocketDebuggerUrl'], timeout=60)
        n = [0]
        def cmd(method, **params):
            n[0] += 1
            ws.send(json.dumps({'id': n[0], 'method': method, 'params': params}))
            while True:
                m = json.loads(ws.recv())
                if m.get('id') == n[0]:
                    if 'error' in m: raise RuntimeError(method + ': ' + json.dumps(m['error']))
                    return m.get('result', {})
        def ev(expr):
            r = cmd('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
            if 'exceptionDetails' in r: raise RuntimeError(json.dumps(r['exceptionDetails'])[:400])
            return r['result'].get('value')
        cmd('Emulation.setDeviceMetricsOverride', width=w, height=h, deviceScaleFactor=dpr, mobile=True)
        if cpu and cpu > 1: cmd('Emulation.setCPUThrottlingRate', rate=cpu)
        cmd('Page.enable'); cmd('Page.navigate', url=url)
        time.sleep(3.0)
        ev(HOOK.replace('%NAMES%', json.dumps(SECTIONS)).replace('%OFF%', json.dumps(list(off))))
        time.sleep(secs)
        out = ev("JSON.stringify({t:__prof.t, n:__prof.n, long:__prof.long,"
                 " frames:__prof.frames, obs:(__X.game.obstacles||[]).length,"
                 " mode:__X.game.mode, speed:__X.game.speed, runT:__X.game.runT,"
                 " dpr:__X.DPR, scale:__X.SCALE,"
                 " layer:(__X.layers||[]).map(l=>l.tile.canvas.width+'x'+l.tile.canvas.height)})")
        ws.close()
        return json.loads(out)
    finally:
        proc.terminate()

if __name__ == '__main__':
    a = sys.argv[1:]
    url = a[0] if a else 'http://127.0.0.1:8899/index.html?auto=1'
    secs = float(a[1]) if len(a) > 1 else 8.0
    cpu = float(a[2]) if len(a) > 2 else 1
    d = run(url, secs, cpu=cpu)
    print('cpu throttle x%g' % cpu)
    fr = sorted(d['frames'])
    if not fr: print('no frames'); sys.exit(1)
    def pct(q): return fr[min(len(fr)-1, int(len(fr)*q))]
    print('mode=%s runT=%.1f speed=%.0f obstacles=%d' % (d.get('mode'), d.get('runT') or 0, d.get('speed') or 0, d.get('obs') or 0))
    print('frames=%d  avg=%.2fms  p50=%.2f  p90=%.2f  p99=%.2f  max=%.2f  >24ms=%d (%.1f%%)'
          % (len(fr), sum(fr)/len(fr), pct(.5), pct(.9), pct(.99), fr[-1], d['long'], 100.0*d['long']/len(fr)))
    print('%-18s %8s %8s' % ('section', 'ms/frame', 'total ms'))
    for k, v in sorted(d['t'].items(), key=lambda kv: -(kv[1] if isinstance(kv[1], float) else -1)):
        if v == 'MISSING': print('%-18s   MISSING' % k); continue
        print('%-18s %8.3f %8.1f' % (k, v/max(1, len(fr)), v))
