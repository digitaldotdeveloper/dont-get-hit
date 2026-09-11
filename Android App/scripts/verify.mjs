/* Probes the APK's copy of the game in desktop Chrome, set up like a phone:
   landscape 873x393 at DPR 2.75, touch, CPU slowed 4x.

     node scripts/verify.mjs [root=www] [--cpu 4] [--secs 15]

   boot    time from navigation to the loading gate opening, 404s, exceptions
   back    __dghBack() closes an open panel, and says false with none open
   sound   dgh:pause stops every <audio> that was playing and suspends the
           AudioContext, a play() while away waits, dgh:resume brings them back;
           the same through visibilitychange
   frames  frame times over an auto-flown run, and the backing-store scale the
           game's own governor settles on

   Frame times here are Chrome's SOFTWARE rasteriser on this server, so they
   compare builds with each other; they are not a phone's frame rate.
   Exits 1 on any FAIL. */
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { serve } from './serve.mjs';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const ROOT = path.resolve(APP, argv[0] && !argv[0].startsWith('--') ? argv[0] : 'www');
const CPU = +opt('--cpu', 4), SECS = +opt('--secs', 15);
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const freePort = () => new Promise(r => { const s = net.createServer(); s.listen(0, () => { const p = s.address().port; s.close(() => r(p)); }); });

let fails = 0;
const check = (cond, msg) => { console.log(`  ${cond ? 'ok  ' : 'FAIL'} ${msg}`); if (!cond) fails++; };

const srv = await serve(ROOT, 0);
const dport = await freePort();
const profile = path.join(process.env.TEMP || '/tmp', 'dgh-verify-' + dport);
const chrome = spawn(CHROME, ['--headless=new', '--no-sandbox', '--mute-audio', '--hide-scrollbars',
  '--disable-crash-reporter', '--autoplay-policy=no-user-gesture-required', '--remote-debugging-port=' + dport,
  '--remote-allow-origins=*', '--user-data-dir=' + profile, 'about:blank'], { stdio: 'ignore' });
const chromeGone = new Promise(r => chrome.once('exit', r));
/* Every run would leave its Chrome profile in %TEMP%. Deleting it the moment
   Chrome is killed fails: its child processes still hold files for a beat. So
   wait for the exit, then delete with retries. */
async function finish(code) {
  try { srv.close(); } catch {}
  chrome.kill();
  await Promise.race([chromeGone, sleep(3000)]);
  await fs.promises.rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 }).catch(() => {});
  process.exit(code);
}

