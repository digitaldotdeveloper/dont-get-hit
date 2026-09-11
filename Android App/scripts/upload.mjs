/* Uploads a build to Google Play through the Play Developer API, as the
   service account whose key is keystore/play-service-account.json.

     node scripts/upload.mjs --check              prove the key works; changes nothing
     node scripts/upload.mjs                      newest dist/*.aab -> internal testing
     node scripts/upload.mjs --aab <file> --track internal --notes "What's new"

   The service account must be INVITED in Play Console (Users and permissions)
   with "Release apps to testing tracks" on this app. Without that, every call
   is 403 "The caller does not have permission" -- which is exactly what the
   Rachidi Home app's key gets. No dependencies: the OAuth token is a JWT
   signed with node:crypto. */
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const KEY = path.join(APP, 'keystore', 'play-service-account.json');
const PKG = JSON.parse(fs.readFileSync(path.join(APP, 'capacitor.config.json'), 'utf8')).appId;
const API = `https://androidpublisher.googleapis.com/androidpublisher/v3/applications/${PKG}`;
const UPLOAD = `https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/${PKG}`;

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const b64url = b => Buffer.from(b).toString('base64').replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_');
let AUTH = '';

async function signIn() {
  if (!fs.existsSync(KEY)) throw new Error(`no key at ${KEY} -- see README.md, "Uploading from here"`);
  const sa = JSON.parse(fs.readFileSync(KEY, 'utf8'));
  const now = Math.floor(Date.now() / 1000);
  const head = b64url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const claim = b64url(JSON.stringify({ iss: sa.client_email, aud: sa.token_uri, iat: now, exp: now + 3600,
                                        scope: 'https://www.googleapis.com/auth/androidpublisher' }));
  const sig = b64url(crypto.createSign('RSA-SHA256').update(`${head}.${claim}`).sign(sa.private_key));
  const r = await fetch(sa.token_uri, { method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                                assertion: `${head}.${claim}.${sig}` }) });
  const j = await r.json();
  if (!r.ok) throw new Error(`sign-in: ${r.status} ${j.error_description || j.error}`);
  AUTH = j.access_token;
  return sa.client_email;
}

async function call(method, url, body) {
  const r = await fetch(url, { method,
    headers: { Authorization: `Bearer ${AUTH}`, ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : (method === 'POST' ? '' : undefined) });
  const text = await r.text();
  let j = {};
  try { j = text ? JSON.parse(text) : {}; } catch {}
  if (!r.ok) throw new Error(`${method} ${url.replace(API, '')}: ${r.status} ${j.error?.message || text.slice(0, 300)}`);
  return j;
}

/* Resumable, because a simple media upload is meant for small files and a
   bundle is 14 MB: one POST opens a session, one PUT sends the bytes. */
async function uploadBundle(editId, file) {
  const bytes = fs.readFileSync(file);
  const open = await fetch(`${UPLOAD}/edits/${editId}/bundles?uploadType=resumable`, { method: 'POST', body: '',
    headers: { Authorization: `Bearer ${AUTH}`, 'X-Upload-Content-Type': 'application/octet-stream',
               'X-Upload-Content-Length': String(bytes.length) } });
  if (!open.ok) throw new Error(`upload (open): ${open.status} ${(await open.text()).slice(0, 300)}`);
  const put = await fetch(open.headers.get('location'), { method: 'PUT', body: bytes,
    headers: { Authorization: `Bearer ${AUTH}`, 'Content-Type': 'application/octet-stream' } });
  const text = await put.text();
  if (!put.ok) throw new Error(`upload: ${put.status} ${text.slice(0, 400)}`);
  return JSON.parse(text);                                   // { versionCode, sha1, sha256 }
}

function newestAab() {
  const dist = path.join(APP, 'dist');
  const all = fs.existsSync(dist) ? fs.readdirSync(dist).filter(f => f.endsWith('.aab')) : [];
  if (!all.length) throw new Error('no .aab in dist/ -- run npm run build first');
  return path.join(dist, all.sort((a, b) => fs.statSync(path.join(dist, b)).mtimeMs - fs.statSync(path.join(dist, a)).mtimeMs)[0]);
}

async function commit(editId) {
  try { return await call('POST', `${API}/edits/${editId}:commit`); }
  catch (e) {
    // Other console changes (App content, listing) waiting on review block an
    // automatic send; the release is then held with them in Publishing overview.
    if (!/changesNotSentForReview/.test(e.message)) throw e;
    await call('POST', `${API}/edits/${editId}:commit?changesNotSentForReview=true`);
    console.log('  NOTE: held for review with your other changes -- Play Console > Publishing overview > Send changes');
  }
}

const who = await signIn();
console.log(`signed in as ${who}\napp ${PKG}`);
const edit = await call('POST', `${API}/edits`);
let done = false;
try {
  if (argv.includes('--check')) {
    const { tracks = [] } = await call('GET', `${API}/edits/${edit.id}/tracks`);
    for (const t of tracks)
      console.log(`  ${t.track.padEnd(12)} ` + ((t.releases || []).map(r =>
        `${r.status} [${(r.versionCodes || []).join(',')}] ${r.name || ''}`).join(' | ') || '(no releases)'));
    console.log('the key works: signed in, opened an edit, read the tracks. Nothing was changed.');
  } else {
    const file = opt('--aab', newestAab());
    const track = opt('--track', 'internal');
    console.log(`uploading ${path.basename(file)} (${(fs.statSync(file).size / 1048576).toFixed(2)} MB) ...`);
    const bundle = await uploadBundle(edit.id, file);
    console.log(`  accepted: versionCode ${bundle.versionCode}`);
    const notes = opt('--notes', `Test build ${bundle.versionCode}.`);
    const release = status => ({ track, releases: [{ status, versionCodes: [String(bundle.versionCode)],
                                                     releaseNotes: [{ language: 'en-US', text: notes }] }] });
    await call('PUT', `${API}/edits/${edit.id}/tracks/${track}`, release('completed'));
    try { await commit(edit.id); }
    catch (e) {
      // A never-published app only takes DRAFT releases through the API.
      if (!/draft/i.test(e.message)) throw e;
      await call('PUT', `${API}/edits/${edit.id}/tracks/${track}`, release('draft'));
      await commit(edit.id);
      console.log('  NOTE: Play only accepted it as a DRAFT -- Play Console > Internal testing > Edit release > Roll out');
    }
    done = true;
    console.log(`done: versionCode ${bundle.versionCode} is on the ${track} track`);
  }
} finally {
  if (!done) await call('DELETE', `${API}/edits/${edit.id}`).catch(() => {});
}
