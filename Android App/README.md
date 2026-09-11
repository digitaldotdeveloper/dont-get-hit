# DON'T GET HIT — Android app

A Capacitor 8 shell around the game in the folder above. **Nothing here edits
the game**: every build copies it out of the repo, adapts the copy for a phone,
and packs that into an APK/AAB. Work on the game stays in `../index.html` as it
always has; rebuild here to get it onto a phone.

## Build

```
npm run build                  # the committed game (git HEAD) -> dist/*.apk + *.aab
npm run build -- --worktree    # what is on disk right now instead
npm run build:debug            # debug APK, WebView inspectable from chrome://inspect
```

`dist/` gets:

| file | for |
|---|---|
| `DontGetHit-<ver>-<code>.apk` | install directly on a phone (sideload) |
| `DontGetHit-<ver>-<code>.aab` | upload to Play Console (internal testing first) |
| `DontGetHit-<ver>-<code>-mapping.txt` | R8's map; Play reads the copy inside the AAB |

**HEAD is the default** because several sessions edit the working tree at once
and a half-made edit is not something to put on a phone. The build says how
many changed paths it left out.

**Install the APK on a phone:** send it to the phone (WhatsApp, Drive, USB),
open it, allow "install unknown apps" for whatever opened it. Or with the phone
on USB debugging: `%LOCALAPPDATA%\Android\Sdk\platform-tools\adb install -r dist\<file>.apk`.

## Shipping an update ("ship it")

Everything needed is in this folder and in `%LOCALAPPDATA%\Android`; any
session on this machine can do it.

1. **Commit the game change** in the folder above -- the build takes git HEAD.
   Stage named paths only; other sessions share that working tree.
2. `npm run build` -- new `dist/*.aab`, versionCode moves on by itself.
3. `node scripts/verify.mjs` -- all checks must pass. For anything that adds to
   a screen, also look at it at **800x360**: a Samsung held sideways is 360px
   tall, and the score card overflowed there once.
4. `npm run upload -- --notes "What's new, for the testers"` -- straight to
   internal testing. (`npm run release` is steps 2 and 4 in one, with a generic
   note.)
5. `npm run play:check` -- read the internal track back; it should show the new
   versionCode as `completed`.

Pushing the game to GitHub (the web version) is a separate step and only on
request.

## Uploading from here

`keystore/play-service-account.json` is a Google service account
(`dgh-445@acoustic-shade-399714.iam.gserviceaccount.com`) invited in Play
Console with release rights on this app. It is a private key: it lives in the
gitignored `keystore/` with the upload key and must never be committed.

```
npm run play:check     # sign in and read the tracks -- changes nothing
npm run release        # build from git HEAD, then upload to internal testing
npm run upload         # upload the newest dist/*.aab only
node scripts/upload.mjs --notes "What's new text" --track internal
```

`scripts/upload.mjs` talks to the Play Developer API directly (no packages):
open an edit, upload the bundle, put it on the track, commit. Two answers Play
can give back, and what they mean:

- **"held for review"** -- other console changes (App content, the listing)
  are waiting; the release waits with them in *Publishing overview* until you
  press Send.
- **"accepted as a DRAFT"** -- a never-published app only takes drafts from the
  API; roll that one out in the console.

A 403 "The caller does not have permission" means the service account is not
invited in Play Console (*Users and permissions*) with "Release apps to testing
tracks" on this app.

## What the build changes on the way in, and why

`scripts/build-www.mjs` builds `www/` (the copy that ships):

- **An allowlist** — `index.html`, `art/`, `anim/`, `audio/`. `tools/` (100 MB),
  the docs and every working file stay out however the folder grows.
- **No MP3s.** The game asks `canPlayType` for Opus and every Android WebView
  says yes, so the MP3 set (6.5 MB) is never fetched on a phone.
- **Fonts bundled.** The page waits up to 1.4 s on `document.fonts` before it
  boots; on a phone with no signal that was a blank screen and then the wrong
  typeface. Latin + latin-ext of Archivo and Bungee, 90 KB, cached in `cache/`
  after the first build.
- **Minified** with esbuild (target Chrome 90): `index.html` 749 KB -> 267 KB.
  Source maps land in `sourcemaps/` for turning a crash report's column back
  into a line.
- **The privacy link** goes to the live policy, so it opens in the phone's
  browser and the game stays loaded behind it.
- **`src/shim.js`** goes in first. Read its comments; in short:
  fullscreen/orientation are native here, the music is `<audio>` (which a
  WebView keeps playing behind the home screen), and Back needs to know which
  panel is open.

Result: **20.2 MB of web assets -> 13.2 MB**, and a faster boot on a slowed
CPU -- see *Measured* below for how much, as a median, because single samples
of the boot swung by more than the difference.

The native side (`android/app/src/main/java/.../MainActivity.java`):
landscape only (`sensorLandscape`), immersive full screen with the bars a swipe
away, screen kept on, text zoom pinned at 100% so the phone's font size cannot
resize the HUD, no long-press buzz or selection on the WebView (holding IS the
control), WebView paused with the activity, and Back = close the open panel,
otherwise send the app to the background with the run intact. Release builds
run R8 (code + resource shrinking), and WebP/Opus/WOFF2 are stored
uncompressed in the APK (they are compressed already; zipping them again only
costs an inflate on every read).

