/* Builds www/ -- the game exactly as it ships inside the APK -- out of the
   game folder one level up. Nothing in the game folder is ever written to.

     node scripts/build-www.mjs              the committed game (git HEAD)
     node scripts/build-www.mjs --worktree   what is on disk right now
     node scripts/build-www.mjs --no-minify  skip esbuild, to bisect a problem

   HEAD is the default because several sessions edit the working tree at once,
   and a half-made edit is not something to put on a phone.

   What changes on the way in, and why each change is safe:
   - Only SHIP is copied -- an allowlist, so tools/, the handover docs and
     every working file stay out of the APK however the folder grows.
   - audio/*.mp3 goes wherever an .ogg twin exists. The game asks canPlayType
     for Opus and takes it when the answer is truthy, which every Android
     WebView gives, so the MP3 set is never fetched on a phone.
   - Google Fonts are bundled. The page waits up to 1.4s on document.fonts
     before it boots, so on a phone with no signal the fonts cost a blank
     screen and then the wrong typeface.
   - The inline script and style are minified with esbuild.
   - The favicon / manifest links go; the launcher icon is native.
   - The privacy link points at the live policy. Capacitor hands any other host
     to the phone's browser, so the game stays loaded behind it -- a second
     page inside the WebView would unload the game to show a policy.
   - src/shim.js goes in first: see the notes at the top of that file. */
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as esbuild from 'esbuild';

const APP   = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const GAME  = path.resolve(APP, '..');
const CACHE = path.join(APP, 'cache');
let WWW     = path.join(APP, 'www');        // --out moves it (an unminified twin to compare against)
const MAPS  = path.join(APP, 'sourcemaps');

const SHIP = ['index.html', 'art', 'anim', 'audio'];
const LIVE = 'https://digitaldotdeveloper.github.io/dont-get-hit/';
/* esbuild may REWRITE syntax while minifying (`a = a || b` becomes `a ||= b`),
   so the target caps what it is allowed to introduce. Chrome 90 is April 2021;
   the System WebView updates through Play and anything older is noise.
   capacitor.config.json's minWebViewVersion says the same number. */
const TARGET = 'chrome90';
const ANDROID_UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 ' +
                   '(KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36';

const git = (...a) => execFileSync('git', ['-C', GAME, ...a], { encoding: 'utf8', maxBuffer: 64 << 20 }).trim();
const kb = n => (n / 1024).toFixed(0).padStart(6) + ' KB';

function walk(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    e.isDirectory() ? walk(p, out) : out.push(p);
  }
  return out;
}
const bytes = files => files.reduce((s, f) => s + fs.statSync(f).size, 0);

/* ---------- 1. the files ---------- */
function stage(worktree) {
  if (path.relative(APP, WWW).startsWith('..')) throw new Error('refusing to clear ' + WWW);
  fs.rmSync(WWW, { recursive: true, force: true });
  fs.mkdirSync(WWW, { recursive: true });
  fs.mkdirSync(CACHE, { recursive: true });
  if (worktree) {
    // tracked + untracked-but-not-ignored: the repo's own idea of the project
    const files = git('ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', ...SHIP)
      .split('\0').filter(Boolean);
    for (const f of new Set(files)) {
      const src = path.join(GAME, f);
      if (!fs.existsSync(src)) continue;            // deleted on disk, still in the index
      const dst = path.join(WWW, f);
      fs.mkdirSync(path.dirname(dst), { recursive: true });
      fs.copyFileSync(src, dst);
    }
  } else {
    // git archive reads the object store only: no index, no working tree
    const tar = path.join(CACHE, 'head.tar');
    git('archive', '--format=tar', '-o', tar, 'HEAD', ...SHIP);
    const tarExe = process.platform === 'win32'
      ? path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'tar.exe')   // not Git's GNU tar: it reads C: as a host
      : 'tar';
    execFileSync(tarExe, ['-xf', tar, '-C', WWW]);
    fs.rmSync(tar);
  }
}