try {
  let target = null;
  for (let i = 0; i < 80 && !target; i++) {
    try { target = (await (await fetch(`http://127.0.0.1:${dport}/json`)).json()).find(t => t.type === 'page'); } catch {}
    if (!target) await sleep(250);
  }
  if (!target) throw new Error('devtools never came up');
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise(r => { ws.onopen = r; });
  let id = 0;
  const pending = new Map(), bad = [], thrown = [], urls = new Map();
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id) { const p = pending.get(m.id); if (p) { pending.delete(m.id); m.error ? p.rej(new Error(m.error.message)) : p.res(m.result); } return; }
    if (m.method === 'Network.requestWillBeSent') urls.set(m.params.requestId, m.params.request.url);
    if (m.method === 'Network.responseReceived' && m.params.response.status >= 400) bad.push(`${m.params.response.status} ${m.params.response.url}`);
    if (m.method === 'Network.loadingFailed' && !m.params.canceled) bad.push(`${m.params.errorText} ${urls.get(m.params.requestId)}`);
    if (m.method === 'Runtime.exceptionThrown') thrown.push((m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text || '').split('\n')[0]);
  };
  const cmd = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
  const js = async expr => {
    const r = await cmd('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  };
  const tap = async (x, y) => {
    await cmd('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
    await sleep(80);
    await cmd('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  };

  await cmd('Page.enable'); await cmd('Runtime.enable'); await cmd('Network.enable');
  await cmd('Network.setCacheDisabled', { cacheDisabled: true });
  await cmd('Emulation.setDeviceMetricsOverride', { width: 873, height: 393, deviceScaleFactor: 2.75, mobile: true,
                                                    screenOrientation: { type: 'landscapePrimary', angle: 90 } });
  await cmd('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
  await cmd('Emulation.setCPUThrottlingRate', { rate: CPU });
  // Installed before any page script, so before the shim -- which wraps these in turn.
  await cmd('Page.addScriptToEvaluateOnNewDocument', { source: `
    window.__media = []; window.__ctxs = [];
    const p = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () { if (!__media.includes(this)) __media.push(this); return p.apply(this, arguments); };
    const C = window.AudioContext;
    if (C) { window.AudioContext = function (o) { const c = arguments.length ? new C(o) : new C(); __ctxs.push(c); return c; };
             window.AudioContext.prototype = C.prototype; }
    document.addEventListener('DOMContentLoaded', () => {
      const b = document.getElementById('boot'); if (!b) return;
      new MutationObserver(() => { if (/gone/.test(b.className) && !window.__gateAt) window.__gateAt = performance.now(); })
        .observe(b, { attributes: true, attributeFilter: ['class'] });
    });` });

  // ---- boot, the way the app opens it: no flags ----
  const base = `http://127.0.0.1:${srv.port}/index.html`;
  console.log(`${path.relative(APP, ROOT) || ROOT}  (CPU ${CPU}x, 873x393 @2.75)`);

  // --boot N: only the time to the loading gate, N cold loads, median. One
  // sample of this swung 1.75s -> 4.73s between runs on the same build.
  const BOOTS = +opt('--boot', 0);
  if (BOOTS) {
    const t = [];
    for (let i = 0; i < BOOTS; i++) {
      await cmd('Page.navigate', { url: `${base}?n=${i}` });
      let g = 0;
      for (let k = 0; k < 300 && !g; k++) { await sleep(100); g = await js('window.__gateAt || 0').catch(() => 0); }
      t.push(g);
    }
    const s = [...t].sort((a, b) => a - b);
    console.log(`  boot x${BOOTS}: median ${(s[s.length >> 1] / 1000).toFixed(2)}s  ` +
                `[${t.map(v => (v / 1000).toFixed(2)).join(' ')}]`);
    ws.close();
    await finish(t.every(v => v > 0) ? 0 : 1);
  }
  await cmd('Page.navigate', { url: base });
  let gateAt = 0;
  for (let i = 0; i < 300 && !gateAt; i++) { await sleep(100); gateAt = await js('window.__gateAt || 0').catch(() => 0); }
  const nav = await js(`(() => { const n = performance.getEntriesByType('navigation')[0];
                         return { dcl: n.domContentLoadedEventEnd, requests: performance.getEntriesByType('resource').length }; })()`);
  check(gateAt > 0, `loading gate open at ${(gateAt / 1000).toFixed(2)}s (DOMContentLoaded ${(nav.dcl / 1000).toFixed(2)}s, ${nav.requests} requests)`);
  check(await js('window.DGH_NATIVE') === 'android', `shim present: build ${JSON.stringify(await js('window.DGH_BUILD && DGH_BUILD.commit'))}`);
  check(await js(`getComputedStyle(document.body).fontFamily + '|' + document.fonts.check('900 20px Archivo') + '|' + document.fonts.check('20px Bungee')`)
          .then(s => /true\|true$/.test(s)), 'Archivo and Bungee load from the APK, not Google');

  // ---- back ----
  check(await js('window.__dghBack()') === false, 'back with nothing open -> false (the app minimises)');
  await js(`document.getElementById('cog').click()`); await sleep(500);
  const optsOpen = await js(`document.getElementById('opts').classList.contains('show')`);
  const used = await js('window.__dghBack()'); await sleep(500);
  const menuBack = await js(`!document.getElementById('opts').classList.contains('show') && document.getElementById('menu').classList.contains('show')`);
  check(optsOpen && used === true && menuBack, 'back closes the options panel onto the menu');

  // ---- sound ----
  await tap(300, 200);                    // a real touch: the escape starts, and audio with it
  await sleep(4500);
  const playing = () => js('__media.filter(m => !m.paused).length');
  const ctx = () => js(`__ctxs.map(c => c.state).join(',') || 'none'`);
  const p0 = await playing(), c0 = await ctx();
  check(p0 > 0, `music playing after the first tap (${p0} <audio>, AudioContext ${c0})`);
  await js(`dispatchEvent(new Event('dgh:pause'))`); await sleep(400);
  const p1 = await playing(), c1 = await ctx();
  check(p1 === 0 && !/running/.test(c1), `dgh:pause -> ${p1} playing, AudioContext ${c1}`);
  await js('__media[0].play()'); await sleep(300);
  check(await playing() === 0, 'a play() asked for while away waits for the return');
  await sleep(1200);                      // frames still run here; the game's actx() must not win
  check(!/running/.test(await ctx()), `the game's own resume() is held while away (AudioContext ${await ctx()})`);
  await js(`dispatchEvent(new Event('dgh:resume'))`); await sleep(600);
  const p2 = await playing(), c2 = await ctx();
  // Not "the same set": the game's music director may retire a track that was
  // fading out when the app went, and that is the director's call.
  check(p2 > 0 && /running/.test(c2), `dgh:resume -> ${p2} playing, AudioContext ${c2}`);
  await js(`Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
            document.dispatchEvent(new Event('visibilitychange'))`); await sleep(400);
  const p3 = await playing();
  await js(`Object.defineProperty(document, 'hidden', { configurable: true, get: () => false });
            document.dispatchEvent(new Event('visibilitychange'))`); await sleep(600);
  const p4 = await playing();
  check(p3 === 0 && p4 > 0, `visibilitychange: hidden -> ${p3} playing, visible -> ${p4}`);

  // ---- frames, over auto-flown runs (the ?dbg hook restarts him when he dies) ----
  await cmd('Page.navigate', { url: base + '?dbg=1&auto=1&demo=1' });
  for (let i = 0; i < 300; i++) { await sleep(100); if (await js('!!(window.DGH && DGH.game && DGH.game.mode === "play")').catch(() => false)) break; }
  await js(`(() => {
    const F = window.__F = { n: 0, sum: 0, slow: 0, worst: 0, deaths: 0 }; let last = performance.now();
    (function tick(t) {
      const dt = t - last; last = t; const g = DGH.game;
      if (g.mode === 'play' && dt < 1000) { F.n++; F.sum += dt; if (dt > 22) F.slow++; if (dt > F.worst) F.worst = dt; }
      if (g.mode === 'dead' && !F.wait) { F.wait = true; F.deaths++;
        setTimeout(() => { F.wait = false; try { DGH.deathSkip && DGH.deathSkip(); DGH.startQuick(); } catch (e) {} }, 800); }
      requestAnimationFrame(tick);
    })(last);
  })()`);
  await sleep(SECS * 1000);
  const F = await js('({ ...window.__F, dpr: DGH.metrics().DPR, cw: DGH.metrics().CW })');
  const avg = F.n ? F.sum / F.n : 0;
  check(F.n > 30, `frames in play: ${F.n}, mean ${avg.toFixed(1)}ms (${avg ? (1000 / avg).toFixed(0) : 0} fps), ` +
                  `${F.n ? (100 * F.slow / F.n).toFixed(0) : 0}% over 22ms, worst ${F.worst.toFixed(0)}ms, ` +
                  `${F.deaths} death(s), governor settled on DPR ${F.dpr} (css width ${F.cw})`);

  check(!bad.length, bad.length ? `${bad.length} failed request(s): ${[...new Set(bad)].slice(0, 5).join(' | ')}` : 'no failed requests');
  check(!thrown.length, thrown.length ? `${thrown.length} exception(s): ${[...new Set(thrown)].slice(0, 3).join(' | ')}` : 'no exceptions');
  ws.close();
} catch (e) {
  console.log('  FAIL ' + e.message); fails++;
}
console.log(fails ? `${fails} FAILED` : 'all passed');
await finish(fails ? 1 : 0);
