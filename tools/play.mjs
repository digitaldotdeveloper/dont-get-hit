/* Drive DON'T GET HIT through CDP and report what actually happens.
   The pilot runs INSIDE the page on its own rAF, so frame timing is the
   game's, not the round-trip latency of the debugger. */
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import { fileURLToPath } from 'node:url';

const ROOT = process.argv[2] || path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const OUT  = process.argv[3] || '.';
const RUNS = +(process.argv[4] || 12);
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME = {'.html':'text/html','.js':'text/javascript','.webp':'image/webp','.png':'image/png',
  '.mp3':'audio/mpeg','.ogg':'audio/ogg','.json':'application/json','.css':'text/css'};

const freePort = () => new Promise(r => { const s=net.createServer(); s.listen(0,()=>{const p=s.address().port;s.close(()=>r(p));}); });

// ---------- static server ----------
const port = await freePort();
http.createServer((req,res)=>{
  const u = decodeURIComponent(req.url.split('?')[0]);
  const f = path.join(ROOT, u === '/' ? 'index.html' : u);
  fs.readFile(f, (e,d)=>{
    if(e){ res.writeHead(404); return res.end('nope'); }
    res.writeHead(200, {'Content-Type': MIME[path.extname(f)] || 'application/octet-stream'});
    res.end(d);
  });
}).listen(port);

// ---------- chrome ----------
const dport = await freePort();
const prof  = path.join(process.env.TEMP || '/tmp', 'dgh-play-' + dport);
const chrome = spawn(CHROME, ['--headless=new','--no-sandbox','--mute-audio','--hide-scrollbars',
  '--disable-gpu','--remote-debugging-port='+dport,'--remote-allow-origins=*',
  '--user-data-dir='+prof,'about:blank'], {stdio:'ignore'});

const sleep = ms => new Promise(r=>setTimeout(r,ms));
let target = null;
for(let i=0;i<80 && !target;i++){
  try{
    const tabs = await (await fetch(`http://127.0.0.1:${dport}/json`)).json();
    target = tabs.find(t=>t.type==='page');
  }catch{}
  if(!target) await sleep(250);
}
if(!target) { console.error('devtools never came up'); process.exit(1); }

// ---------- minimal CDP client ----------
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let msgId = 0; const pending = new Map();
ws.onmessage = ev => {
  const m = JSON.parse(ev.data);
  if(m.id && pending.has(m.id)){ const {res,rej}=pending.get(m.id); pending.delete(m.id);
    m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }
};
const cmd = (method, params={}) => new Promise((res,rej)=>{
  const id = ++msgId; pending.set(id,{res,rej});
  ws.send(JSON.stringify({id, method, params}));
});
const evalJS = async (expression) => {
  const r = await cmd('Runtime.evaluate', {expression, returnByValue:true, awaitPromise:true});
  if(r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || 'eval threw');
  return r.result.value;
};

// landscape phone: 900x420 @2x is a mid-range Android held sideways
await cmd('Emulation.setDeviceMetricsOverride', {width:900, height:420, deviceScaleFactor:2, mobile:true});
await cmd('Page.enable');
await cmd('Runtime.enable');

const consoleErrors = [];
ws.addEventListener('message', ev => {
  const m = JSON.parse(ev.data);
  if(m.method === 'Runtime.exceptionThrown')
    consoleErrors.push(m.params.exceptionDetails?.exception?.description?.split('\n')[0] || 'error');
});

await cmd('Page.navigate', {url:`http://127.0.0.1:${port}/index.html?dbg=1&noboot=1`});
await sleep(4000);

// wait for the debug hook
let ok = false;
for(let i=0;i<40 && !ok;i++){ ok = await evalJS('!!window.DGH').catch(()=>false); if(!ok) await sleep(500); }
if(!ok){ console.error('window.DGH never appeared — game did not boot'); console.error(consoleErrors.slice(0,5)); process.exit(1); }