function prune() {
  const dropped = [];
  const page = fs.readFileSync(path.join(WWW, 'index.html'), 'utf8');
  for (const f of walk(WWW)) {
    const rel = path.relative(WWW, f).split(path.sep).join('/');
    const base = path.basename(f);
    let why = null;
    if (/\.mp3$/i.test(base) && fs.existsSync(f.replace(/\.mp3$/i, '.ogg'))) why = 'mp3';
    else if (/^audio\/src\//.test(rel)) why = 'audio master';
    else if (/\.bak-/.test(base) || base === 'Thumbs.db' || base === '.DS_Store') why = 'working file';
    // notes and data dumps -- but only ones the page never names, since a file
    // the game fetches can have any extension
    else if (/\.(md|py|txt|psd|kra)$/i.test(base) &&
             !page.includes(base.replace(/\.[^.]+$/, ''))) why = 'working file';
    if (why) { dropped.push({ rel, size: fs.statSync(f).size, why }); fs.rmSync(f); }
  }
  // folders the pruning emptied
  const dirs = [];
  (function collect(d) { for (const e of fs.readdirSync(d, { withFileTypes: true }))
    if (e.isDirectory()) { const p = path.join(d, e.name); collect(p); dirs.push(p); } })(WWW);
  for (const d of dirs) if (!fs.readdirSync(d).length) fs.rmdirSync(d);
  return dropped;
}

/* ---------- 2. fonts ---------- */
const fontName = u => {
  const m = u.match(/\/s\/([^/]+)\/(v\d+)\/([^/?]+)$/);
  return m ? `${m[1]}-${m[2]}-${m[3]}` : path.basename(u);
};

async function bundleFonts(html) {
  const link = html.match(/<link\b[^>]*href="(https:\/\/fonts\.googleapis\.com\/css2?\?[^"]+)"[^>]*>/i);
  if (!link) return { html, files: [] };
  const url = link[1].replace(/&amp;/g, '&');
  // Cached by URL, so only the first build of a given font set needs the network.
  const dir = path.join(CACHE, 'fonts', createHash('sha1').update(url).digest('hex').slice(0, 12));
  const cssFile = path.join(dir, 'google.css');
  if (!fs.existsSync(cssFile)) {
    const res = await fetch(url, { headers: { 'User-Agent': ANDROID_UA } });
    if (!res.ok) throw new Error(`fonts: HTTP ${res.status} for ${url} (the first build needs the network once)`);
    const css = await res.text();
    fs.mkdirSync(dir, { recursive: true });
    for (const u of new Set([...css.matchAll(/url\((https:[^)]+)\)/g)].map(m => m[1]))) {
      const r = await fetch(u);
      if (!r.ok) throw new Error(`fonts: HTTP ${r.status} for ${u}`);
      fs.writeFileSync(path.join(dir, fontName(u)), Buffer.from(await r.arrayBuffer()));
    }
    fs.writeFileSync(cssFile, css);          // last, so a half-finished download is retried
  }
  /* Latin and latin-ext only. Every word in the game is English, and a
     unicode-range block the page never uses is a file in the APK for nothing. */
  const css = fs.readFileSync(cssFile, 'utf8');
  const blocks = [...css.matchAll(/\/\*\s*([\w-]+)\s*\*\/\s*(@font-face\s*\{[^}]*\})/g)]
    .filter(m => m[1] === 'latin' || m[1] === 'latin-ext').map(m => m[2]);
  if (!blocks.length) throw new Error('fonts: no latin @font-face blocks in ' + cssFile);
  fs.mkdirSync(path.join(WWW, 'fonts'), { recursive: true });
  const files = new Set();
  const local = blocks.map(b => b.replace(/url\((https:[^)]+)\)/g, (_, u) => {
    const n = fontName(u);
    fs.copyFileSync(path.join(dir, n), path.join(WWW, 'fonts', n));
    files.add(n);
    return `url(fonts/${n})`;
  })).join('\n');
  html = html.replace(link[0], `<style>${local}</style>`)
             .replace(/<link\b[^>]*rel="preconnect"[^>]*>\s*/gi, '');
  return { html, files: [...files] };
}

/* ---------- 3. minify ---------- */
async function minify(html, mapName) {
  const warnings = [];
  const parts = html.split(/(<script\b[^>]*>[\s\S]*?<\/script>|<style\b[^>]*>[\s\S]*?<\/style>)/i);
  let js = 0;
  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 0) { parts[i] = parts[i].replace(/<!--[\s\S]*?-->/g, ''); continue; }   // markup: drop comments
    const [, open, tag, body, close] = parts[i].match(/^(<(script|style)\b[^>]*>)([\s\S]*?)(<\/\2>)$/i);
    if (tag.toLowerCase() === 'style') {
      const r = await esbuild.transform(body, { loader: 'css', minify: true, target: TARGET, charset: 'utf8' });
      warnings.push(...r.warnings);
      parts[i] = open + r.code.trim() + close;
    } else if (!/\bsrc=|\btype=/i.test(open)) {
      const r = await esbuild.transform(body, {
        loader: 'js', minify: true, target: TARGET, charset: 'utf8', legalComments: 'none',
        sourcemap: 'external', sourcefile: `index.html#script${js}`,
      });
      warnings.push(...r.warnings);
      let code = r.code.trim();
      if (/<\/script/i.test(code)) code = code.replace(/<\/script/gi, '<\\/script');   // cannot end the tag early
      // The crash reporter records file:line:col; with one line of code the column is the only
      // coordinate left, and this map is what turns it back into a place in index.html.
      fs.mkdirSync(MAPS, { recursive: true });
      fs.writeFileSync(path.join(MAPS, `${mapName}.script${js}.js.map`), r.map);
      js++;
      parts[i] = open + code + close;
    }
  }
  return { html: parts.join(''), warnings };
}

