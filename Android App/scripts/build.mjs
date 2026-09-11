/* One command from the game to files a phone can install.

     npm run build                    www from git HEAD -> signed APK + AAB in dist/
     npm run build -- --worktree      the same, from the working tree
     npm run build:debug              debug APK: debuggable WebView (chrome://inspect)

   Uses the JDK 21 and Android SDK kept under %LOCALAPPDATA%\Android
   (JAVA_HOME / ANDROID_HOME override them). A release build uses the
   versionCode in version.json and then moves it on by one, because Play
   refuses a code it has already seen. */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildWww } from './build-www.mjs';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ANDROID = path.join(APP, 'android');
const DIST = path.join(APP, 'dist');
const WIN = process.platform === 'win32';
const LOCAL = process.env.LOCALAPPDATA || '';
const JAVA_HOME = process.env.JAVA_HOME || path.join(LOCAL, 'Android', 'jdk-21');
const ANDROID_HOME = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT || path.join(LOCAL, 'Android', 'Sdk');
const args = new Set(process.argv.slice(2));
const debug = args.has('--debug');

const env = { ...process.env, JAVA_HOME, ANDROID_HOME, ANDROID_SDK_ROOT: ANDROID_HOME,
              PATH: path.join(JAVA_HOME, 'bin') + path.delimiter + process.env.PATH };
const q = s => (/[\s"]/.test(s) ? `"${s}"` : s);
function run(line, cwd, capture = false) {
  const r = spawnSync(line, { cwd, env, shell: true, stdio: capture ? 'pipe' : 'inherit', encoding: 'utf8' });
  if (r.status !== 0) throw new Error(`"${line}" exited ${r.status}${capture ? '\n' + (r.stdout || '') + (r.stderr || '') : ''}`);
  return r.stdout || '';
}
const mb = f => (fs.statSync(f).size / 1048576).toFixed(2) + ' MB';

for (const [what, p] of [['JDK', path.join(JAVA_HOME, 'bin', WIN ? 'java.exe' : 'java')], ['Android SDK', path.join(ANDROID_HOME, 'platforms')]])
  if (!fs.existsSync(p)) throw new Error(`${what} not found at ${p} -- see README.md, "The toolchain"`);

const t0 = Date.now();
const info = await buildWww({ worktree: args.has('--worktree') });
run('npx cap sync android', APP);

// Gradle finds the SDK through local.properties (gitignored, machine-specific).
fs.writeFileSync(path.join(ANDROID, 'local.properties'),
  `sdk.dir=${ANDROID_HOME.replace(/\\/g, '\\\\').replace(/:/g, '\\:')}\n`);

const version = JSON.parse(fs.readFileSync(path.join(APP, 'version.json'), 'utf8'));
const tasks = debug ? 'assembleDebug' : 'bundleRelease assembleRelease';
console.log(`\ngradle ${tasks}  (versionCode ${version.versionCode}, ${version.versionName} (${info.commit}))`);
// By absolute path: cmd here is run with NoDefaultCurrentDirectoryInExePath, so
// a bare `gradlew.bat` is "not recognized" even from inside android/.
run(`${q(path.join(ANDROID, WIN ? 'gradlew.bat' : 'gradlew'))} ${tasks} -PdghCommit=${info.commit} --console=plain --warning-mode=summary -q`, ANDROID);

const out = path.join(ANDROID, 'app', 'build', 'outputs');
const name = `DontGetHit-${version.versionName}-${version.versionCode}${debug ? '-debug' : ''}`;
fs.mkdirSync(DIST, { recursive: true });
const made = [];
const take = (src, dst) => { fs.copyFileSync(src, path.join(DIST, dst)); made.push(path.join(DIST, dst)); };
if (debug) {
  take(path.join(out, 'apk', 'debug', 'app-debug.apk'), name + '.apk');
} else {
  const signed = path.join(out, 'apk', 'release', 'app-release.apk');
  if (fs.existsSync(signed)) take(signed, name + '.apk');
  else take(path.join(out, 'apk', 'release', 'app-release-unsigned.apk'), name + '-UNSIGNED.apk');
  take(path.join(out, 'bundle', 'release', 'app-release.aab'), name + '.aab');
  const mapping = path.join(out, 'mapping', 'release', 'mapping.txt');
  if (fs.existsSync(mapping)) take(mapping, name + '-mapping.txt');
}

// Say who signed it: the upload key for a release, the machine's debug key otherwise.
const bt = fs.readdirSync(path.join(ANDROID_HOME, 'build-tools')).sort().pop();
const apk = made.find(f => f.endsWith('.apk'));
const certs = run(`${q(path.join(ANDROID_HOME, 'build-tools', bt, WIN ? 'apksigner.bat' : 'apksigner'))} verify --print-certs ${q(apk)}`, APP, true);
const signer = (certs.match(/certificate DN: (.*)/) || [])[1] || '(unsigned)';
const sha = (certs.match(/certificate SHA-256 digest: (\w+)/) || [])[1] || '';

if (!debug) {
  version.versionCode += 1;
  fs.writeFileSync(path.join(APP, 'version.json'), JSON.stringify(version, null, 2) + '\n');
}
console.log(`\nbuilt in ${((Date.now() - t0) / 1000).toFixed(0)}s from ${info.source} ${info.commit}`);
for (const f of made) console.log(`  ${path.relative(APP, f).padEnd(48)} ${mb(f)}`);
console.log(`  signed by ${signer}${sha ? '  sha256 ' + sha.slice(0, 16) + '...' : ''}`);
if (!debug) console.log(`  next release build will be versionCode ${version.versionCode}`);