// ---------- the pilot, installed in-page ----------
await evalJS(`(() => {
  const D = window.DGH, BIRD_H = 142;
  const R = window.__R = { runs:[], frames:0, slow:0, worst:0, fpsSamples:[], events:[] };
  let last = performance.now(), fpsAcc = 0, fpsN = 0;
  let cur = null, deadAt = 0, restarts = [];

  function freeBands(o){
    try{ const band = o.band || 700; return o.spec.free(o, band) || []; }catch(e){ return []; }
  }
  function pickTarget(){
    const g = D.game, p = D.player;
    let best = null, bestD = 1e9;
    for(const o of g.obstacles){
      const d = o.x - p.x;
      if(d > -60 && d < bestD){ bestD = d; best = o; }
    }
    let tgt = 250;
    if(best){
      const bands = freeBands(best);
      let bi = null, bd = 1e9;
      for(const f of bands){
        const lo = f[0], hi = f[1] - BIRD_H;
        if(hi < lo) continue;
        const c = (lo + hi)/2, dd = Math.abs(c - p.y);
        if(dd < bd){ bd = dd; bi = [lo,hi]; }
      }
      if(bi) tgt = (bi[0] + bi[1]) / 2;
    }
    // crows arrive horizontally and announce first — slide away from them
    for(const c of (g.crows||[])){
      const dx = c.x - p.x;
      if(dx > -80 && dx < 900 && Math.abs((c.y||0) - p.y) < 150)
        tgt = (c.y||0) > p.y ? Math.max(60, p.y - 190) : Math.min(560, p.y + 190);
    }
    return tgt;
  }

  function deathCause(){
    const g = D.game;
    const hit = g.obstacles.find(o => o.hitBy);
    if(hit) return (hit.spec && hit.spec.elec) ? 'electric:' + hit.key : 'prop:' + hit.key;
    if((g.crows||[]).some(c => c.hitBy)) return 'crow';
    return D.player.y <= 2 ? 'ground' : 'unknown';
  }

  function tick(){
    const now = performance.now(), dt = now - last; last = now;
    R.frames++;
    if(dt > 0){ fpsAcc += 1000/dt; fpsN++; if(fpsN >= 30){ R.fpsSamples.push(fpsAcc/fpsN); fpsAcc=0; fpsN=0; } }
    if(dt > 22) R.slow++;
    if(dt > R.worst) R.worst = dt;

    const g = D.game;
    if(g.mode === 'play'){
      if(!cur) cur = { t0: now, startedFrom: deadAt ? now - deadAt : null };
      const p = D.player;
      const tgt = pickTarget();
      if(p.y < tgt - 10) D.thrustOn(); else if(p.y > tgt + 10) D.thrustOff();
      cur.dist = g.dist; cur.score = g.score; cur.near = g.near;
      cur.eggs = g.runEggs; cur.combo = g.comboBest; cur.tier = g.tier;
      cur.rode = cur.rode || D.riding();
    } else if((g.mode === 'dying' || g.mode === 'dead') && cur){
      cur.cause = cur.cause || deathCause();
      cur.secs = (now - cur.t0)/1000;
      if(!cur.closed){ cur.closed = true; R.runs.push(cur); deadAt = now; }
    }
    // restart once the death card has settled
    if(g.mode === 'dead' && cur && cur.closed && now - deadAt > 1400){
      if(R.runs.length < ${RUNS}){
        /* DISMISS THE OFFER FIRST, or the next run is played with a dead button.
           Any run past 100m opens the death offer, which sets META.open, and
           thrustOn returns early on META.open -- for the full DEATH_SECS (8s),
           which is far longer than the 1.4s we wait here. Restarting without
           closing it handed the pilot a bird that could not fly: it ran along
           the ground into the first ground hazard at ~57m, and the run after
           that caught the tail of the same lockout and died at ~11m. That
           read as a three-run cycle in the game. It was this line. */
        if(D.deathSkip) D.deathSkip();
        cur = null; D.thrustOff(); D.startQuick ? D.startQuick() : D.startRun();
      }
    }
    requestAnimationFrame(tick);
  }
  D.startRun();
  requestAnimationFrame(tick);
  return true;
})()`);

// ---------- let it play, screenshotting along the way ----------
const shots = [];
async function shot(name){
  const r = await cmd('Page.captureScreenshot', {format:'png'});
  const f = path.join(OUT, name + '.png');
  fs.writeFileSync(f, Buffer.from(r.data,'base64'));
  shots.push(f);
}
await sleep(2500);  await shot('dgh-01-early');
await sleep(9000);  await shot('dgh-02-mid');
await sleep(12000); await shot('dgh-03-late');

// play until the run budget is spent (cap the wall clock)
const deadline = Date.now() + 210000;
let n = 0;
while(Date.now() < deadline){
  n = await evalJS('window.__R.runs.length').catch(()=>n);
  if(n >= RUNS) break;
  await sleep(2000);
}
await shot('dgh-04-final');

const R = await evalJS('JSON.parse(JSON.stringify(window.__R))');
R.consoleErrors = consoleErrors.slice(0,10);
R.shots = shots;
fs.writeFileSync(path.join(OUT,'dgh-results.json'), JSON.stringify(R,null,2));

// ---------- report ----------
const runs = R.runs.filter(r=>r.secs);
const fps = R.fpsSamples.length ? R.fpsSamples.reduce((a,b)=>a+b,0)/R.fpsSamples.length : 0;
const med = a => { const s=[...a].sort((x,y)=>x-y); return s.length? s[Math.floor(s.length/2)] : 0; };
console.log('\n===== DON\'T GET HIT — ' + runs.length + ' autopiloted runs =====');
console.log('frames', R.frames, '| avg fps', fps.toFixed(1), '| frames >22ms', R.slow, '(' + (100*R.slow/R.frames).toFixed(1) + '%)', '| worst frame', R.worst.toFixed(0)+'ms');
console.log('\n  #   secs    dist(m)   score   near  eggs  combo  tier  truck  cause');
runs.forEach((r,i)=>console.log(
  String(i+1).padStart(3),
  (r.secs||0).toFixed(1).padStart(6),
  Math.round(r.dist||0).toString().padStart(9),
  Math.round(r.score||0).toString().padStart(7),
  String(r.near||0).padStart(6),
  String(r.eggs||0).padStart(5),
  String(r.combo||0).padStart(6),
  String(r.tier||0).padStart(5),
  String(!!r.rode).padStart(6),
  ' ' + (r.cause||'?')));
console.log('\nmedian run', med(runs.map(r=>r.secs)).toFixed(1)+'s',
            '| median dist', Math.round(med(runs.map(r=>r.dist||0)))+'m',
            '| longest', Math.max(...runs.map(r=>r.secs)).toFixed(1)+'s');
const causes = {}; runs.forEach(r=>causes[r.cause||'?']=(causes[r.cause||'?']||0)+1);
console.log('causes:', JSON.stringify(causes));
const rs = runs.map(r=>r.startedFrom).filter(Boolean);
if(rs.length) console.log('restart gap (incl. our 1.4s wait):', Math.round(med(rs))+'ms');
if(R.consoleErrors.length) console.log('\nPAGE ERRORS:', R.consoleErrors);

ws.close(); chrome.kill(); process.exit(0);
