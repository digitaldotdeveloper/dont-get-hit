/* Second pass: sample the run once a second and report the shape of the ramp. */
import { spawn } from 'node:child_process';
import http from 'node:http'; import fs from 'node:fs';
import path from 'node:path'; import net from 'node:net';
import { fileURLToPath } from 'node:url';

const ROOT = process.argv[2] || path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const CHROME='C:/Program Files/Google/Chrome/Application/chrome.exe';
const MIME={'.html':'text/html','.js':'text/javascript','.webp':'image/webp','.png':'image/png','.mp3':'audio/mpeg','.ogg':'audio/ogg'};
const freePort=()=>new Promise(r=>{const s=net.createServer();s.listen(0,()=>{const p=s.address().port;s.close(()=>r(p));});});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

const port=await freePort();
http.createServer((q,s)=>{const u=decodeURIComponent(q.url.split('?')[0]);
  fs.readFile(path.join(ROOT,u==='/'?'index.html':u),(e,d)=>{ if(e){s.writeHead(404);return s.end();}
    s.writeHead(200,{'Content-Type':MIME[path.extname(u)]||'application/octet-stream'});s.end(d);});}).listen(port);

const dport=await freePort();
const chrome=spawn(CHROME,['--headless=new','--no-sandbox','--mute-audio','--hide-scrollbars','--disable-gpu',
  '--remote-debugging-port='+dport,'--remote-allow-origins=*','--user-data-dir='+path.join(process.env.TEMP,'dgh-p2-'+dport),'about:blank'],{stdio:'ignore'});
let t=null; for(let i=0;i<80&&!t;i++){ try{ t=(await (await fetch(`http://127.0.0.1:${dport}/json`)).json()).find(x=>x.type==='page'); }catch{} if(!t) await sleep(250); }
const ws=new WebSocket(t.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
let id=0; const P=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&P.has(m.id)){const{res,rej}=P.get(m.id);P.delete(m.id); m.error?rej(new Error(JSON.stringify(m.error))):res(m.result);}};
const cmd=(m,p={})=>new Promise((res,rej)=>{const i=++id;P.set(i,{res,rej});ws.send(JSON.stringify({id:i,method:m,params:p}));});
const ev=async x=>{const r=await cmd('Runtime.evaluate',{expression:x,returnByValue:true,awaitPromise:true});
  if(r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description||'threw'); return r.result.value;};

await cmd('Emulation.setDeviceMetricsOverride',{width:900,height:420,deviceScaleFactor:2,mobile:true});
await cmd('Page.enable');
await cmd('Page.navigate',{url:`http://127.0.0.1:${port}/index.html?dbg=1&noboot=1`});
await sleep(4000);
for(let i=0;i<40;i++){ if(await ev('!!window.DGH').catch(()=>0)) break; await sleep(500); }

// geometry + a one-second sampler that plays with a generous "stay in the opening" pilot
await ev(`(()=>{
  const D=window.DGH, BIRD_H=142;
  const S=window.__S={ geom:{}, samples:[], zones:{}, obKeys:{}, truckRuns:0, runs:0 };
  // band geometry, read off a live obstacle
  S.geom.UPM = D.UPM;
  S.geom.canvasH = document.querySelector('canvas').height;
  S.geom.canvasW = document.querySelector('canvas').width;
  function pilot(){
    const g=D.game,p=D.player;
    if(g.mode!=='play') return;
    let best=null,bd=1e9;
    for(const o of g.obstacles){const d=o.x-p.x; if(d>-60&&d<bd){bd=d;best=o;}}
    let tgt=250;
    if(best){ S.geom.band = best.band || S.geom.band;
      try{ let bi=null,bb=1e9;
        for(const f of best.spec.free(best,best.band||700)){
          const lo=f[0],hi=f[1]-BIRD_H; if(hi<lo)continue;
          const c=(lo+hi)/2,dd=Math.abs(c-p.y); if(dd<bb){bb=dd;bi=[lo,hi];}}
        if(bi) tgt=(bi[0]+bi[1])/2; }catch(e){}
    }
    for(const c of (g.crows||[])){ const dx=c.x-p.x;
      if(dx>-80&&dx<900&&Math.abs((c.y||0)-p.y)<150) tgt=(c.y||0)>p.y?Math.max(60,p.y-190):Math.min(560,p.y+190); }
    if(p.y<tgt-10) D.thrustOn(); else if(p.y>tgt+10) D.thrustOff();
  }
  let lastSample=0, deadAt=0, sawTruck=false;
  function loop(){
    const g=D.game, now=performance.now();
    pilot();
    if(g.mode==='play'){
      if(D.riding()) sawTruck=true;
      if(now-lastSample>1000){
        lastSample=now;
        S.samples.push({ t:+g.runT.toFixed(1), m:Math.round(g.dist/D.UPM), speed:Math.round(g.speed),
          obs:g.obstacles.length, onScreen:g.obstacles.filter(o=>o.x-D.player.x>-200&&o.x-D.player.x<1400).length,
          crows:(g.crows||[]).length, diff:+(g.diff||0).toFixed(2),
          // game.tier is declared and never assigned -- read the real thing the
          // way tierNow() does, off runT, or every row reports tier 0.
          tier:(g.runT<9?0:g.runT<22?1:g.runT<40?2:g.runT<64?3:4),
          y:Math.round(D.player.y) });
        for(const o of g.obstacles) S.obKeys[o.key]=(S.obKeys[o.key]||0)+0;
      }
      for(const o of g.obstacles) if(!o.__seen){ o.__seen=1; S.obKeys[o.key]=(S.obKeys[o.key]||0)+1; }
      const z = g.dist/D.UPM;
      const zn = z<560?'farm':z<1180?'terr':z<2100?'empire':z<3000?'deep':'lab';
      S.zones[zn]=(S.zones[zn]||0)+1;
    } else if(g.mode==='dead'){
      if(!deadAt){ deadAt=now; S.runs++; if(sawTruck)S.truckRuns++; sawTruck=false; }
      if(now-deadAt>1200 && S.runs<8){ deadAt=0; D.startQuick?D.startQuick():D.startRun(); }
    }
    requestAnimationFrame(loop);
  }
  D.startRun(); requestAnimationFrame(loop); return true;
})()`);

await sleep(180000);
const S = await ev('JSON.parse(JSON.stringify(window.__S))');
fs.writeFileSync('probe2.json', JSON.stringify(S,null,2));

console.log('GEOM', JSON.stringify(S.geom));
console.log('runs', S.runs, '| runs containing the truck', S.truckRuns);
console.log('\n  t(s)   metres  speed  obsOnScreen  crows  diff  tier   y');
S.samples.slice(0,70).forEach(s=>console.log(
  String(s.t).padStart(6), String(s.m).padStart(8), String(s.speed).padStart(7),
  String(s.onScreen).padStart(11), String(s.crows).padStart(7), String(s.diff).padStart(6),
  String(s.tier).padStart(5), String(s.y).padStart(5)));
console.log('\nhazard keys ever spawned:', JSON.stringify(S.obKeys));
console.log('frames spent in each zone:', JSON.stringify(S.zones));
ws.close(); chrome.kill(); process.exit(0);