/* ---------- 4. the shim ---------- */
async function shim(info) {
  const src = fs.readFileSync(path.join(APP, 'src', 'shim.js'), 'utf8')
    .replace('__DGH_BUILD__', JSON.stringify(info));
  const r = await esbuild.transform(src, { loader: 'js', minify: true, target: TARGET, charset: 'utf8' });
  return r.code.trim();
}

/* ---------- the build ---------- */
export async function buildWww({ worktree = false, noMinify = false, out = null } = {}) {
  const t0 = Date.now();
  if (out) WWW = path.resolve(out);
  const commit = git('rev-parse', '--short', 'HEAD');
  const subject = git('log', '-1', '--format=%s');
  const dirty = git('status', '--porcelain', '--', ...SHIP).split('\n').filter(Boolean).length;
  const gameVersion = (git('show', 'HEAD:index.html').match(/const GAME_VERSION\s*=\s*'([^']+)'/) || [])[1] || '?';

  stage(worktree);
  const srcBytes = bytes(walk(WWW));
  const dropped = prune();

  const file = path.join(WWW, 'index.html');
  let html = fs.readFileSync(file, 'utf8');
  const htmlBefore = Buffer.byteLength(html);
  // The launcher icon is native. An empty data: icon stops a browser asking for
  // /favicon.ico -- the one request the asset sweep would otherwise 404 on.
  html = html.replace(/<link\b[^>]*rel="(?:icon|apple-touch-icon|manifest)"[^>]*>\s*/gi, '')
             .replace(/<title>/i, '<link rel="icon" href="data:,">$&');
  html = html.replace(/href="privacy\.html"/g, `href="${LIVE}privacy.html"`);
  const fonts = await bundleFonts(html);
  html = fonts.html;
  const tag = `${commit}${worktree && dirty ? '-dirty' : ''}`;
  let warnings = [];
  if (!noMinify) ({ html, warnings } = await minify(html, tag));
  const info = { commit: tag, subject, source: worktree ? 'worktree' : 'HEAD', gameVersion,
                 built: new Date().toISOString(), minified: !noMinify };
  const shimCode = await shim(info);
  if (!/<meta charset="utf-8">/i.test(html)) throw new Error('index.html has no <meta charset="utf-8"> to put the shim after');
  html = html.replace(/<meta charset="utf-8">/i, m => `${m}<script>${shimCode}</script>`);
  fs.writeFileSync(file, html);
  fs.writeFileSync(path.join(CACHE, 'build-info.json'), JSON.stringify(info, null, 2));

  // ---- report ----
  const outBytes = bytes(walk(WWW));
  const by = dir => bytes(walk(path.join(WWW, dir)));
  console.log(`www/ from ${info.source} ${tag} "${subject}"  (game ${gameVersion})`);
  if (!worktree && dirty) console.log(`  note: ${dirty} changed path(s) in the working tree are NOT in this build (--worktree includes them)`);
  const dropMp3 = dropped.filter(d => d.why === 'mp3');
  console.log(`  dropped ${dropMp3.length} mp3 (${kb(dropMp3.reduce((s, d) => s + d.size, 0)).trim()})` +
              (dropped.length > dropMp3.length ? `, ${dropped.length - dropMp3.length} other: ` +
                dropped.filter(d => d.why !== 'mp3').map(d => d.rel).join(', ') : ''));
  console.log(`  fonts bundled: ${fonts.files.length} files`);
  console.log(`  index.html ${kb(htmlBefore)} -> ${kb(Buffer.byteLength(html))}`);
  for (const name of ['art', 'anim', 'audio', 'fonts'])
    console.log(`  ${name.padEnd(10)} ${kb(by(name))}`);
  console.log(`  total      ${kb(srcBytes)} -> ${kb(outBytes)}  (${walk(WWW).length} files, ${((Date.now() - t0) / 1000).toFixed(1)}s)`);
  if (warnings.length) console.log(`  esbuild: ${warnings.length} warning(s), first: ${warnings[0].text}`);
  return info;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const argv = process.argv.slice(2), a = new Set(argv);
  const outAt = argv.indexOf('--out');
  buildWww({ worktree: a.has('--worktree'), noMinify: a.has('--no-minify'),
             out: outAt >= 0 ? argv[outAt + 1] : null })
    .catch(e => { console.error('build-www failed:', e.message); process.exit(1); });
}
