# -*- coding: utf-8 -*-
"""Record a real-time clip of the game over CDP and save it as a GIF.

   Page.startScreencast streams frames with timestamps, so the clip keeps the
   game's real timing -- which is the whole point when the thing being judged
   is how fast it feels. Screenshot-per-frame does not: each capture stalls the
   page for ~100ms and the result plays back at the wrong speed.

     python tools/clip.py URL out.gif [seconds] [fps]
"""
import base64, io as _io, json, os, socket, subprocess, sys, time, urllib.request
import websocket
from PIL import Image

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def record(url, secs=6.0, w=420, h=900, dpr=1, scale=1.0, settle=3.0):
    """-> [(t_seconds, PIL.Image), ...] in real time from the first frame."""
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    prof = (os.environ.get('CLAUDE_JOB_DIR') or os.environ['TEMP']) + '/clip-%d' % port
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
                    if 'error' in r: raise RuntimeError(m + ': ' + json.dumps(r['error']))
                    return r.get('result', {})
        cmd('Emulation.setDeviceMetricsOverride', width=w, height=h, deviceScaleFactor=dpr, mobile=True)
        cmd('Page.enable'); cmd('Page.navigate', url=url)
        time.sleep(settle)
        cmd('Page.startScreencast', format='jpeg', quality=80,
            maxWidth=int(w*scale), maxHeight=int(h*scale), everyNthFrame=1)
        frames, t0, deadline = [], None, time.time() + secs
        ws.settimeout(5)
        while time.time() < deadline:
            try: m = json.loads(ws.recv())
            except Exception: break
            if m.get('method') != 'Page.screencastFrame': continue
            p = m['params']
            n[0] += 1
            ws.send(json.dumps({'id': n[0], 'method': 'Page.screencastFrameAck',
                                'params': {'sessionId': p['sessionId']}}))
            t = p['metadata'].get('timestamp') or time.time()
            if t0 is None: t0 = t
            frames.append((t - t0, Image.open(_io.BytesIO(base64.b64decode(p['data']))).convert('RGB')))
        try: cmd('Page.stopScreencast')
        except Exception: pass
        ws.close()
        return frames
    finally:
        proc.terminate()


def to_gif(frames, out, fps=12, secs=None):
    """Resample a timestamped capture onto an even grid so playback is real time."""
    if not frames: raise RuntimeError('no frames captured')
    span = secs if secs is not None else frames[-1][0]
    step, i, imgs = 1.0/fps, 0, []
    t = 0.0
    while t <= span:
        while i + 1 < len(frames) and frames[i+1][0] <= t: i += 1
        imgs.append(frames[i][1]); t += step
    imgs[0].save(out, save_all=True, append_images=imgs[1:],
                 duration=int(1000/fps), loop=0, optimize=True)
    return len(imgs)


if __name__ == '__main__':
    a = sys.argv[1:]
    fr = record(a[0], float(a[2]) if len(a) > 2 else 6.0)
    print(a[1], to_gif(fr, a[1], float(a[3]) if len(a) > 3 else 12), 'frames',
          '%.1fs captured, %d raw' % (fr[-1][0], len(fr)))