## Check a build

```
node scripts/verify.mjs            # www/ in Chrome as a phone: 873x393 @2.75, touch, CPU 4x
node scripts/verify.mjs cache/www-plain   # an unminified twin (build-www --no-minify --out cache/www-plain)
node scripts/serve.mjs             # serve www/ to look at it in a browser
```

`verify.mjs` checks boot time, the shim (back, pause/resume of music and the
AudioContext), frame times over auto-flown runs, 404s and exceptions. Its
frame times are Chrome's *software* rasteriser on this server — they compare
builds, they are not a phone's frame rate.

The game's own asset sweep runs against `www/` too, with its root pointed here:

```
python -c "import sys; sys.path.insert(0, r'..\tools'); import assets; assets.ROOT = r'www'; sys.argv = ['assets.py']; assets.main()"
```

## Measured (2026-09-11, HEAD 513c9b5)

| | |
|---|---|
| APK (sideload, every density) | **13.71 MB** |
| AAB (Play; a phone downloads its own split) | 14.20 MB |
| web assets in the APK | 13.2 MB (the repo's shipped folders are 20.2 MB) |
| `index.html` | 749 KB -> 267 KB (91 KB compressed inside the APK) |
| native code after R8 | 904 KB of dex |
| launcher icons + splash badge | 209 KB |
| loading gate, Chrome-as-a-phone, CPU 4x, median of 7 | minified 1.84 s / 1.48 s, unminified 1.90 s / 1.56 s (two rounds) |
| `tools/assets.py` sweep of `www/` | 2042 requests, 358 files, nothing missing, no exceptions -- identical minified and not |
| `scripts/verify.mjs` | all 14 checks pass |

**Minifying is a size change, not a speed change.** The gate waits on ~250
images, not on the script, and the medians differ by about 4% -- inside the
spread of single samples (1.2-3.0 s). It stays on because it takes two-thirds
off `index.html` and the sweep finds nothing it broke; `--no-minify` turns it
off. What makes the app open quickly is that nothing comes over the network:
on the web the same gate waits on ~5 MB of downloads (the game's own figure
since `3401893`).

## Identity — decide before the first Play upload

- **Package: `com.digitaldotdeveloper.dontgethit`.** Permanent once uploaded to
  Play. Change it in `capacitor.config.json` and `android/app/build.gradle`
  (namespace + applicationId + the Java package folder) *before* that.
- **Upload key: `keystore/dgh-upload.jks`** with its passwords in
  `keystore/keystore.properties`. Gitignored. **Back the folder up** — with
  Play App Signing a lost upload key can be reset through Play support, but it
  costs days. SHA-256 `C8:0B:D3:52:67:1D:BE:D9:C6:D1:CA:E0:BA:DC:FA:70:AF:F1:14:6E:71:05:1E:B7:E6:C9:5F:50:C8:55:3F:FB`.
- **Version:** `version.json`. Each release build uses `versionCode` and then
  adds one, because Play refuses a code it has seen.
- **`allowBackup` is false** so the app matches `privacy.html` ("no cloud
  backup"). Flip both if progress should follow a player to a new phone.

## The toolchain (this machine)

- JDK 21 (Microsoft OpenJDK): `%LOCALAPPDATA%\Android\jdk-21`
- Android SDK: `%LOCALAPPDATA%\Android\Sdk` — platform 36, build-tools 36.0.0,
  platform-tools (adb)
- Gradle 8.14.3 via the wrapper, AGP 8.13, compile/target SDK 36, min SDK 24
- Node 24; Capacitor 8.5.1; esbuild 0.28.2

`build.mjs` finds the JDK and SDK there by itself (`JAVA_HOME` /
`ANDROID_HOME` override). The machine has no Android emulator (no hardware
virtualisation), so on-device testing is a real phone.

## Not done yet

- **No pause screen.** Leaving mid-run and coming back drops you straight back
  into the run. The game has no pause state to hand to; the Android side is
  ready for one (`dgh:pause` / `dgh:resume` reach the page).
- **Ads and billing.** `rewardedAd()` and `iapBuy()` in the game are the seams.
  AdMob goes in as a Capacitor plugin (`@capacitor-community/admob`) and Play
  Billing likewise; both need the Play/AdMob app IDs first.
- **Offline privacy link** — it opens the live page, so it needs a connection.
- Store listing assets beyond `store/play-icon-512.png`.

## Files

```
capacitor.config.json   app id/name, WebView colour, SystemBars hidden
version.json            versionName / versionCode
src/shim.js             the page's side of the Android shell
scripts/build.mjs       www -> cap sync -> gradle -> dist/
scripts/build-www.mjs   the game -> www/
scripts/make_icons.py   ../icon/icon-master.png -> launcher icons, splash badge, Play icon
scripts/verify.mjs      Chrome-as-a-phone checks
scripts/serve.mjs       static server for www/
android/                the native project (Capacitor 8 template, customised)
keystore/               upload key -- secret, gitignored
```
