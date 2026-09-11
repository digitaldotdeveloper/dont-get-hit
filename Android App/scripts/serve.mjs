/* Serves www/ (or any folder) the way Capacitor serves it inside the APK --
   same-origin, byte ranges for <audio> -- so the phone's copy of the game can
   be opened and probed in a desktop browser.

     node scripts/serve.mjs [root] [port]      port 0 = any free port

   verify.mjs imports serve() rather than running this. */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ogg': 'audio/ogg', '.mp3': 'audio/mpeg', '.woff2': 'font/woff2',
};

export function serve(root, port = 0) {
  root = path.resolve(root);
  const srv = http.createServer((req, res) => {
    let rel;
    try { rel = decodeURIComponent(new URL(req.url, 'http://x').pathname); }
    catch { res.writeHead(400); return res.end(); }
    const file = path.join(root, rel === '/' ? 'index.html' : rel);
    if (path.relative(root, file).startsWith('..')) { res.writeHead(403); return res.end(); }
    fs.stat(file, (err, st) => {
      if (err || !st.isFile()) { res.writeHead(404); return res.end('not found'); }
      const head = { 'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream',
                     'Cache-Control': 'no-store', 'Accept-Ranges': 'bytes' };
      const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || '');
      if (m && (m[1] || m[2])) {
        const start = m[1] ? +m[1] : Math.max(0, st.size - +m[2]);
        const end = m[1] && m[2] ? Math.min(+m[2], st.size - 1) : st.size - 1;
        res.writeHead(206, { ...head, 'Content-Range': `bytes ${start}-${end}/${st.size}`, 'Content-Length': end - start + 1 });
        return fs.createReadStream(file, { start, end }).pipe(res);
      }
      res.writeHead(200, { ...head, 'Content-Length': st.size });
      fs.createReadStream(file).pipe(res);
    });
  });
  return new Promise(resolve => srv.listen(port, '127.0.0.1',
    () => resolve({ port: srv.address().port, root, close: () => srv.close() })));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const s = await serve(process.argv[2] || path.join(APP, 'www'), +(process.argv[3] || 0));
  console.log(`serving ${s.root} at http://127.0.0.1:${s.port}/`);
}
