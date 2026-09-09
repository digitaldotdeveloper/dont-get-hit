# DON'T GET HIT — handover

Live: https://digitaldotdeveloper.github.io/dont-get-hit/
Hat picker: https://digitaldotdeveloper.github.io/dont-get-hit/chickens.html
Repo: https://github.com/digitaldotdeveloper/dont-get-hit
Local: C:\Users\it\Desktop\jj

**Landscape-only** one-button arcade flyer. **Hold to flap, release to fall.**
The bird flies with its own wings — deliberately not a jetpack, so the game reads
as its own thing rather than a Jetpack Joyride clone. Target is Android with ads
later; GitHub Pages is only the test harness.

Everything is in **index.html** plus four PNGs in `art/`. No build step.

## The character — read this before touching him

**One animated chicken assembled from five painted parts, plus interchangeable
cosmetic layers.** There are no per-outfit animations and there never should be.

### Parts (the important bit)

`art/part-bodyref.png` and `art/part-headref.png` are **cut directly out of the
reference render** (`concept_hi/run2.png`) - not redrawn. That is why the
character finally matches: it is literally the reference art. The head cut keeps
the cap, shades and chain, so it is used whenever no head/face cosmetic is
equipped; equip one and `part-head.png` (the bare head) is used instead.

The remaining parts (`part-wing`, `part-wingfold`, `part-leg`, `part-shoe`) are
generated pieces in the same style.

**There is deliberately no tail part.** The reference's tail is part of the body
silhouette, and the body cut already contains it; a separate tail was an
invention that never matched. Do not add one back.

The spread wing could not be cut from `fly.png` either - both wings overlap in
that pose, so no polygon isolates one. It stays generated.

To re-cut from a reference: flood-fill the body's cream region, dilate ~9px to
swallow its own outline, cut the head with an ellipse, erase the reference's
fist, and repaint the wing area cream inside an eroded mask so the wing can move.
The head-to-body offset is then measured from the reference itself, which is what
makes the assembly correct rather than guessed.

The older, fully generated parts
and hung on the rig by `loadPart` / `drawPart`. The rig moves the pieces; it does
not draw the character. This is why he looks like the reference — he *is* the
reference art.

Each part has `w` (width in world units) and `ax`/`ay` (the anchor, as a fraction
of the image, i.e. the point the pivot holds it by).

**How to fit a new part — do it this way, not by eye.**

1. Measure the landmark in the PNG with PIL and express it as a fraction of the
   image. Set `ax`/`ay` to that fraction, so the pivot *is* the landmark.
2. Derive the rig number from the art, not the other way round. Current values:

   | part | landmark | drives |
   |---|---|---|
   | head | skull centre `0.4324, 0.4607`, radius `0.4108·w` | `headR`, and `w = 2·headR/0.4108` |
   | wing | shoulder `0.624, 0.0852`, blade `1.16·w` | `wingA+wingB`, `w = (A+B)/1.16` |
   | tail | root `0.9985, 0.5761` | tail pivot |
   | shoe | ankle centre `0.3413` | ankle pivot |
   | body | bbox centre | `bodyRX/bodyRY` = half the art |

3. Check it with **`?align=1`**: draws the rig underneath in flat magenta with the
   painted parts over it at 70%. Any mismatch is then visible instead of guessed.

Eyeballing these cost several rounds and never converged. Measuring took one.
Because the head pivot is the skull centre, hats need no fudge offset.

Two traps that already bit:
- `ctx.rotate(t)` maps `dir(a)` to `dir(a-t)`, **not** `a+t`. The wing part must
  be rotated by `-ang`, with `rot:-0.65` squaring the asset to "straight down".
  Get this backwards and "wings up" draws wings down.
- Head cosmetics sit on the *painted* skull, not the pivot: `(-2,-8)` for the hat
  slot and `(2,-8)` for the face slot, both measured off `part-head.png`.
- The leg is ONE straight tube part reused for both bones, stretched to length by
  `drawBone` — so a new pair of legs is one image, not four.

**Every part is optional.** If an image is missing, the fully procedural chicken
draws instead (`partReady` guards every call), so the character can never vanish.
Do not delete the procedural path.

Earlier attempts, for the record: a painted *head* on a code body read as
assembled parts and was scrapped; a fully code-drawn chicken never matched the
reference. Generated per-frame sprite sheets were rejected because the character
drifts between frames.

### Cosmetic system

```
BaseChicken            owns idle / run / fly / glide / land / hit / death
├── BackPivot          (free — capes, packs; NOT a jetpack: he has wings)
├── BodyPivot          outfit
├── NeckPivot          scarf
├── HeadPivot          hats
└── FacePivot          glasses
```

A cosmetic is `{id, slot, draw(R,ctx)}` **or** `{id, slot, img, w, ox, oy, ax, ay}`
— a code drawing or a PNG, same slot, same pivot. Register with
`defineCosmetic(...)` / `cosmeticImage(id, slot, src, opts)`.

```js
equip('head','hat_bucket');  equip('face','shades_art');  unequip('back');
```

Runtime, any time. Unknown slot or missing asset is a silent no-op — a broken
cosmetic can never break the character. **Adding a cosmetic must never require
touching a pose function.** Adding a whole new slot is two lines (`SLOTS`,
`Loadout`) plus one `drawSlot` call at the right z-position in `drawChicken`.

PNG cosmetics come from Gemini Studio, keyed off flat green and trimmed to the
largest connected blob. See [[feedback-gemini-sprite-sheets]] for the prompt
rules that keep them consistent.

## Where things are (search these strings)

| What | Marker |
|---|---|
| Chicken rig constants | `const CK = {` |
| Painted parts | `const PARTS`, `loadPart`, `drawPart`, `partReady` |
| Cosmetic registry / slots | `const SLOTS`, `defineCosmetic`, `equip` |
| Cosmetic draw hook | `function drawSlot` |
| All poses | `function poseRun` … `function poseCheer` |
| Flap keyframes | `const FLAP_TRACK`, `function sampleTrack` |
| Flap-driven flight pose | `function poseFly` |
| Character renderer | `function drawChicken` |
| Wing shape | `function drawWing` |
| Death tumble + egg | `const rag = {`, `function layEgg` |
| Feathers | `function featherBurst` |
| Flight physics | `const GRAV`, `// ---- flight ----` |
| Landscape framing + rotate gate | `function resize()`, `#rotate` |
| Gates | `function spawnGate`, `OB.tower`, `OB.hanger` |
| The cage intro | `const CAGE`, `cageGeom`, `cagePose`, `updateIntro` |
| The blast | `drawBoom`, `FRAME_DATA.boom` |
| Painted panels | `function loadPanels`, `const FARM` |
| Farm hazards | `function farmProp`, `Object.assign(OB, {` |
| Gate members fill their hitbox | `crateStack`, `CAP_H` |
| Obstacles (9 code-drawn, 16 painted) | `const OB = {`, `farmProp` |
| Difficulty tiers | `function tierNow`, `function spawnPattern` |
| The angry crows | `THE ANGRY CROWS`, `updateCrows`, `drawCrowAlerts` |
| The meta shell (menu strip, shop, daily) | `THE META SHELL`, `const META = {`, `function metaBind` |
| The loading screen | `#boot`, `.bootCol`, `body.booting`, `gateStart` |

## Flight model — one system, do not add a second

Jetpack Joyride mechanics, exactly:

```
hold    -> continuous upward thrust, for as long as it is held
release -> thrust stops that frame, gravity takes over
```

**No jump impulse, no fixed jump height, no tap-to-jump, no tap assist.**
Altitude is controlled purely by how long you hold. `thrustOn()` / `thrustOff()`
only set `player.thrusting`; all motion happens in one place in `updatePlay`:

```js
p.vy += GRAV*dt;
if(p.thrusting) p.vy -= THRUST*dt;
p.vy -= p.vy * DRAG * dt;
```

`DRAG 2.6` is what makes it feel smooth - velocity eases toward a terminal speed
(about +/-1000 over ~0.4s) instead of ramping linearly into a clamp. `VY_UP` and
`VY_DOWN` are safety rails only. Impulses, latches and lift ramps were all tried
and all removed: each one is a second movement system competing with this one.

Measured hold-length to altitude: 0.2s -> 71, 0.5s -> 295, 1.1s -> ceiling,
rapid tapping -> 22 (tapping must not be a strategy).

## Feel numbers that matter

- `DRAG 2.6` is what makes flight feel smooth: velocity eases toward a terminal
  speed (about +/-1000 over ~0.4s) instead of ramping linearly into a hard clamp.
  `VY_UP/VY_DOWN` are now safety rails only.
- `FLAP_KICK` fires **only off the ground**, as a jump. Applying an impulse in
  mid-air is a jolt, and jolts are what stopped the flying feeling smooth.
- `GRAV 2500`, `LIFT 5200` — holding applies **constant** upward acceleration,
  Jetpack Joyride style, and the wingbeat is purely visual. Lift used to arrive in
  pulses on each downstroke, which read on a phone as the hold not registering, so
  players tapped instead of held. Do not reintroduce pulsed lift.
- `FLAP_KICK 340` — every press lands an instant upward impulse, and
  `flapLatch` keeps the downstroke running for 0.16s even if the finger lifts
  first. Without those, a quick tap could end before the stroke produced lift and
  the control felt dead in mid-air.
- **`touchstart` and `touchmove` MUST be non-passive and call `preventDefault()`.**
  Registered passive, they cannot preventDefault, so the browser's long-press
  handling ends the touch and fires `touchend` on its own - a hold then arrives as
  a tap and holding is impossible. This cost seven attempts to find, because the
  symptom looks like a physics or event-family problem. `input-test.html` proves
  it in one screenshot: a hold showed `touchstart=3 touchend=3`. Buttons are
  exempted from preventDefault so their clicks still work.
- **Touch devices use touch events ONLY** (`TOUCH` branch). Pointer events are a
  trap here: a phone fires `pointercancel` mid-hold from a micro finger movement,
  and *any* handler that releases on it silently ends the hold with no further
  event until the next tap. That is what forced multi-tapping instead of holding,
  and it survived one "fix" because the release was hidden inside a pointer-set
  handler. Do not add a `pointercancel` listener that releases.
- `CK.ANKLE` is **computed from the shoe art** on load: the IK aims the ankle
  ANKLE units above the ground and the shoe hangs `(1-ay)*height` below it, so
  those must be the same number or the sneakers float or sink.
- `CATCH 0.45` — re-pressing while diving kills 45% of downward speed and fires a
  wider power stroke. Without it, recovering from a full-speed fall cost 250
  units of sink over 0.95s and the bird read as heavy. With it: 0.07s, no sink.
  If you change `VY_DOWN` or `FLAP_ACC`, re-check that recovery.
- Speed ramps `430 → 730` over 85s. Much slower than the old jump version: you
  are steering continuously, not reacting once.
- Framing: `SCALE = min(CH/980, CW/1450)`, landscape, and only that. See
  **Landscape only** below.
- `CEIL` is the altitude cap; air hazards spawn at random heights inside it.

## Debug flags

`?auto=1` start a run · `?demo=1` auto-flap · `?flap=0.5` freeze the wings at one
point in the cycle · `?hold=0` glide · `?zoom=1.7` zoom on the bird ·
`?dbg=1` altitude readout · `?slow=6` run the escape in slow motion ·
`?stage=1` drop three gates in front · `?solo=1` character only,
no world or HUD · `?run=0.3` freeze a stride frame · `?pose=land:1` freeze any state ·
`?sz=2` zoom the solo view · `?rig=1` draw the pivot crosshairs (use this before tuning parts) ·
`?wear=head:hat_bucket,face:shades_art,neck:scarf_art` set a loadout ·
`?crow=1` crows from the third second instead of the twenty-fourth, back to back ·
`?crowshot=1` park one moment of the attack (`window.__crow('track'|'lock'|'fly'|'close'|'live')`) ·
`?crowtest=1` measure how often a volley actually gets to fly.

## Animation

The flap is **8 hand-placed keys** through a periodic Catmull-Rom (`FLAP_TRACK`),
not a sine. The uneven timing is the point: the power stroke fires in ~0.10 of
the cycle and the recovery takes ~0.38, which is what makes a wingbeat read as
effort. Body pump, head lag and tail all come off the same track.

`?flap=0.375` snaps the pose to that exact key (no blending) so you can inspect
a single frame — blending made earlier screenshots lie about what the keys were.

## Frame animation

`anim/*.webp` are **hand-drawn frames**, generated through Gemini Studio from the
reference and sliced out of four sheets (run 6, fly 6, jump 4, land 4). Total
**198 KB for 20 frames** - WebP q88.

How they were made, because it is repeatable:
- One prompt per *sheet*, not per frame - 4 browser sessions instead of 20.
- Each prompt attaches the reference and **names the outfit explicitly** (teal cap
  worn backwards, black shades, gold chain, white sneakers). Naming the clothes is
  what stops the character drifting between generations.
- Slice by **column projection**, not connected components: the figures touch, so
  flood fill merges them. Cells much wider than the median are sub-split at their
  emptiest interior columns.
- Each sheet comes back at its own scale. Frames are sized by **how many times
  the silhouette can be shrunk before it vanishes** - the radius of his fattest
  part - which ignores wing spread, leg position and which way up he is. One
  scale per sheet from its median, plus a per-frame trim clamped to 15%, so real
  squash survives but figures drawn too big get reined in. Do NOT size by the
  teal cap: Gemini draws it at different proportions on different sheets, so
  matching cap area actively makes the bodies disagree.
- Frames are sized by **fat radius** — how many times the silhouette can be
  shrunk before it vanishes — which ignores wing spread, leg position and which
  way up he is. One scale per sheet from its median, plus a per-frame trim
  clamped to 15%. The run cycle measures 30; match a new sheet to that. Do NOT
  size by the teal cap: Gemini draws it at different proportions on different
  sheets, so matching cap area actively makes the bodies disagree.
- Every frame stores `ay`, the point inside the frame the drawing origin sits
  on: the feet for poses on the ground, the centre of mass for poses in the air,
  so his body holds still while his legs dangle differently. This replaced
  `lift`, which recorded how high above a sheet's ground line Gemini happened to
  draw a figure - meaningless for a character positioned by physics, and it made
  him jump 23px between falling and landing.
- A lanky character (the crickets) must be sized by **height**, not thickness -
  thickness sized them taller than the hero.

`SPR` converts frame pixels to world units. `pickFrame` maps state to frame.
**Every frame is optional**: if an image fails to load, `FR.ready` stays false and
the procedural puppet draws instead.

**Cosmetics do not apply while frames are in use** - the cap, shades and chain are
drawn into the frames. That is the trade for hand-drawn art, and it is why the
puppet path is still worth keeping.

## Environments

**One map, and it does not change.** Cluck County: he is kicked out of the barn
onto the farm road and stays on it. The run used to travel -- a leg every 26s,
farm -> city -> block, crossfaded rather than cut -- and the two other palettes,
their layer builders, their props, the painted prison wall and the whole
crossfade machinery are gone with it. `THEME` is a plain object now, not an
entry in a `THEMES` array, and `applyTheme()` takes no argument.

If a second map ever comes back it comes back as its own `THEME` plus a builder
and a deliberate way in -- **not** as a timer that swaps the world out from
under the player mid-run.

The farm is **painted panels**, not coloured rectangles. See **The painted
farm** under **Themes**.

## The sound of flying

**The wingbeat is SILENT, and that is the current state.** Cut on 2026-09-05 on
request. At eight and a half beats a second, anything there at all becomes a
texture you cannot stop hearing -- which is the same wall the two retunes below
kept running into -- and the wind bed already carries the flight. `S.flap()` is
a documented no-op, `flapSide` is gone, and the two flight call sites are gone
with it. The stub stays because two sessions write this file and a call added
later should be silent, not a crash.

**The truck's double jump was the third caller** and would have gone quiet along
with it, which nobody asked for. Its first jump already used `takeoff()`, so the
second one does now too.

**Open: the air bed still ducks to 22% while he is holding** (`const duck` in
`updatePlay`), and it does that solely to make room for a wingbeat that is no
longer there. As it stands, holding -- the game's whole control -- makes the
mix quieter. Either drop the duck or keep it deliberately as "flight is calm";
it should not stay by accident.

Everything below is the history of how the beat got short and thin before it was
cut. It is kept because the measurements still govern anything short and
percussive added here later, not because the flap still makes a sound.

**A wing beat must not contain a sub.** The flap used to lead with a 74Hz sine
under 180ms of broadband noise, and that sine carried more gain than anything
else in it -- measured, **85% of the sound's energy sat below 300Hz, with a
spectral centroid of 288Hz**. That is a bellows, and no amount of hiss on top
disguises it. There is nothing below about 300Hz in it now and the whole beat is
over in a tenth of a second: centroid 3982Hz, 0.2% below 300. A flick, not a
gust. The weight of a flap is the physics' job -- `FLAP_KICK` and `LIFT` -- and
the sound only has to say "feathers".

**The air bed sat too low as well.** `WIND` is a looping bandpass whose level and
cutoff are pushed every frame, and it ran 260-1760Hz at Q 0.55. A band that broad
that low has skirts down in the rumble, so the constant layer under everything
was a fan rather than speed. It runs 640-3140Hz at Q 0.85 now, and quieter.

**And it must not be LONG either.** `FLAP_HZ` is about eight and a half beats a
second, so they land 118ms apart: anything over about 70ms overlaps its own next
beat, overlapping beats of filtered noise are a texture, and a texture is
indistinguishable from wind however feathery its spectrum. Length was as much of
the problem as pitch.

The last version before the cut had short alternating strokes -- a fuller
down-stroke, a thinner recovery -- plus a rubbery squeak one beat in six and a
strangled cluck one in thirty. It was the best the beat ever sounded and it was
still a texture at eight a second, which is what settled the argument.

**The air bed DUCKS to 22% while he is holding** (`windSet` smooths over 0.10s,
so it is a swell rather than a switch). It was put there to stop the bed
competing with the wing beats. There are no wing beats now -- see the open
question at the top of this section.

**Nothing but functions may live on `S`.** `stepFoot` sits beside it at module
level rather than on it, because `?audiotest=1` walks every key of `S` and calls
it, so a number parked in there is a crash. The test caught exactly that when
`flapSide` was added.

When retuning any of this, measuring beats guessing: sum the parts offline and
look at the spectral centroid and the fraction of energy below 300Hz. Filtered
noise is hard to model faithfully at low Q, but pure tones are exact -- and a
tone is usually what is making a sound heavy.

## Music

**The scene follows game.mode, and `musicScene` is still the only thing that
sets volume.** `trackTick` compares `musicFor()` against the current scene and
asks for the right one when they drift apart. It sets no volumes itself.

That guard exists because hanging music off TRANSITIONS means every new
transition is a chance to forget one, and this has now been forgotten twice.
`musicScene('play')` lived at the end of the cage intro, so the retry beat --
which deliberately skips the cage -- never reached it: a retry played the menu
theme straight through the run and the chase never started. `toMenu` had the
mirror of it before that, carrying the chase theme on into the score card.
`startRun` no longer sets a scene at all, because it is shared by the escape
(which wants the menu theme over it) and by a retry (which does not).

**`?musictest=1` now drives the real entry points**, not just the scenes.
The scenes were always right in isolation -- `musicScene('play')` set the right
volumes every time -- and testing only those is why this shipped. It calls
`toMenu`, `startIntro`, `startQuick` and back, ticks a frame, and checks what is
actually playing. On the broken build it reports `FAIL RETRY -> menu (wanted
play)`.

**`musicScene('menu'|'play'|'duck')` is the only thing that sets music volume.**
The menu theme (`audio/music_menu.mp3`) covers the title screen, the escape and
the score card; the chase playlist belongs to the run and starts on the kick.
Before this, `toMenu` never touched the track, so dying and retrying carried the
chase theme straight on from wherever it was, and `startRun` began it during the
intro. `?musictest=1` checks each scene and that the two never play at once.

`MOVEMENTS` in `initTrack` is the playlist: two long-form tracks played back to
back, about 5 minutes 25 before anything repeats. Any entry that fails to load is
skipped, and the old synthesised groove is still the fallback if none load
(`musicTick` returns early when a track exists). The mute button controls both.
`?track=NAME` plays one `audio/music_NAME.mp3` on loop instead of the chase playlist.

**Music length is set by the MODEL, not the prompt.** Everything generated on
Flash comes back at 30.8s however long a piece is asked for - three minutes, a
piano solo, Lyria 3 Pro named outright, all 30.8s. Gemini Studio now selects Pro
for music (`config.json` -> `musicModel`), which gives 2-3 minutes. Measured,
same prompt: Flash 30.8s, Pro 147.3s. Do not spend another round on prompt
wording. Details in the studio's own `_CONTINUE-HERE.md`.

Asking Pro for "a THREE MINUTE piece" returns *no audio at all* and burns the
full 10 minute timeout. Describe the music and add "as long as you can".

`tracks.html` is the comparison page: waveforms, loop toggle, and an A/B that
keeps position when switching so the same bar can be compared.

## Known rough edges

- Expression is one eye plus a brow, driven by `p.shockT`. It reads at phone
  size but there is room for more.
- Wearing every slot at once gets visually busy. Tuning, not architecture.
- At the bottom of the flap (`?flap=0.375`) the near leg draws over the wing tip.
  One line of draw order in `drawChicken` if it starts to matter.
- **No jetpack cosmetics.** The bird flies with his own wings; a jetpack would
  undercut the one idea that keeps this from being a Jetpack Joyride clone.
- Difficulty is speed, spacing and hazard mix - see **Obstacles**. There are no
  gates any more.
- `chickens.html` keys green in-browser, so it only works over http(s), never
  `file://` (tainted canvas).

## Deliberately not built yet

Shops, missions, customisation UI, multiplayer, ads, IAP, login.

Golden eggs ARE in (see below) and the bank persists, but nothing spends them
yet - that is the obvious next thing.

## The bug that broke hold-to-fly for days (fixed, build b2305)

`bp.Q = 1.1` on a BiquadFilterNode. `Q` is an **AudioParam**, so it is
read-only and the assignment throws in strict mode. Chrome on the desktop
never showed it because audio only starts after a real user gesture, which
headless runs never make. On the phone it threw inside `S.flap()`, which
`thrustOn()` called *before* setting `player.thrusting` -- so every press
counted a tap and then aborted. That is the whole `taps=14 held=0` report.

Three defences now:
- `bp.Q.value = ...`
- `tone()` and `noise()` swallow their own errors; sound can never abort a caller
- `thrustOn()` sets `player.thrusting` FIRST, before any effect or sound

**`?audiotest=1` plays all 20 sounds and prints failures on screen.** Run it
headless with `--autoplay-policy=no-user-gesture-required`, or the audio
context never starts and the test passes vacuously.

## Slicing generated sprite sheets

`sheets/v2/*.png` are the source sheets; `anim/*.webp` + `anim/frames.json`
are the output. The build script pattern is in the session, and the two
things that actually matter:

- **Splitting.** Prefer empty-column gaps -- they are exact. Only when a sheet
  has fewer gaps than figures, flood out from each teal cap through the
  silhouette (multi-source BFS). A straight vertical cut through overlapping
  chickens always clips a wing or a shoe; flooding follows the leg instead.
  Keep the N biggest pieces, or a knocked-off pair of sunglasses becomes a frame.
- **Scale.** The teal cap is the only thing the same size in every pose, so
  match cap *area* per frame to kill Gemini's per-figure drift. Then apply one
  extra factor across all sets so the run cycle keeps the height it already
  had on screen. Do not use body area -- spread wings inflate it.

### What the generator gets wrong
- Asking for the comb "in front of the cap" makes it drop the comb on some
  figures and keep it on others. Inconsistency between frames is worse than
  the original problem. The `run_fists` prompt (fists + comb described
  together) is the one that came back consistent -- reuse that wording.
- "In-between poses" are not grounded: it invents a second independent cycle
  rather than interpolating the first. Order merged frames by a *measured*
  phase, never by assuming frame i sits between i and i+1.
- Sheets drift in proportion between each other. `sheets/v2/fly.png` drew a
  chunkier chicken with a smaller cap and had to be dropped; `fly_mid.png`
  matches the run cycle. Always compare a new sheet against the run cycle
  before merging.
- Ask for one row, small figures, and "a vertical line between any two
  neighbours must cross nothing but flat green" -- that phrasing works.

## Animation states

`FRAME_DATA` holds run 6, fly 6, fall 4, jump 5, land 4, hit 6, kick 5, boom 5. `pickFrame()` is the
single place that chooses; `cyc()` wraps a 0..1 phase onto whatever length a
set happens to be, so adding frames needs no other change.

`hit` is driven by `game.dyingT` over the ragdoll tumble, and its last frame
is held for `game.mode === 'dead'` behind the score card. The ragdoll's own
rotation is damped to 25% while frames are ready, because the art already
tumbles and the two rotations fight each other.

## Landscape only

There is **one framing**. `PORTRAIT` survives as a single question — *should we
ask for a turn?* — and nothing else: `resize()` computes the landscape scale
unconditionally and toggles `body.portrait`, which shows the `#rotate` gate.
The run is **frozen** behind that gate (`frame()` renders but does not update),
so turning the phone mid-run never costs a life.

### Fullscreen on the turn

Turning the phone sideways is the whole gesture: `onOrient()` calls
`goImmersive()`, which asks for fullscreen on `<html>` and chains
`screen.orientation.lock('landscape')` onto it. **The request is made
synchronously inside the orientation handler.** The Fullscreen spec allows a
request triggered by *a user generated orientation change* as well as one
triggered by a user gesture, and that permission is spent the moment you defer
it — putting the call behind the `setTimeout(resize, 120)` that handler already
had would throw it away. The resizes stay deferred (twice: 120ms for the
viewport, 450ms for the fullscreen transition landing); only the request is
immediate.

`isLandscape()` reads `screen.orientation.type` **before** falling back to
`innerWidth > innerHeight`. This is not defensive padding: measured over CDP, at
the instant the orientation handler runs the viewport is still the old portrait
one (`innerWidth 412 > innerHeight 915` is false) while `screen.orientation.type`
already says `landscape-primary`. Comparing the viewport there simply never
fires.

Both `orientationchange` and `screen.orientation`'s `change` fire for one
physical turn, so `onOrient` ignores a second call within 500ms — otherwise
every turn asks twice.

`goImmersive()` also runs on the first gesture, from `audioInit` (via the
`lockLandscape` alias), for a player who arrives already sideways. `audioInit`
runs on *every* touch, so the already-immersive case early-returns on
`inFullscreen() && lockDone`. Leaving fullscreen sets `fsOptOut`, and a player
who deliberately swipes out is **not** dragged back in by their next flap —
only by turning the phone again, which re-arms it.

All of it is best-effort and every failure is swallowed. iPhone Safari has no
element fullscreen at all (the `apple-mobile-web-app-capable` meta only helps a
home-screen install), and desktop is left alone entirely (`TOUCH` guard). The
`#rotate` gate is still what actually guarantees landscape; fullscreen is the
convenience.

The menu is laid out **on the right half** (`padding-left:46vw`,
`align-items:flex-end`) so the left stays clear — that is where he is waiting in
the cage, and seeing him there is the whole hook. Type sizes are `vmin`, not
`vw`: on a 844x390 phone `vw` sizing put the logo through the right edge.

**Clear the canvas to `C.skyA`, not `C.ink2`, outdoors.** The camera rises with
the bird and a zoom punch shrinks the world a fraction, and both expose canvas
outside the drawn band. Against the ink that reads as a black letterbox around a
bright farm.

## The intro (the cage)

Cluck County Farm Correctional Facility. The menu IS the cage: he is standing in
it, behind the bars, from the moment the title appears. `toMenu()` parks him
there, `startIntro()` runs two seconds, and the kick hands over to a normal run.

    T_WIND  0.42  coils, rocking back — the frame and the title start to rattle
    T_KICK  1.15  THE KICK. Door, lock, splinters, blast, all on this frame.
    T_BURST 1.52  through the doorway, still airborne
    T_OUT   2.00  control returns mid-stride

**The scene is painted, not drawn.** `sheets/v2/cage_scene.webp` is the barn
with an empty doorway; `art/cage_door.webp` is the barred door on its own, so it
can buckle (`doorBow`) and then leave (`game.door` + `updateDoor`). Every
position in `CAGE` is a fraction **measured off the art** — the doorway rect, the
straw floor, the roof apex — which is what puts his feet on the straw rather
than near it. The painted dirt below the ground line is cropped off so
`drawGround` carries on underneath and the two can never disagree about where
the floor is.

**`cageGeom` is anchored on the DOORWAY, not on GROUND** (`CAGE.doorH`, in world
units). Nugget stands in the doorway, so the doorway is the one measurement that
must hold still; anchoring on the canvas means every change to the art's framing
silently resizes him.

### The barn's roof is reconstructed, not generated

Three rounds of asking for the whole barn came back with the same crop, every
one of them slicing the gable off — which is what "the top of the building is
faded" was. `tools/build_apex.py` builds it instead, and it is geometry rather
than guesswork: a gable is two straight lines, both edges are visible in the
art, and their slopes are measured off the trim colour and extended until they
meet. The wedge between them is filled by smearing the wall's top row upward,
which is exactly right because the planks are vertical.

The one liberty: the true apex measures **412px above a 572px image**, and
building that is useless — the doorway has to stay a fixed size so Nugget does,
and a barn that much taller than its doorway will not fit a phone in landscape
with him still readable. So `RIDGE` brings the peak down to a plausible gambrel
pitch. Nobody measures a cartoon barn; everybody notices a building with its top
sliced off.

**`drawCageBack` also extends the barn to the left screen edge** by stretching
the art's leftmost two columns — a vertical run of plank colour — out to it. The
scene used to be alpha-ramped on both sides, and ramping the left turned the
planks half transparent with a field showing through them: a ghost, not a blend.
Only the right edge is ramped, where the farm behind the barn hands over to the
map's own panels.

### The neighbours

Three hens in a crate on the barn roof (`drawRoofHens`, `art/roof_crate.webp`,
`FRAME_DATA.hensad` / `.henjoy`). They are desperate the whole time Nugget is
caged and lose their minds from the frame the kick lands — the only reaction in
the game to the thing the player just did. Two details carry it: they are drawn
**before** the crate, so its keyed-transparent wire mesh reads as being in front
of them, and the crate's y is **clamped** so it can never climb off the top of
the frame — on a short landscape phone there is only about 70px of sky above the
apex.

`cagePose()` is the single place that decides where he is and which frame he is
on; `pickFrame` defers to it for both 'menu' and 'intro'. The blast is
`FRAME_DATA.boom`, five painted frames over the doorway, drawn after everything
else in the scene including the door that is already leaving.

### Two numbers that stop it teleporting

- **`CAGE_RUNOUT` (300)** is how far he travels between the kick and control,
  and the cage is parked exactly that far *behind* the play position
  (`game.cageX = -CAGE_RUNOUT`, camera at `-PX`). The escape's last frame and
  the run's first frame then land on the same pixel. Park the cage anywhere else
  — it used to sit at `2*PX` — and he jumps half a screen in one frame.
- **`CAGE_CAM` (430)** pulls the camera back while he is still inside, and
  `updateIntro` eases it onto the play mark over the kick. Without it the cage
  has to sit `CAGE_RUNOUT` behind `PX`, and `PX` is only 27% of the width, which
  shoves the barn half off the left edge and hides the one thing the menu is for.

`?introt=N` freezes the intro at a moment. It now takes **one step of the whole
remaining time** so the one-shots fire on the way; assigning `introT` directly
made `was` and `t` equal and the flag could show the poses and nothing that
actually happens. `?slow=6` runs the whole thing in slow motion instead, which
is the better way to look at the hand-over.

Two traps this hit before, both still worth remembering:

- **`if` in the middle of an `else if` chain.** `if(game.door) updateDoor(dt)`
  went between `else if(intro)` and `else if(play)`, so `updatePlay` bound to
  the door check and the game stopped dead for the third of a second the door
  was airborne. Anything added to that dispatch goes after the whole chain.
- **Dead references after replacing a block.** `drawTitle` still called a
  function from the sequence it replaced and threw every frame. Grep for callers
  before deleting a block, and check the on-screen error panel.

## Screenshots

**Do not use `chrome --headless --screenshot` for layout.** It lays the page
out at 500px wide regardless of `--window-size` and then crops the image to the
window, which chops the right-hand side off and looks exactly like a layout
bug. It cost a round of chasing a bug that did not exist in tracks.html.

Use `shot.py` (in the job tmp dir, kept with the session): it drives Chrome over
CDP, sets `Emulation.setDeviceMetricsOverride`, and prints the real viewport and
scrollWidth alongside the file so overflow is measured rather than eyeballed.
Needs `--remote-allow-origins=*` or the websocket handshake is refused.

## Obstacles

`poolFor(tier)` filters by tier and nothing else -- there is one map, so there
is one cast, and it is all farm. Everything that read as a city street is gone:
the sofa, the shop sign, the coffee machine, the vacuum, the pizza, the cake, the
chair, the cart, the duck, the beach ball, the traffic cone, the banana skin, the
cardboard box, the beach ball, the blowing newspaper, and the code-drawn barrel
the painted `woodkeg` replaces. **The zapper went too** -- it is a laser, and it
belongs to a different game.

What is left of the old set is `tower`, `hanger` and the bird flock, which is now
`crows` in farm colours rather than city pigeons.

**Removing the zapper cost real difficulty and the spawn table had to absorb it.**
It was 22-26% of every tier above 0 and the only hazard that could sit anywhere
in the column; without it every tier collapses into "fly over the ground props"
and the ceiling stops mattering. Its share went to the standalone columns and the
air, which are the only other things that make you choose a height. The measured
corridor at tiers 1-4 went from 258-320 to about 485, so the game IS easier than
it was -- if that needs winding back, move the spawn gaps and the column share,
not the tier thresholds.

**Dropping the city took both falling hazards with it** -- the sofa and the sign
were the only `kind:'fall'` entries, so tiers 2 and 3 quietly lost a whole
category. `fallbale` and `fallcrate` replace them, reusing the hay bale and
crate sprites.

**`?obtest=1` was testing the wrong tiers.** Its `game.runT` values were
`[0,30,55,80,120]`, which map through `tierNow()` to tiers 0,2,3,4,4 -- so tier 1
was never exercised at all and tier 4 was tested twice. They are `[0,15,30,50,80]`
now. Any change to `tierNow`'s thresholds has to be mirrored there.

The farm's sixteen hazards are **painted props** cut off a Gemini Studio sheet
and keyed off flat green (`art/farm/*.webp`), built by `farmProp(name, w, h)`.
The sprite fills its hitbox exactly — `w` and `h` are what `spawnOne` collides
with, so anything drawn outside them is a hit you cannot see coming — and every
one falls back to a flat block if its image is missing, the same bargain the
character frames make. Art can never make a hazard invisible.

**Electrified corn is live STALKS and nothing else.** There used to be a
horizontal wire strung across the top of every corn hazard as well, which gave
it the one silhouette it must not have: a fence with corn planted behind it.
The fence pieces are a different hazard with a different rule, and two hazards
that look alike teach the player nothing. The crop is the hazard here.

`spawnPattern` places ONE hazard at a time anywhere in the column. There are no
gates any more -- a floor piece and a ceiling piece at the same x is Flappy
Bird, and it is what made everything look stacked. `tower` and `hanger` are
placed only by `spawnStandalone`, and are filtered out of the generic ground
pool, or a hanger spawns sitting on the floor drawn upside down.

Zappers (`kind:'beam'`) are the Jetpack Joyride hazard: a bar at any angle,
collided with `segRect` so the hitbox is the bar you can see. Every candidate
is rejected unless it leaves a 210px corridor.

`?obtest=1` spawns 240 patterns at each tier and checks for stacking, corridor
width and exceptions. `?runt=N` starts a run at a difficulty.

## Themes -- there is one

`buildLayers` builds the farm and nothing else. `buildFarmLayers` is only the
**fallback**: it returns early the moment `FARM.ready`, because the painted
panels are the middle distance and drawing the coloured layers as well stacks a
second farm behind the first, with its hills showing through the fade.

### The painted farm

`sheets/v2/farm_a|b|c.webp` are generated panels, laid overlapping and
dissolving into each other by `loadPanels` -- a left-edge alpha ramp, so a hard
seam through a fence line never shows.

**`marks` is TWO landmarks per panel**, measured off each image: the painted
ground line, and the top of the fence's top rail. Two landmarks give two
equations and a panel has two unknowns -- its scale and where its top sits -- so
`farmGeom` solves both instead of guessing. That is what makes the grass line
AND the fence line run continuously across a seam, and the panels end up at
slightly different scales (the widest is ~17% bigger than the narrowest), which
is a price worth paying.

One shared `floorFrac` was the bug behind "the fences do not attach": the three
panels were painted with ground lines at 0.785, 0.802 and 0.820, so anchoring
all of them on 0.806 stepped the grass by up to 13px at every join and left the
rails meeting at different heights.

**Draw the panels BEFORE the spectators.** They paint the whole middle distance,
so anyone standing in the field drawn before them is simply covered -- which is
what happened to the crickets the moment the art landed.

Three things that cost a round each and are the reason it reads:

- **The sky is keyed OUT of the panels** (a flood from the top row over
  sky-blue, which stops dead at the black ink outlines). Drawn as opaque
  rectangles they show their own, lighter blue as a hard band across the whole
  screen, and fading the top instead eats the silo and the barn roof -- the only
  content up there worth keeping. The painted clouds are white, fail the blue
  test, and survive as cutouts.
- **The sky's clouds are cut out of the panel art too** (`SKY_CLOUDS`,
  `art/cloud*.webp`): white islands enclosed by the keyed-out sky. The soft
  translucent blobs the code used to draw sat next to cel-shaded painted clouds
  looking like smudges on the lens. Every one is optional and falls back to the
  old blob.
- **The three panels are TONE-MATCHED to each other** (`cut_panels`). They came
  back from three separate generations at three different exposures -- panel C's
  grass was 21% brighter in green than panel A's -- so wherever one ended and the
  next began there was a tonal step running the full height of the screen, which
  is what "the fences look faded" actually was. A 46px crossfade cannot hide a
  whole-panel tone difference; it only smears the step. The match is made on the
  GRASS BAND, because the grass is what meets at a seam and runs the full width
  of every panel, and applied to the whole panel as a clamped per-channel gain.
  **The cage scene is deliberately NOT matched this way**: its right third is
  open farm, but the rest is a big red barn, and the gain that fixes the grass
  turns the barn olive. A foreground building is allowed its own tone.
- **`haze` washes the distance out** (`source-atop`, so it tints the art and
  never the keyed-out sky). The hazards are painted in the same style at the
  same saturation as the map, so without it a hay bale in front of a hay field
  is camouflage. This is aerial perspective doing a gameplay job.
- **Size against `GROUND`, not the play band.** The play band magnifies a 572px
  source about fourfold and puts the silo tops off the frame.

`drawGround` is a dirt track with a grass fringe and wheel ruts, coloured off
the panels. A curb and a hazard stripe are a street; this is a farm road.

**`drawCageBack` extends the barn to the left screen edge** by stretching the
art's leftmost two columns -- a vertical run of plank colour -- out to it. The
cage scene used to be alpha-ramped on both sides, and ramping the left turned
the planks half transparent with a field showing through them: a ghost, not a
blend. Only the right edge is ramped now, where the painted farm behind the barn
has to hand over to the map's own panels.

## Golden eggs

`game.eggs`, `spawnEggs`, `updateEggs`, `drawEggs`. Laid out the way Jetpack
Joyride lays out coins - a flat line, an arc, or a climb - so a run of them can
be followed with one held press. **`eggFree` rejects any egg that lands inside a
hazard**, including zapper beams, so chasing them is a real choice and never
bait. **The SHADING is painted per angle; only the WIDTH is set in code**
(`sheets/v2/egg_spin.png`, `tools/cut_eggs.py`). That split is the whole design:
the part that has to be hand-drawn is the part a program cannot fake, and the
part a program should own is the one number an artist cannot hold steady across
ten drawings.

What has to be drawn, and what the prompt asks for in these words, is what gives
it a third dimension:

- **shading bands that CURVE round the form** like lines of longitude -- bowed
  ellipses, tight near the silhouette and spread in the middle, never straight
  vertical stripes. Flat stripes are what made the first sheet read as a decal;
- **a warm bounce light hugging the dark limb**, a thin band of lit bronze
  between the outline and the core shadow, so the form turns away instead of
  just going dark;
- **a bright polished RIM** on the edge-on frame, and a reverse face that comes
  round **darker because it faces away from the light**. Those two are the
  entire difference between a spin and a squash.

The sheet comes back in whatever order the model felt like, so frames are chosen
by MEASUREMENT: width says how far round it is, mean brightness says whether it
is the lit face or the reverse. They are then laid on a cosine, and the second
half of the turn reuses the first half's art MIRRORED -- what a symmetric object
actually does, and it stops the loop reading as a repeat.

**`EGG_SPIN` is turns a second, and it is 1.15.** It was 0.30 -- one turn every
three and a half seconds -- which meant an egg crossed the whole screen having
barely left the frame it entered on, and none of the painted rotation was ever
seen. The procedural fallback is tied to the same constant so the two cannot
drift apart.

**Twelve frames, and the width is eased.** At ten frames the step is 36
degrees, so nothing lands on 90: there is no true edge-on view, and the two
nearest it are a third of full width -- which put FOUR of ten frames into a
sliver and turned a run of eggs into a row of splinters. Twelve hits the edge
exactly, twice and only twice, and `EASE` fattens the rest so the egg reads as a
solid object turning with one quick flick through the edge.

**Classify the EDGES before splitting lit from reverse.** Sorting the whole
sheet on median brightness put the edge-on views -- mid-toned by nature, being
mostly rim -- into the reverse pool, where `LIFT` then brightened them into pale
slivers. Width says which frames are edges; only the wide ones are sorted by
brightness, and at their biggest GAP rather than at a median, because a median
splits a group in half whether or not there are two groups to split.

**`LIFT` brightens the reverse frames by a third.** The painted reverse is
genuinely dark, which is right for a lit object and wrong for a pickup: half a
cycle of dark brown reads as the egg flickering out of existence rather than
turning.

Two dead ends are written up at the top of the tool because both are tempting.
Squashing one hero per frame leaves the highlight welded to the surface, so the
eye reads a picture being scaled. Re-projecting the painting as a texture around
a solid of revolution is the *correct* model and comes out striped, because the
mapping crushes the texture into a few columns at the silhouette.

The egg carries no marking -- a stamped one reads as a token rather than
treasure. `art/egg_icon.webp` is the widest frame off the same sheet, so the HUD
counter and the pickup are one object. Alternates: `egg_alt_soft.png`,
`egg_alt_cool.png`, `egg_alt_band.png`, `egg_alt_plain.png`. Taken eggs fly to the counter; the pickup pings up a
semitone per egg in a streak. `game.eggBank` persists in `localStorage` under
`dgh_eggs`.

## The hay bales (`tools/thin_bales.py`)

`art/bg/near.webp` is one tile that loops, so however many stacks are painted on
it is how many the player sees for the whole run. Two per 923px was a stack
every half screen, forever, and the field read as a hay depot.

**Nothing is deleted.** Bale-free stretches are spliced in, which makes the tile
longer and the bales rarer and needs no inpainting at all, because every pixel
is already the right pixel. The splice is invisible because everything crossing
it -- the grass line, the fence rails -- is horizontal, so any x works provided
the cut misses the posts and the bales.

Deleting a stack is the first instinct and it is a trap: a fence post stands
behind it, so the hole needs a donor slab carrying its own post at exactly the
right offset, and on a tile this short no such donor exists. Every attempt left
either a sliver of hay or a hole in the fence.

Finding the bales is the other half, and colour alone will not do it:

- Blobs are filtered **by height**. The grass is full of buttercups that pass
  any straw colour test, and the fence rail has a straw-coloured highlight
  running its whole length. A stack is a hundred pixels tall; a buttercup is
  twenty. Filtering by area instead merges every stack into one run covering
  most of the tile.
- The blobs are **dilated** before their extent is taken. The colour test finds
  the lit face of a bale and misses its ink outline and the loose straw round
  its foot, so the raw extent is about 40px too narrow at each end -- and a
  chunk cut against it contains a sliver of the very thing it is avoiding.
- Posts are found by **opacity**, not colour: the sky is keyed out of this
  layer, so a post is a column that is opaque all the way up.

The copies are taken at different offsets inside the clean stretch rather than
being the same slab N times, because three identical slabs of grass in a row
read as a repeat.

## NPCs

**`NPC_REACT` is FALSE: they walk and do nothing else.** Reactions made every
one of them an encounter -- a gap, a thing happening, another gap -- when what a
background wants is for someone to be passing by. Setting the flag to `true`
restores every reaction at once: the livestock panic run, the farmer's rage, the
pigeons' alert. All the frame sets are still loaded and still sliced; only the
switch is off.

**One at a time, not a crowd.** Animals every **1750** units with 58% of stops
populated and exactly one animal per stop; the farmer every **3200** at 55%.
That works out at about one figure on screen, sometimes two, often none -- which
is what "someone happens to be walking past" looks like. A dense band of them
reads as a parade, and the eye starts watching the crowd instead of the bird.
`NPC_WALK` is 78 units a second, an amble.

### They TRAVEL, and the phase comes from distance

They used to sit at fixed world positions playing a walk cycle on the spot,
which is a moonwalk: the legs say one speed and the body says nothing, and the
eye reads it as the animation being broken rather than the position. `npcWalk()`
is how far they have actually gone in world units, subtracted from their
position so they head back down the road the way they already face.

**The animation phase comes from that DISTANCE, never from the clock**:
frame = `(distance / stride) * frames`. Drive it from time and the feet skate
the moment either number is retuned; drive it from distance and the stride
length is the only thing that can be wrong -- and a stride is measurable.
`NPC_STRIDE` is world units per full six-frame cycle as a fraction of the
figure's drawn height, because a farmer's pace is not a goat's.

**Every background NPC has TWO six-frame loops**, a walk and a reaction, the
way the livestock do -- a background character that holds one pose reads as a
sticker, not a character.

**The farmer** (`drawFarmer`) owns the place and Nugget has just left it.
`farmerwalk` is his stroll and is what he does with `NPC_REACT` off;
`farmeridle` is him wiping his brow and settling; `farmer` is six frames of
escalating rage -- noticing, fists up, pointing, hat off, doubled over -- run
only while a chicken is going past. The rage loop starts at frame **2**, because
frames 0 and 1 are the calm and the double-take and looping through them resets
him to placid mid-tantrum. He gets his OWN pass at his own spacing rather than
joining the livestock: one farmer reads as a man, three in a row reads as a bug,
and the animals want to come in groups.

**The lookouts** (`drawSpyPigeons`, `SPY`) are three pigeons in sunglasses on the
watchtower's balcony rail. `spy` is a slow shuffle; `spyalert` is head up, wing
to the earpiece, talking into it. The near test is **screen** distance, not world
distance, because the tower rides the parallax and its world x is not where it
looks. The tower is painted into panel C, so they are drawn per panel at
fractions measured off that image and ride with it wherever it repeats -- which
is why they live in `drawFarmPainted` and not in the props pass.

**One scale per sheet, taken from its first frame.** Normalising every frame to
the same height stretched the doubled-over rage frame back up to full standing
height, so the farmer got TALLER the angrier he got. A crouch has to be shorter
than a stand, and only a per-sheet scale keeps that.


Cricket guards in suits, `cricket0..5`, a six-frame panic loop with the antennae
whipping. `drawSpectators` plays the loop only while a chicken is going past at
speed and holds frame 0 otherwise. `drawLilChicken` is the flat fallback if the
frames have not loaded.

## Finding runtime errors

`sh check.sh` is a SYNTAX check and nothing more. It passes happily on code that
throws on every frame, which is how `pb is not defined` shipped: `updateCrows`
kept the obstacle loop's `pb`/`pt` names after its box became `rbox`, so the
near-miss line threw the first time a crow lined up with him -- and because it
threw from inside `updateCrows`, it took the rest of that frame's update with it.

`tools/shot.py` now installs an error collector **before** the page's own script
runs and prints anything it catches. That matters because the game's own
`window.onerror` keeps only the FIRST error and only in a DOM panel, so an
exception repeating every frame never reaches a screenshot.

**Two traps when hunting these:**

- **`game` in the devtools console is the CANVAS, not the game.** `<canvas
  id="game">` puts a `window.game` there, and the real `const game` is in the
  script's lexical scope where `Runtime.evaluate` cannot see it. Probing
  `game.crows.length` therefore reads a property of a canvas element and returns
  undefined, which looks exactly like the bug you are chasing. Use the debug
  flags and the `window.__*` harnesses instead -- they are deliberately on
  `window` for this reason.
- **A clean sweep proves nothing unless the path actually ran.** Five long
  sessions came back with no errors on the build that definitely had this bug,
  because no crow happened to cross him. `?crowshot=1` + `window.__crow('live')`
  reproduces it in five seconds. When a sweep is clean, check that the code you
  care about was reached.

## Before shipping any edit

    sh check.sh        # or: node --check on the extracted <script>

A duplicate `const` is a **syntax** error, which means the whole script never
runs, the error handler never installs, and every headless probe reports a clean
page. **A blank pass looks exactly like a pass.** This shipped once. `tools/`
has the CDP screenshot helper; `--headless --screenshot` lays out at 500px
regardless of `--window-size` and crops, which reads as a layout bug that is not
there.

## What difficulty is, and is not

Difficulty is **speed, spacing, and how many hazards share a screen**. It is not
withholding the art. The giant pizza was tier 3 and the cake tier 4, which at the
old thresholds meant surviving 72 and 100 seconds to see them - almost nobody
does, so every run was cones and cardboard boxes and the obstacles felt lame.
Variety now arrives at 9s and the whole cast is in play by 22s. If it needs to be
harder, move `game.diff`, the spawn gaps, and the zapper share - not the tiers.

## Pace

`PACE` (top of the physics block) is how fast the whole game runs; it is 1.85.
Raising the scroll speed on its own would only have shortened the time you get
to react, so the vertical model is scaled with it: **speeds by PACE,
accelerations by PACE^2**. That leaves every arc, gap and corridor exactly the
same shape in *space* and simply plays it faster -- the maths is that scaling
`a -> k^2 a` and the drag rate `D -> kD` gives `y_new(t) = y_old(kt)`. Hazard
spacing is in seconds, so the cadence per second stays put as well and only
the fixed human reaction time gets harder.

Everything written in velocities therefore has to be divided by `PACE` to keep
its old meaning -- the landing shake and the landing feather burst are, and
anything similar added later must be too. `?pace=N` tries another value; the
`?selftest=1` arcs are sampled per frame, so at 1.85 they show the old curve
read 1.85x further along, not a taller one.

## The HUD, the metre, and the score

The readout is **one small block pinned into the top-left corner** -- Jetpack
Joyride's shape: a `SCORE` label, the count, `BEST`, and the egg counter under
it, all inside `#hudTL`. It used to be a 54px score centred across the top,
which put the biggest thing on screen exactly where the next obstacle arrives
from. It is small on purpose: the number is glanced at between hazards, never
read. Fonts are unchanged -- Archivo 900 for the count, Bungee for the eggs.

`pad6` keeps the count six digits wide so it cannot jitter in the corner, and
`setScore()` wraps the padding zeros in `<span class="z">` at 26% opacity, so
the width is fixed but the eye only gets the digits that mean something. It
writes to the DOM only when the six digits change; it is called every frame.

**`UPM` is how many world units make a metre, and it is 60.** It was 10, and
that is what was wrong with the odometer: the screen is ~1300 units across, so
a viewport holding one barn and a stretch of fence claimed to be 130 metres
wide, and a ten-second run clocked 1200m. The number sprinted while the scenery
strolled and the two visibly disagreed. At 60 a screen is a believable ~22m of
farmyard, and he covers 10 m/s at the start and 23 m/s flat out -- a panicking
chicken, not a car. **Nothing about the world moved; only what we call the
distance it moves through**, so every arc, gap and spawn cadence is untouched.

Score is **1 point per metre** (`SCORE_PER_M`), the Jetpack Joyride deal where
the counter *is* the distance. The old rate was 0.25 per *unit* = 2.5 per metre,
which spun the odometer at 150-340 a second: too fast to read, and fast enough
that a 25-point egg and a 60-point near miss were rounding errors against it.
At 1/m the bonuses are worth chasing. The odometer tick sound fires every 10
metres for the same reason -- at the old rate its every-50 threshold was a
machine gun.

Anything measured in metres has to be `* UPM`, never `* 10`. `CROW_FLOCK_M` and
`NPC_TEACH_M` were restated (3000 -> 500, 400 -> 67) so they still fire at the
same *world* position they always did. `BEST_KEY` went to `v2`: bests banked at
the old ~15x rate would never have been beaten.

## Performance -- it is fill rate, nothing else

Profiled with `tools/prof.py` (wraps every draw section over CDP and reports
ms/frame, plus `Emulation.setCPUThrottlingRate` to stand in for a slow phone):
at a 6x throttle the **entire script cost 4ms a frame while the frames took
120ms**. None of the cost is JS. It is all rasterising, and rasterising is
priced in pixels. Do not go looking for slow loops.

The A/B, measured by no-oping one draw at a time at 4x throttle:

| change | frame time |
|---|---|
| backing store 2.25x -> 1x | **-72%** |
| drawStreetProps off | -36% |
| drawSky off | -28% |
| vignette off | -18% |
| drawLayers off | -12% |
| everything else | <6% each |

So two things were done, and they took the same run from 73ms to 30ms a frame
at 4x throttle (13 fps -> 33 fps):

- **The backing store is the dial.** `DPR` is capped at `dprCap`, which starts
  at 1.75 and is moved by `perfWatch` off the measured frame time: below ~43fps
  it gives up a quarter, and once it has dropped it never climbs back (that
  ratchet is what stops it oscillating). Floor 1x.
- **Full-screen gradients are cached.** A gradient is shaded per pixel on every
  fill, and the sky, the wall's top fade and the vignette are all full-screen
  and identical frame to frame, so each is painted once into a bitmap by
  `surface()` and blitted after that. The cache is keyed by size and `SCALE*DPR`
  and cleared by `resize()` -- **anything else cached per frame must be cleared
  there too**.

What is *not* worth doing: caching the parallax tiles per theme. A theme swap
rebuilds them and the whole rebuild measured 16ms at 2x throttle, i.e. one
dropped frame every 26s, for tens of MB of canvas held on a phone.

## Tools

    python tools/prof.py URL [secs] [cpu]   # ms/frame per draw section
    python tools/probe.py URL [wait]        # run a ?test flag, print the panel
    python tools/clip.py URL out.gif [s]    # real-time GIF over screencast
    python tools/shot.py URL out.png        # one screenshot, real device metrics
    python tools/title_art.py               # rebuild the title poster from ref/
    python tools/npc_frames.py              # recut the cow, pig and goat frames
    python tools/farm_seams.py              # where the farm panels should be cut
    python tools/gen_bg.py                  # generate the parallax layers (Gemini)
    python tools/bg_layers.py               # key, loop and trim them
    python tools/cage_art.py                # recut the intro barn and its door
    python tools/farm_strip.py              # the old one-image background
    python tools/build_apex.py              # rebuild the barn's roof from sheets/v2/barn_raw.png
    python tools/opt_audio.py --write       # re-encode the music small, both formats
    python tools/loop_menu.py [--write]     # cut the menu track to one loop of itself
    python tools/audio_report.py            # bitrate, channels and tag weight, no ffmpeg needed

There is an ffmpeg on this machine even though `ffmpeg` is not on PATH: the
`imageio_ffmpeg` package bundles one, and `imageio_ffmpeg.get_ffmpeg_exe()`
hands back the path. Every audio tool here goes through that. Do not conclude
there is no encoder available -- that was the assumption `audio_report.py` was
written under, and it is wrong.

`clip.py` uses `Page.startScreencast`, which timestamps frames, so the GIF keeps
the game's real timing. Screenshot-per-frame does not -- each capture stalls the
page and the clip plays back at the wrong speed, which is useless when the thing
being judged is how fast it feels.

## The title screen -- there are two, and `POSTER_TITLE` picks one

Both were built from the same key art, `ref/keyart.png`, in two sessions that
crossed. **`POSTER_TITLE = false` (the default): the menu is the LIVE SCENE** --
he is standing in the cage behind the bars from the moment the title appears,
and the menu sits on the right half to leave him visible. That is why the
landscape menu is laid out the way it is.

**`POSTER_TITLE = true`: the painted poster fills the screen** (`art/title.webp`
as a CSS background on `body.poster #menu`, with the DOM logo and tagline hidden
because the picture carries both and a scrim over the bottom 46% keeping the
chips and the PLAY button legible), and the first press blows it off the canvas.
It frames the art better; it hides him until it clears. Flipping the constant
switches the CSS class, the canvas branch in `drawTitle` and the `titleT` seed
in `startIntro` together -- there is nothing else to change.

It is built from `ref/keyart.png` by `tools/title_art.py`, and the two numbers
in that script are the whole story:

- **The crop is arithmetic, not taste.** A phone is about 0.47 wide for its
  height and the poster is 0.5625, so `background-size:cover` throws away ~17%
  of the width: only 0.085..0.915 of the picture is ever on screen. The logo
  and the chicken both have to live inside that, which pins the crop to
  0.171..0.781 of the source. The first attempt used 0.19..0.75, which put the
  T of HIT at 0.935 and a phone sliced it in half. **Re-check this if the crop
  is ever touched.**
- **The picture is extended, not stretched.** The poster is 16:9 and the screen
  is 9:16, so flat graded sky is added above and dirt below. The fill is one
  colour per row; stretching the edge pixels instead drags whatever touches the
  edge -- the barn's roof line, the tip of a siren ray -- into a full-height
  streak, which is what the first build looked like. Only the last ~34px before
  the seam cross-fade to the real edge colours, so anything cut off dissolves.

Nothing inside the poster is redrawn or regenerated. Every original pixel is
still there, in place.

**With the poster on, pressing PLAY blows it off the screen.** The canvas picks the same
file up (`TITLE`, `titleRect()`) on the frame the DOM menu hides -- `cover`
there is the same arithmetic as `background-size:cover` in CSS, so the handover
is invisible -- and `drawTitle` then grows and fades it over a third of a
second, uncovering the cell before he swings off the bunk at `T_UP`. If the
image has not loaded yet, `startIntro` leaves `titleT` positive and the old
drawn wordmark stands in.

Two bugs fixed on the way in, both worth knowing about:

- **The PLAY button skipped the escape.** It called `startRun()` directly, so
  the one control a player is most likely to press was the one that threw away
  the opening; only tapping elsewhere ran the intro. Both buttons now go
  through `startIntro()`, guarded by a mode check because a real press has
  already started it via `pointerdown` by the time the click lands.
- **The title blast never animated.** It walked `titleT` toward zero and then
  clamped it with `Math.min(-0.001, ...)`, so it stuck on the first frame; the
  kick set `-1` and the title simply vanished between two frames. It now walks
  the other way, `-0.001` to `-1`.

## The neighbours

A cow, a pig and a goat walk the farm road: `NPC_KIND`, `drawSpectators`,
`drawNPC`, twelve frames each in `anim/` (`cow0..5` strolling, `cowrun0..5`
panicking, and the same for pig and goat). They replace the cricket guards,
who belonged to a prison that no longer exists.

- **They walk facing back down the road.** Once the world scrolls past a static
  NPC it drifts left, so an animal facing forwards moonwalks. The panic set
  faces the other way, because it is a run away from the thing that just went
  past, and that turn is the whole beat.
- **Species comes off the position hash**, so the same animal stands in the
  same place on every run and a group can be mixed.
- **The panic window is deliberately lopsided**: `dx > -430 && dx < 900`. Tight
  on the approach so you get to see them being unimpressed first -- widening
  that side was the difference between "three walk cycles nobody ever sees"
  and the version in the game -- and long on the far side, so they are still
  going when he is most of a screen down the road.
- **They are scenery, and are left out of `FR.ready`.** 36 frames of cow, pig
  and goat gating the readiness count would keep the chicken a puppet through
  the first seconds of a cold load to decorate a verge he has not reached.
  `drawNPC` checks each image itself, so one that has not arrived costs a frame
  of scenery and nothing else.

The frames are cut from green-screen sheets by `tools/npc_frames.py`; the two
traps there (the characters wear the background, and the poses are not evenly
spaced) are written up in that file's docstring.

**Debugging them is a trap in itself.** They are sparse -- a group every 430
units, a fifth of the stops empty -- so a single screenshot easily catches a
frame with none on screen, which looks exactly like a wiring bug and cost a
long chase through save/restore depth, clip regions and canvas identity before
a six-frame strip showed them walking about quite happily. Grab a clip with
`tools/clip.py`, not a screenshot.

## The background is one painting

`sheets/v2/farm_strip.webp` is the whole farm: one image, one scale, tiled.
`tools/farm_strip.py` builds it from the three painted panels, and it exists
because drawing them as three was the source of every complaint about this
background.

What was wrong, and what replaced it:

- **They overlapped and cross-faded.** A 46-unit overlap with an alpha ramp
  down each panel's left edge meant one painting showed through another -- a
  silo ghosting behind a windmill. The strip is cut, not blended: the seam is
  *searched for* (`tools/farm_seams.py` scores every pair of columns near the
  facing edges and keeps the pair that meets best), so the join lands where the
  fence, the horizon and the grass already agree.
- **Each panel was scaled differently** so its own two landmarks would land
  where the game wanted them -- up to 17% apart, which is why the fence changed
  size halfway across the field. The ground lines are levelled by *sliding*
  each panel now, which keeps every fence post the size it was painted.
- **The painted sky is thrown away.** The three skies are not variations of one
  sky: (27,157,252), (56,182,253) and (1,117,216) at the same height. No
  correction reconciles that -- row-matching them left a step and flattened the
  art -- so the sky is keyed out and the game's own gradient shows through the
  whole strip. One sky by construction. The clouds survive: they are white and
  enclosed by sky, so the flood that clears it never reaches them.

The remaining tone differences are in the fields, and those are matched row by
row and then feathered across each seam. **Smooth the corrections before
applying them**: measured per row and used raw, a row that happens to be mostly
cloud has almost no sky left to average, the delta jumps against its
neighbours, and the sky ends up in horizontal stripes.

Costs nothing: 28.4ms a frame before, 28.9 after, at a 4x CPU throttle.

## Loading: six at a time, not all at once

`IMQ` in `loadFrames` is a queue, and it exists because a browser will not do
this for you. The frame sets come to 130-odd images and they used to be
requested the instant the script ran -- all of them, alongside the background
art, the cage and the props, about **170 requests in flight**. A local server
does not care. A CDN does: some of those requests come back having transferred
nothing at all (`decodedBodySize` 0 after a couple of seconds), and survivors
can take twenty seconds.

That is how the live site drew the vector fallback for a full minute while
every file it needed was sitting there serving perfectly to anything that asked
for one on its own -- the 190KB background was simply one of the requests that
got dropped. Three panels hid it: losing one of three still left a background.
One strip does not.

Six at a time now, scenery last, and the image objects are created up front so
anything looking one up still finds it -- an `Image` with no `src` reports
`naturalWidth` 0, which is the "not ready" the draw calls already test for.

**Test a change like this against the deployed site, not localhost.** Nothing
about this was visible locally; every asset loaded instantly and the game
looked right.

## The obstacle set — everything is wire

There is no jumping half. The farmyard props, the crate columns, the crows,
the things that fell out of the sky, the bale trap, the rotating bar and the
windmill are all gone, and with them the `air`, `fall`, `roll` and `bounce`
obstacle kinds and every branch that served them. What is left is four
families, and all four are electric:

| family | keys | what it asks |
|---|---|---|
| zapper | `zap_h` `zap_v` `zap_d` `zap_m` | pick a side |
| corn | `corn_one` `corn_clump` `corn_row` | get over it |
| fence | `e_fence` `e_wire` | get over it, higher |
| ladder | `e_double` `e_gate` `e_multi` `e_g2a` | find the opening |

**Variety has to come from the wire, because the wire is all there is.** A
fence at two heights is the same fence twice. A wire at two ANGLES is two
obstacles, and one you must go under is a different question from one you must
go over. That is what the zappers are for, and it is why nothing about a
zapper is fixed by its type: `rollZap` rolls the angle, the length, the height
and the drift at spawn.

**`rollZap` is rejection sampling, not arithmetic.** The constraint is not a
range you can solve for -- the angle changes how much vertical room the wire
eats and the drift changes it again -- so it rolls, checks, and rolls again.
Twenty tries, and the last resort is a guaranteed-legal flat wire low in the
column, so it cannot fail to place something on a screen too short for the fun
ones. A drifting zapper's corridor is measured at the ENDS of its sweep, never
the middle: a corridor that is only open half the time is not a corridor.

**The rule both `rollZap` and `?obtest=1` enforce**: a side is either a
corridor of at least `CLEAR`, or it is under `SHUT` and plainly reads as no
way through. Never the in-between -- the 200 units that look flyable and are
not, which is the shape of every unfair obstacle ever shipped.

`CLEAR` is 330 and it is the single number that says how tight this game is
willing to be; every ladder's gap range is clamped to it. Raise that rather
than widening pieces one at a time.

**Every lethal post carries a live wire up it.** Bare timber is the thing you
have been flying over all game, so an upright that reads as scenery and then
electrocutes you is the game lying, however honest the hitbox is. `postWire`
marks a wire `thin` -- a third the weight -- because at full strength the glow
is 26 units and `e_posttall` is 34 wide, and the post vanished inside its own
electricity. The wire also carries an ink rim under its core: cyan on a bright
blue sky is the lowest-contrast pairing in the game, and a zapper IS its wire.

Each piece describes itself once in `build()`, and the drawing, the collision
and the near-miss meter all read that same description -- so the wire you see
and the segment you die on are the same two numbers. Geometry is in world
units with y measured UP from the ground; the flip to screen happens once, in
`drawElec`.

`elecSpec` must copy through anything `build` needs off the spec. It did not
copy `zap`, so every zapper spawned with no angle and no length and drew
nothing -- silently, because a missing image is a fallback here and an
undefined number is a NaN, and neither throws.

### Patterns, not dice

`spawnPattern` picks from `PAT`: short sequences with their spacing in
SECONDS, followed by a safe section. Seconds and not pixels, because the world
speeds up as a run goes on and pixel spacing would quietly tighten every
pattern into a different one. Difficulty is which patterns have unlocked and
how much shorter the safe tail is -- never a hazard that got harder to see.

Patterns are written in **tokens** (`#zap` `#corn` `#fence` `#lad`), not keys,
so a pattern says what SHAPE it wants and the tier decides which one that is.
That is why the table did not have to be rewritten when the roster was.

Corn keeps a short cooldown (`game.cornT`, 5-9s) -- it is a third of the
roster now rather than one prop among twenty, so the cooldown is there to stop
two corn beats running into each other, not to make the crop rare. **`?obtest=1`
zeroes it every iteration**, because that loop does not advance the clock and
the crop would otherwise appear once per tier and lock itself out of its own
test.

### Looking at them

- `?ob=KEY` parks one hazard mid-screen in a live run and holds it there
  (`game.freeze`, which is 6% time, not a pause -- a paused game does not draw).
  It hangs the setup on `window`, because everything is inside an IIFE.
- `?hit=1` draws every lethal shape over the art: boxes magenta, wires yellow
  at their true lethal thickness. This is how "the sprite fills its hitbox"
  gets checked instead of asserted.
- `tools/obshot.py URL out.png key,key --hit` builds a contact sheet from those.
  `OBSHOT_SETTLE` overrides the wait; 6s is plenty locally and nowhere near
  enough against the CDN.
- `?obtest=1` spawns 240 patterns per tier and checks openings, half-gaps and
  spacing. Corridors come out >=330, gaps >=0.85s.

Art the set no longer uses is still in `art/farm` -- nothing requests it, so it
costs nothing, and it is there if the farmyard props are ever wanted back.

## The angry crows — the one hazard that comes at you

Jetpack Joyride's missiles, in feathers, and the only hazard in the game that
moves horizontally. **The alert is the feature; the bird is the payoff.** A
hazard closing faster than the world scrolls is unfair unless it is announced,
so every crow spends `CROW_WARN` (1.30s) as a badge pinned to the right edge of
the screen at the height it will come in at.

The badge has two states and they look nothing alike, on purpose:

| | Colour | Blink | Extra | Meaning |
|---|---|---|---|---|
| tracking | amber | slow, soft beep | chevrons | it is still following your altitude |
| locked | red | fast, sharp beep | dashed lane line + red edge wash | the height is fixed — MOVE |

`CROW_LOCK` (0.46s) is how long the locked state lasts before launch. That is
the skill in the whole thing. Without a lock the bird just follows you into the
floor; with a much longer one you step out of the lane before it fires.

Then it launches off the right edge of the **camera** and flies left at
`CROW_SPEED` (1080 · PACE) **on top of** the world scroll, so it closes at about
1700/s and crosses in ~0.65s. Four painted frames off a Gemini Studio sheet,
cycled at 17Hz, with feathers and speed lines off the tail.

Things that are the way they are for a reason:

- **A crow is never in `game.obstacles`.** Obstacles are placed ahead in world x
  and stand still while the player runs onto them. A crow is the opposite in
  every respect. It lives in `game.crows` and is updated OUTSIDE the mode chain,
  next to `updateDoor`, so a bird already launched flies on through the death
  animation. One still winding up is dropped instead — a siren counting down
  over the score card is a promise the run cannot keep.
- **"Clear air" is not the horizon, it is the arrival window.** The first
  version asked for an empty field ahead and so the crows never flew once: the
  pattern spawner always has something out there, by design. `crowWindowClear`
  checks only the stretch the player will be standing in when the birds arrive
  (`crowSpan()` away, about 1.35s wide), and `launchCrows` then pushes
  `game.spawnT` out so nothing new can land in it. Measured, not assumed —
  `?crowtest=1` runs the real spawner against a moving player for two minutes a
  tier and reports the wait: **a volley every 7–10s, worst case ~12s.**
- **The lane runs 40 to `ceilH-10`, past where he can get to.** A lane that
  stopped short of the roof clamped the lock to a height that missed a
  ceiling-hugging chicken by a body — and since a volley suppresses the pattern
  spawner, the sky he was camping in was empty too. `?crowtest=1` checks the
  lock reaches him at both extremes.
- **The art overhangs the hitbox.** The box (`CROW_HW/HH`, 140×74) is the head
  and body only; wingtips and tail feathers are not a hit. `CROW_AX/AY` are
  where that lethal centre sits inside the frame, measured off the registered
  sheet, so recutting the art cannot drift the box off the bird. `?hit=1`.
- **Volley size is chosen once and kept** until a window opens. Re-rolling it
  each retry quietly selects for whichever size fits, and the three-bird volley
  needs the widest window of all. 1 bird early, 2 from diff>0.50, 3 from >0.82,
  0.70s apart — the second badge locks onto wherever the first one chased you.

### The art

`tools/gen_crow.py` → `sheets/v4/crow_raw_*.png` → `tools/cut_crow.py` →
`art/farm/crow1..4.webp` + `crowhead.webp` (the badge icon). Loaded through
`loadProp`, like every other painted hazard, with a drawn fallback under it.

A flap CYCLE needs one thing a set of props does not: **registration.** Cutting
each frame to its own bounding box and centring them makes the bird lurch,
because the box is mostly wing and the wing is what moves — and Gemini draws one
cell of a 2×2 smaller than the rest. Both are fixed off the one feature that is
identical in every frame, the open orange beak: each frame is scaled so its beak
matches the median beak width, then hung off the beak TIP. After that the head
holds still and only the wings beat. `python tools/cut_crow.py --preview` writes
a strip and a GIF to check that by eye.

### How many, and how soon

Tuned down hard after the first play with them in, and the numbers are all in
one place at the top of the section:

| | was | now | why |
|---|---|---|---|
| `CROW_T0` | 24s | **40s** | the run has a vehicle, a livestock lesson and four hazard families to teach before it needs a homing one as well |
| `CROW_FLOCK_M` | 1500m | **3000m** | a screen with two locked badges on it is a different game from the one the first minute teaches |
| gap between volleys | 6.5-11s | **11-17s** | at 2000m the old numbers were one every five seconds, which is a rhythm rather than an event |
| how much the gap closes | to 0.60 | **to 0.75** | same reason, at the far end of a run |
| badge radius | `VH*0.086` | **`VH*0.058`** | it was the size of the chicken, for something that is one dodge |

**A crow takes the vehicle, not the run.** It is a hazard, and while there is a
vehicle to take, a hazard takes it -- being killed outright by one thing and
merely dismounted by another is the kind of inconsistency a player reads as a
bug in their own understanding. Both the obstacle loop and the crow loop ask
`rideBox()` for what can be hit, because two definitions of that drift apart:
the first version of this had the crow loop keeping the obstacle loop's `pb`
and `pt` names after its own box was renamed, which threw `pb is not defined`
every frame a crow lined up with him.

## The intro barn, and the neighbours in the field

The barn is `sheets/v2/cage_scene.webp` and its door is `art/cage_door.webp`,
both regenerated by `tools/gen_bg.py`'s sibling `tools/cage_art.py` in the
map's own style -- flat cel, bold outline -- and, crucially, **cut out of their
sky**. The old barn was painted with its own farm behind it (a windmill, a
fence, a line of hills), which is why it needed a fade down its right edge to
hand over to the map, and why that hand-over ghosted one picture through the
other. There is no fade now, in either direction, and no wall stretched out to
the screen edge either: the parallax layers simply show behind it.

Everything the intro needs off that art is a fraction in `CAGE`, measured, not
guessed -- the doorway, the straw he stands on, the roof apex. **`doorH` is the
one number that sizes the barn**: the chicken is a fixed 175 world units, so
that constant really means "how big is he next to it". 325 made a barn he was
lost inside; 250 is the one in the game.

Automating the doorway measurement was a false economy -- a barn drawn with a
black outline has dark pixels in every row, so counting them says the doorway is
the whole picture, and the longest-run test that fixed that then found the roof
line instead. It is four numbers read off a grid overlay in a minute.

**The neighbours and the farmer are in the field, not on the road**: their own
parallax (`NPC_F`), their own scale, feet on the painted ground line. The farmer
is the one exception to `NPC_REACT` -- the animals were calmed down because a
field of livestock all panicking at once is noise, but he is the man whose
chicken just left, so him standing in his own field yelling about it is the
joke rather than the noise.

Two traps, both of which looked like "the NPCs are not drawing":

- **Laid out along one axis, looked for along another.** `first` came from
  `cam.x` while their position used `cam.x*par`, so every one of them sat off
  the right edge by a gap that grew with the run.
- **`drawBgLayers` took the layer to stop after**, so the second call -- the one
  for the fence -- started at the beginning again and redrew the hills and the
  farm *over* the neighbours who had just been drawn between them. They were on
  screen the whole time and painted over a frame later. It takes a list of
  layers now, which also stops the two big layers being paid for twice a frame.

## The truck -- the vehicle

Jetpack Joyride's contract, and every part of it earns its place: a vehicle is
picked up mid-run, it **replaces** the control you already know, the level
changes to suit it, and **a hit takes the vehicle rather than the run**. That
last one is why a vehicle reads as a reward instead of a handicap -- riding is
strictly safer than not, so you chase the pickup.

It is a shopping basket on monster-truck wheels, and it is a GROUND vehicle.

- **Control.** Holding does nothing. The press is a jump -- one off the road and
  one more in the air (`RIDE_JUMP`, `RIDE_JUMP2`) -- and that is the whole
  difference from the bird, whose entire control is the hold. Same solved
  movement model; only the constants change.
- **TAKING IT CUTS THE FARM'S POWER.** This is the best thing about it. Every
  live wire on the board stops killing on the frame of the pickup (`wireHot()`,
  read by `elecDist`), and the picture follows over half a second -- `game.gridT`
  goes 1 to 0 and each wire independently *strobes* against the level rather
  than crossfading, so it reads as a substation tripping. Dead, a wire is a
  slack grey cable. Only the wires go: posts, corn stalks' own boxes and painted
  hardware stay solid, so a ladder becomes two posts to jump rather than an
  empty screen. Lethality flips on a boolean and the picture eases, which is the
  right way round -- the only frames where they disagree are frames where the
  wire looks live and is already harmless.
- **It brings its own obstacles.** `RIDE_PAT` used to be the flying fences at two
  heights, which made the reward for taking a monster truck *the same obstacle
  with a fence on top of it*. The roster is now six `roadblock()` pieces built
  out of farmyard props with no wire on them at all: `r_tyres`, `r_trough`,
  `r_crates`, `r_bales`, `r_drums`, `r_wagon`. Crates and drums go **through**
  (`spec.smash`, which lives on the piece now rather than in a `SMASHABLE` list
  half the game away from the collision test); the rest you jump.
- **They wear hazard stripes** (`drawHazardBase`). The background is painted full
  of hay bales, because it is a farm, so a seventh bale standing on the road is
  not an obstacle -- it is scenery you happen to die on. The electric set never
  had this problem because it glows. Nothing in the background has a striped
  plinth.
- **THE SCALE WAS THE REAL BUG, not the tuning.** At `GROUND*0.46` the rig was a
  third of the screen wide, and that number was set when the sprite was the cart
  alone. A piece 300 wide plus a truck 379 wide overlap for 680 units of road,
  while the whole airtime of a jump at the slowest speed in the game covers
  about 500 -- the low tiers were *arithmetically impossible* while the fast
  ones were fine, which is the shape of a bug that reads as bad difficulty
  curve. Fixed with a smaller rig (`GROUND*0.335`), lighter gravity for the hang
  (`RIDE_G` 0.60 -> 0.27; a truck jump is the one thing here allowed to float),
  and impulses to match.
- **Two ceilings.** `VY_UP*RIDE_VUP` rails the velocity -- the impulse and the
  rail have to be raised *together* or neither does anything, which is why
  `RIDE_VUP` is next to the impulses and not buried in the physics. Separately
  `rideCeil()` rails the *height*: `CEIL` is headroom measured for a bird 142
  tall, and the rig is nearly 300 including its driver, so the bird's rail threw
  it three quarters of the way out of the picture and the jump read as a glitch.
- **`rideApex(impulse)` solves the height in closed form** -- `(u - vT*ln(1 +
  u/vT))/k` -- and the teaching course is laid out of it, so changing the jump
  moves the lesson instead of quietly making it a lie.
- **`?ridetest` is how any of this is known.** It does not reason about the arc:
  it drives. One piece on an empty road, press at a given distance, run the real
  update loop, sweep the distance, and report the **window** of presses that
  clear -- 270-450px everywhere now, and 0 before. A piece is tested at its own
  tier's pace, because the arc is a fixed number of *seconds* and slow running
  covers less road. It also asks `elecDist`, not the paint, whether the grid is
  really off, and checks the closest pair in any pattern against the time a jump
  takes.
- **`?demo=1` could not drive it.** The autopilot set `p.thrusting` directly,
  which never reaches `thrustOn()`, and a jump happens on the edge -- so every
  measurement came back "never left the ground". It presses now.
- **Landing recharges the double jump.** It never did: `rideJumps` was zeroed
  once, in `startRide`, so the second press worked exactly one time per pickup
  and every landing after that left one jump and no way to know why.
- **It is faster** (`RIDE_BOOST`), and calmer -- wider tails in the table and
  crows at 1.8x the gap, because the vehicle is where the run breathes out.

**The frames.** `TRUCK_FR` is four pictures with Nugget *painted into the cart*
(`sheets/v2/truck_ride.png` -> `tools/cut_truck.py`): driving with both wings on
the wheel, the launch with his cap already leaving, over the top braced and
shouting, and the compressed landing. `truckFrame()` reads the physics rather
than running a clock, so the animation cannot drift from what the truck is doing;
`rideLand` is the only timer, and only because the landing frame has to hold for
a beat after the tyres are down.

- He is **not** drawn separately any more. He used to be lifted half a truck up
  so his head cleared the rim, which works for exactly one pose -- the moment the
  rig tilts, a bird hovering at a fixed offset over a tilted cart is a bird
  standing on nothing.
- The sheet is cut by **connected component**, not by column gaps: the four
  trucks are drawn at four tilts and overlap in x, so a vertical cut puts half a
  tyre in the wrong frame. The flying cap is a loose blob and is given back to
  the nearest truck rather than dropped.
- ONE scale for the whole sheet, off the driving frame's width. Normalising each
  frame to a common box is what makes a sprite breathe as it animates.
- **The exhaust is drawn, not painted**, because it has to flicker and because
  its length is a number the rest of the game reads. Each frame carries `px`/`py`
  -- where its own pipes ended up, as fractions of its own picture, read off the
  art. A single offset for all four put the flame on the grass behind the truck
  with nothing attached to it.
- **Dust, not sparks** (`smoke()`, and a `'smoke'` kind in `drawParticles`). Big,
  dull, slow, rising, growing. A wall of it off the back tyres on the launch, a
  ring under the truck on the second jump because there is no contact to feel,
  and a skirt of it on the landing.

**The pickup is a mystery egg** (`art/mystery_egg.webp`), not a small picture of
the truck -- a screenshot of the reward answers the question before the player
has crossed the screen for it. It is placed by the **column**, not the point:
`spawnBasketDrop` used to roll twenty heights at one x and accept the first that
missed a wire, which passes an egg threaded between two rungs of a ladder, so
going for it was punished and ignoring it was punished. The x now walks forward
until the road is clear for `DROP_CLEAR` either side, and the next pattern is
held off until the pickup is behind him.

**Taking it lays a lesson** (`layRideCourse`). A vehicle whose controls differ
from the game's has to teach them, and the only honest way to teach a jump is to
put something you want in the shape of the jump: one arc that peaks inside a
single press, then one that is 1.6x *longer* -- not higher, because the play area
is barely taller than one jump, so the second press mostly buys hang. Obstacles,
crows and the normal egg spawner are all pushed past the end of it.

**What it does to the neighbours**, and the two read differently on purpose:

- **Scorched.** The flame reaches about `NPC_BURN` behind the truck. Anything in
  that stretch drops its amble and runs, facing the way it is running. The panic
  sets already existed, so this costs a frame table and a flip.
- **Bowled.** `NPC_HIT_W` of bumper, at any height low enough to be hitting
  something -- driving through one and landing on one are the same event as far
  as the animal is concerned. They tumble off in an arc and fade.

The livestock are derived from a hash rather than stored, so **the only state
kept is the ones that have been hit**: an index and a moment. Everything else
stays derived, which is why a field of them costs nothing.

`?ride=1` starts a run already in it -- the only sane way to look at a vehicle
that otherwise turns up once every twenty seconds. The pickup is placed by
`eggFree`, the same "is this bit of sky safe" test the eggs use.

**A crow takes the vehicle too.** It is a hazard, and a hazard takes the
vehicle rather than the run while there is one to take -- being killed outright
by one thing and merely dismounted by another is the kind of inconsistency a
player reads as a bug in their own understanding. Both the obstacle loop and
the crow loop ask `rideBox()`, because two definitions of what can be hit
drift.

## The music, and how small it got

Three passes, in this order, and the order is the point -- each one was only
worth doing because the one before it had been done properly.

1. **Format and bitrate** (`tools/opt_audio.py`). The masters were 192 kbps
   joint-stereo for music that plays under sound effects on a phone speaker.
   Opus 64k for Android and every current browser, MP3 96k as the fallback for
   Safari older than 17.4, picked by `MUS_EXT`. The 192k originals live in
   `audio/src/` -- they are the only masters there are, and re-encoding a 96k
   file later to chase another 20% would be a third generation of the same
   artefacts.
2. **Length** (`tools/loop_menu.py`). The menu track was a three-minute piece
   playing behind a screen nobody looks at for more than a few seconds, on a
   loop. Cutting it to one loop took it from 2127 KB to 188 KB (MP3) and 1610
   to 159 (Opus) -- about 22x smaller than the master it started as.
3. **Channels.** Mono, for the one place in the game where the music is the
   only thing playing.

**Where to cut is measured, and the measurement has two halves.** The track is
decoded to a coarse energy envelope and autocorrelated: music that repeats
every N seconds peaks at N. That alone is not enough, and the way it fails is
worth remembering -- the longest well-correlating period here was 48s, and the
cut it produced measured **8661 RMS at the head against 2357 at the tail**, an
audible drop every time round. Correlating well across a whole track says
nothing about whether the particular cut point can be come back to. So the seam
is scored as well, and 24s wins: it correlates best AND matches its own start
to within 4%.

The trade is that the tune goes round more often. For menu music behind a
static screen that is the right way round; re-cut at another period with the
tool if it ever stops being.

## Flight is solved, not stepped

`dv/dt = a - k*v` is the entire movement model -- gravity, thrust while held,
drag -- and it has a closed form. It used to be integrated as `v -= v*k*dt`,
which is the Euler approximation of that exponential, and **the error grows
with the step**. Measured across 60/90/120/144Hz before the fix: a 4.13%
spread on the same half-second hold, about 28 units of altitude against
corridors 330 wide. Nobody reports that as a bug. They say the game feels
wrong on their phone.

`updatePlay` now uses the solution:

```
vT = acc/k;  e = exp(-k*dt);
vy = vT + (vy - vT)*e;
y -= vT*dt + (vy0 - vT)*(1-e)/k;      // the exact integral, not vy*dt
```

The position integral matters as much as the velocity one -- moving by `v*dt`
after solving for `v` puts the step error straight back into `y`. Two `exp()`
calls a frame, no accumulator, and the game keeps the single loop it has.
Spread is now 0.04%, which is float noise.

**The feel moved slightly and on purpose.** A half-second hold tops out at 707
rather than 659 at 60Hz, because 659 was the approximation undershooting and
707 is what the constants were always asking for -- high-refresh displays were
already near it. If that ever reads floaty, `THRUST` is one number.

`?selftest` measures this rather than asserting it, replaying one hold at four
rates. **The hold is counted in FRAMES**, because 1/6, 1/3 and 1/2 of a second
are whole frames at all four and 0.20s is not: scripted against a wall clock,
144Hz holds for 0.194s and the test reports its own sampling as a physics
fault. It did exactly that on the first run.

`?hit=1` draws Nugget's box as well as the hazards' -- solid is the broad
phase, dashed is the 8-unit inset that actually kills. The audit it makes
possible: the box is fair and asymmetric in the right direction. His wing
sweeps outside it behind him and his comb pokes over the top, neither of which
kills, while the beak and feet sit on the edge. The world scrolls left, so the
forgiving side is the trailing side.

## Nothing gets knocked flying

Obstacles, smashed corn, the hazard that takes the basket, and the livestock
all hold their ground on contact. They did not used to: the thing that hit you
was launched into an arc and spun off.

That is a fine gag when the hazard is a loose crate and a bad one when it is a
fence bolted to the ground -- and worse for the electric ladders, whose wires
are **geometry rather than a sprite**, so they tumbled with the frame and left
live wire lying diagonally across the road while the ragdoll bounced past it.

It also told the wrong story. At the moment a player dies they are looking for
WHAT HIT THEM, and the answer should still be standing where it was.

`hitBy` stays -- it is what stops one obstacle firing the collision twice --
but the spin and launch velocity are gone from every caller. Two of the three
were already dead: **nothing integrates a hit obstacle during PLAY**, only
during dying, so `smash()` and `loseRide()` had been setting numbers that never
moved anything. A bowled animal bolts on the spot in its panic frames instead;
its entry is still dropped after two seconds because it is keyed by the stop's
index and would otherwise grow for as long as the player survived.

## The retry loop, and Nugget's name

Dying cost up to 2.2s of ragdoll and then the full 2.0s barn escape again,
because retry called `startIntro` like a first run did. Over four seconds to
get back to the thing the player was enjoying, on a game whose entire loop is
"again".

A **first** run still opens with the escape; it is the game's introduction to
itself. A **retry** gets `startQuick`: no cage, straight into the run, with
READY then GO inside `GO_TIME` (0.85s) while the spawner and the crows are
held off by exactly the length of the beat. **Input is live throughout** -- it
is a beat to read the screen, not a gate to wait behind, and taking the
controls away for even half a second would undo the responsiveness everything
else here is for. The ragdoll's cap came down 2.2s -> 1.5s as well; the
settled-ragdoll test usually fires at 0.95 and that was only the fallback.

`drawGo` runs **after the camera is restored**, so a countdown cannot shake or
zoom with the world, and on canvas rather than the DOM -- one text draw for
under a second, on frames where the player is already flying.

`overLine()` puts his name on the card. One line, at the top, above the number,
and nowhere else: the card exists to show a score and a joke in every slot is a
joke nobody reads twice. **Two lists**, because "THAT WAS CLOSE" is not a death
message, it is what you say to somebody who nearly beat their best -- it is
only reachable within 10% of it, and the line is picked **before** `finish()`
overwrites `game.best` or that comparison is the score against itself and true
every time.

## Assets: what ships, and how big

**3.5 MB before the player touches anything, 5.1 MB once they press PLAY**,
184 requests, measured with the cache disabled -- not summed off disk. Music is
the difference between the two numbers and it is gesture-gated: `audioInit`
only runs on a real press, so nothing in `audio/` is fetched until PLAY. Note
that `?auto=1` presses it for you, which is why a measurement taken with that
flag shows the larger figure.

| | files | |
|---|---|---|
| `art` | 23 | 1699 KB |
| `anim` | 134 | 1085 KB |
| `index.html` | 1 | 328 KB |
| `art/farm` | 19 | 249 KB |
| `art/bg` | 3 | 112 KB |
| background strip | 1 | 63 KB |
| fonts (Google) | 3 | 50 KB |
| music, after PLAY | 2 | 1659 KB |

Re-measure with the probe rather than trusting this table -- both sessions add
art, and it drifts.

**Images are all WebP and all lossless.** `tools/to_webp.py` did the last
fourteen (2336 KB -> 1315 KB) and **refuses to delete a PNG whose WebP does not
decode back to the same pixels**. That check caught its own first version:
comparing the whole RGBA buffer failed ten of fourteen with a 255-channel
delta, because a PNG may store any colour it likes *underneath* a fully
transparent pixel and WebP normalises that away. It compares alpha exactly
everywhere and colour exactly where alpha is non-zero, which is what lossless
means for a sprite. Lossless and not q90 because these are cut-out art: flat
cel shading, hard ink outlines, an alpha edge -- the three things lossy rings
on. Half the saving was there anyway.

**Music ships twice and downloads once** -- see *The music, and how small it
got* above for the encode chain. `MUS_EXT` asks `canPlayType` at load and takes
Opus where it exists, MP3 96k where it does not. The Opus set is 2.8 MB, the
MP3 set 3.9 MB, and no player ever fetches both.

Two things that section does not cover, and both matter for a bundle:

**The soundtrack is three tracks, and only three exist.** `MOVEMENTS` is
`spy_long` and `spy_long_b`, plus `music_menu`. Five more were carried for a
while and referenced by nothing -- never fetched on the web, but they *would*
have gone into an APK -- so they were deleted on 2026-09-05, taking the shipped
audio from 12.9 MB to 6.7 MB across both formats. Their 192k masters are still
in `audio/src/`, so bringing one back is a re-encode rather than a
regeneration. `?track=NAME` only accepts a name that still exists; an unknown
one 404s, the error handler marks it dead, and the run is silent rather than
broken.

**`tools/audio_report.py`** reads bitrate, channel mode and duration straight
off the ID3 header and the first MPEG frame, so it works on a machine with no
audio tooling installed at all -- which is how the 192k masters were diagnosed
in the first place, before there was an ffmpeg on the box to ask.

**Android estimate:** ~4.9 MB images and code, ~2.8 MB music, ~50 KB fonts if
bundled locally = **~7.6 MB of assets**, plus ~3 MB for a Capacitor/WebView
wrapper, so **an APK around 10-11 MB** and an AAB nearer 8-9. At bundle time
drop `audio/*.mp3` (Android has Opus natively) and `audio/src/`.

## The loading gate, and the roof that would not shut up (2026-09-05)

Three things, all reported as one complaint: *"remove the flying sound when I
hold"*, *"the game progressively opens animation, they load a bit"*, and
*"make sure the character and coins and obstacles and npc load before I start"*.

### The flying sound was the ceiling, firing 35 times a second

`S.flap` has been a deliberate no-op since 2026-09-05 and the wind bed **ducks**
to 0.22 while you hold, so neither of them was it. What was actually playing:

```
held for 3s   →  {takeoff: 1, ceiling: 104, tick: 2}
```

Holding pushes `vy` negative again on every frame, so at the roof
`if(p.vy < 0)` was true every frame, and the contact sound plus three feathers
fired at the frame rate. At 35 a second a sound stops being a sound and becomes
a texture you cannot stop hearing.

**This is the exact bug the camera shake was already fixed for** — the comment
above it explains that the roof "costs nothing, you hold against it for seconds,
and it therefore fires over and over" — and the sound was left doing it.

Now edge-triggered with hysteresis: it speaks once on arrival and cannot speak
again until he has dropped `CEIL_CLEAR` (90 units, about his own body). A bare
`wasTouching` flag is **not** enough — the bounce sets `vy` positive for a frame
or two and he re-touches immediately, which flickers, and a flicker at this rate
is the original bug back. Measured after: `{takeoff: 1, ceiling: 1, tick: 2}`.

**Generally: any sound fired from a condition that a held button keeps true is
a per-frame sound until proven otherwise.** Wrap `S` and count the calls —
`tools/` has no harness for this because one probe answered it, but the shape is
three lines of CDP over `?dbg=1`.

### Nothing starts until the art is in

Everything was already queued at boot; nothing was ever **waited for**. So the
hazards drew as flat blocks, the neighbours popped into the field, and the
chicken was a drawn rig until his frames landed — 20.2s for the first prop over
the CDN, measured earlier.

`LOAD` counts and `gateStart()` waits. The counting is the part worth
understanding:

**One property setter is intercepted — `src` on `HTMLImageElement.prototype` —
so every image counts itself, wherever it is created.** A hand-written manifest
was the obvious alternative and would have been wrong the first time somebody
added a sprite; the image sources are spread over the frame queue, the prop
lane, the parts, the backgrounds, the truck, the clouds, the cage and the
cosmetics. The interception is the first thing in the file because it has to
run before any image exists. It counts 186, which is exactly the game's image
requests (191 total minus index.html, three audio files and the favicon).

- The bar **only ever goes forward** (`shown = Math.max(shown, f)`): `total`
  grows while the file is still executing, so a raw ratio steps backwards, and
  a loading bar that goes backwards looks broken even when it is honest.
- `thrustOn` returns early and the PLAY button is gated, so a press cannot start
  a run against half an atlas. Verified: at 14s into a cold 2 Mbps load the mode
  stayed `menu`.
- **The give-up condition is a STALL, not a clock, and getting that wrong was
  the one real bug in this change.** It shipped as "give up after 20s" and then
  fired at 20.5s on a perfectly healthy 2 Mbps load of the *live* site — the
  exact connection the gate exists for. **A slow line and a broken one are
  indistinguishable on a clock and obvious on a counter.** So: give up when
  nothing has arrived for `STALL_MS` (9s). While the bar is still moving we
  wait however long it takes, because the player can see it moving and that is
  the entire job of the screen. `CEILING_MS` (90s) is only a backstop against a
  pathological trickle.
  All three paths are tested, and the second one is not obvious: a **drain**
  opens at 15.2s on 2 Mbps; going **offline** opens it in 0.4s, because every
  pending request fails immediately and an error counts as done — the gate
  cannot hang on a disconnect; a **trickle** (sockets open, nothing arriving)
  opens it 9.3s later with `gaveUpOn:'stall'`. A gate that never opens is worse
  than the bug it fixes, so test the giving-up, not just the finishing.
- `?noboot=1` skips the wait, for harnesses that drive runs directly. Every
  `tools/` probe needs it.

Warm cache is ~110ms, so a returning player sees a flash, not a screen.

### The art was 6-15x oversampled, and lossy is still the wrong answer

`tools/shrink_art.py`. `part-shoe` was a 599px picture drawn at ~40 device
pixels; `part-leg` 233x1024 drawn at 19. Thirteen files were 1.26MB of a 4.4MB
payload. Target is derived, not guessed: `SCALE = min(CH/980, CW/1450)`, so 4K
landscape gives 2.20 px per world unit — round to 2.3, x1.5 for the rig and the
intro, **3.45 px per world unit**.

The tempting alternative is to leave the resolution alone and encode lossy. It
is worse, and the comparison only means anything **at the size the sprite is
actually drawn**:

```
part-wing   resize 0.63 RMSE   lossy q90 1.40   both 2.60
part-shoe          1.59                  0.78        4.48
part-leg           0.94                  0.88        6.49
```

Cut-out art is the three things lossy WebP is worst at at once: hard ink
outlines, flat cel fills, and an alpha edge. Resizing is near-invisible.

**The four hats are the exception and prove the rule about looking first.** They
were rejected by the sprite path for coming back RGB — because they are not
sprites. They are opaque 1024x559 reference *renders* shown as picture cards by
`chickens.html`, never composited, with no alpha at all. Photograph-shaped
images get photograph treatment: 512px and q88, 92% off each. They are not in
the game's payload.

1261KB -> 341KB. Load at 2 Mbps went 16.95s -> 15.19s; the rest is the 3.5MB
the game genuinely needs, so it is bandwidth-bound now rather than wasteful.

### One thing found and NOT changed

**The painted parts are a fallback that the gate has made nearly dead code.**
`drawChicken` returns early when `FR.ready`, so the rig only draws when the
frames have not arrived — and the gate now guarantees they have, before play.
The parts are still downloaded every load. Instrumenting `drawImage` across the
menu, intro, a run, a death and the ride recorded 100 images and **not one
`part-*`**. Making them lazy would take ~290KB more off the critical path, but
it removes the safety net at exactly the moment it exists for, so it wants its
own change and its own test rather than a ride on this one.


## The world travels now: farm → ant territory → ant empire (2026-09-05)

The run is one continuous place with regions pinned to DISTANCE, not a stack of
maps. `ZONES` in index.html; `tools/gen_ants.py` makes the art,
`tools/cut_ant_bg.py` and `tools/cut_ant_props.py` and `tools/cut_ants.py` cut
it. Look at any metre with `?dist=N`.

**This is not the old travelling system coming back.** That one changed leg
every 26 SECONDS and CROSSFADED the screen, and it was deleted for good reason:
the world dissolved around a stationary-looking bird on a timer, which is a
scene change, not a journey. What is different:

- **The boundary is a place, not a moment.** Zones are pinned to metres, so the
  farm ends at a spot on the map and 1100m is the same dusk in every run.
- **The seam is a vertical line that scrolls past you.** Farm slides off the
  left, empire slides in from the right, and for a while the screen genuinely
  holds both.
- **The seam is hidden behind something solid** — the root-and-earth formation
  with the tunnel mouth stands exactly on it, so the join is behind an object
  you are looking at and running into.

### I built the far/mid layers as a cross-fade first and it was wrong

The reasoning was that the seam is only ~22m of screen — about one second at
20 m/s — so distance should change by haze instead. It produced a **double
exposure**: the empire hung over the farm as a ghost, both worlds at half alpha
in the SAME pixels. And "left is farm, middle is the entrance, right is the
empire" is a spatial arrangement that no amount of alpha can produce.

**Two keyed layers at partial alpha are a ghost, never a horizon.** Every slot
uses the spatial seam now. What gives the change its time is not the seam, it is
the approach: fifteen mounds growing over 500m, the light dimming, the livestock
thinning out, and the formation visible from far off with the lit city already
showing through its mouth.

### The light is on a different schedule from the scenery, deliberately

The layers cut; the palette cannot, because a sky that changes between two
frames is the cheapest-looking thing a game can do. But a plain long crossfade
turns the sky black while a sunlit farm still fills the screen. So it is
**asymmetric and hung off the boundary**: 0 → 0.45 over the 300m approach (it
gets gloomy near the hole), then 0.45 → 1 over 80m past it (it is night inside).
`LIGHT_PRE` / `LIGHT_POST` / `LIGHT_AT_MOUTH`.

### The open top is the one rule that overrides the reference art

Every reference for this world is a tunnel with a heavy solid ceiling filling
the upper third. Nugget flies to the top of the screen, so a roof drawn across
it forbids the exact space the whole control scheme is about. The layer prompts
carry an explicit CRITICAL clause demanding the top third stay empty, and there
is a **fourth layer slot, `hang`**, anchored to the TOP of the screen instead of
the ground: roots and lanterns that drop INTO frame with air between them.
Things that dangle say "there is a ceiling somewhere" while leaving it flyable.
One tall tile could not do both halves — sized so the bank sits right the roots
float in the middle, sized so the roots reach the top the bank is enormous —
which is why `cut_ant_bg.py` splits the source on the empty band between them.

### Things that were quietly still the farm

Each of these is a small lie that adds up to "this is a brown filter over the
farm", and each needed its own fix:

- **`T.sunR || 1` made a sunR of ZERO mean ONE**, so the underground zones —
  which set it to 0 precisely to have no sun — drew a full-size disc. A
  falsy-guard on a number whose meaningful value is 0 is always this bug.
- **`C.road` is applied once from the STARTING theme**, so the largest flat area
  on screen stayed farm-tan in a mine. `drawGround` reads `themeNow()` now.
- Clouds, the sun and the meadow grass all multiply by `outdoor()` rather than
  testing a boolean, so none of them can pop off between two frames.
- The livestock and the farmer thin out over the last 380m and are gone before
  the mouth (`farmness()`), rather than vanishing.

### The ants

Background life only: never in `game.obstacles`, no collision. `ANT_H` is 52
world units against Nugget's ~190, which is the scale joke — a sugar cube is
cargo. Placed by world position so they do not pop, spaced wide because a column
of ants is a wall and readability wins. The guard flips to his startled frame
when Nugget is within 420 units: no state machine, no alert cone, just "is the
chicken close", and it lands every time.

**The walk sheet cut into 2 blobs instead of 6** because the generator draws a
ground rule under each row and it TOUCHES ALL OF THEM — same family as the
truck's dark-pixel labelling. `parts_no_rule()` erases any horizontal dark run
spanning >55% of the sheet first; no ant is 60% of the width. The baseline is
not lost, it is exactly where the erased rows were, and that is what grounds the
frames.

**The signboards are generated BLANK and lettered in code.** A generator cannot
spell reliably at sign size, one blank board is every sign, and drawn text stays
sharp at any scale.

### Not built yet

*(Superseded the same day -- deep empire and the lab are built; see the next
section. Kept because "the pattern is already there" turned out to be the
accurate part: the second and third worlds cost one prompt group and one
cutter argument each.)*

## Deep empire and the secret lab (2026-09-05, later)

The progression is complete: farm → ant territory → ant empire → deep ant
empire → secret ant lab. `?zone=farm|terr|empire|deep|lab` jumps to any of
them; `?dist=N` is still the finer control.

### The deep zone is not a new place, and that is the point

The environmental question is *"why do the ants have this?"*, and it only gets
asked if the answer arrives late. So the deep city is the SAME earth city with
technology growing through it — pipes bolted onto chambers you have already run
past, hazard boxes and warning lamps screwed into dirt walls, riveted plates set
into the soil, and the warm lanterns replaced by caged electric bulbs. If it read
as a different world nobody would wonder how it got there.

The lab IS a different world, which is why it gets the only hard visual break in
the game: dark blue metal, cold cyan light, green glass. It still obeys the open
top — ducts, cable bundles, strip lamps and a security camera hang down into
frame, never a sealed ceiling — because the controls do not change just because
the set does.

### Two doorways, one mechanism

`GATEWAYS` replaced the single hardcoded gate. Each entry names a zone boundary
and the art standing on it, so the layer seam always cuts behind something the
player is running into. The lab door is drawn at **2.35x, deliberately past the
screen edges**: the sprite carries its own rectangle of earth around it, and at
a modest size you can see that rectangle's edges sitting on the scene. Scaled
until the edges leave the frame, the doorway simply *is* the view at the moment
of crossing — which is the same trick the seam itself relies on.

### Per-slot fallback, and why a world declares its slots

`slotFor(zone, key)` walks back through the zones behind a world for any slot it
does not have. Per-slot rather than per-set, because a world in progress usually
has its floor and its middle distance before it has its haze and its ceiling, and
borrowing only the missing pieces keeps it coherent instead of showing bare sky.

The other half of that: **a world lists only the slots it OWNS**, because a
listed slot is a file REQUESTED. The deep city has no haze of its own — it is
the same cavern as the empire, seen from the same distance — so it does not ask
for one, and does not 404 on every load. That was a real 404 (nine of them)
caught by the verify pass, not a hypothetical.

### The bug the seam had been hiding

`drawField()` paints the farm's daylit meadow band. It was gated on the seam
only, which worked while a seam was on screen — and past the mouth there is no
seam, so `same` was true and it drew at full strength: **a bright green stripe
across the middle of an ant city**. Gated on `outdoor()` now, which is the thing
that actually means "there is a sky here". A guard that only holds during the
transition is not a guard.

### The generator's failure mode at volume

33 renders queued back to back came back roughly half failed — *"I can search
for images, but can't create any right now"*, and one *"not signed in"*. It was
**not quota** (4% of the daily window, checked). It is capacity, and it lands on
whatever is at the end of the queue: the `staff` group finished with **zero**
renders and had to be re-run on its own, after which it worked first time.

So: **ask for 3 takes, queue big groups separately, and check what actually
arrived rather than that the job exited 0.** `cut_*.py --list` is the check —
it counts renders per prompt, and a zero there is the failure this produces.

### `split_row` had to stop looking for empty

The first version wanted a run of near-EMPTY rows to split the hanging half off
the standing half. That was fine for the ant layer and useless the moment the art
got busy: the deep layer has root tips and cable loops dangling into the same
band the earth bank occupies, so there is no empty row anywhere and the whole
frame came back as one tile — which the near slot then squashes to a quarter of
its height. It looks for the QUIETEST row now, over a smoothed window. There is
always a quietest row, which is the point: a picture of things hanging above a
floor always has a waist, even when something crosses it.

### Reaching it

Zone starts are 0 / 560 / 1180 / 2100 / 3000 metres. At the speed curve that is
around two and a half minutes of clean flying to reach the lab, which is a long
way — the flags exist because nobody should have to earn it to look at it.


## The flight lost its bed, and kept its glide (2026-09-06)

User asked twice. The first time I measured the roof contact firing 35 times a
second and fixed that -- a real bug, but not what they meant. What they meant
was everything that makes a noise *while airborne*, and measured over ten
seconds of ordinary hold-and-release flying that was:

    glide  x12     the wings-out rustle, on a 0.42s cooldown
    + the wind bed, continuous, the whole run

**Only the bed went.** It was one looping noise source through a bandpass with
its level and cutoff pushed from airspeed every frame, and it was written up
here as "the thing that made flying sound like flying" -- which is exactly why
it had to go. Holding is not an occasional action in this game, it is the entire
input, so a layer that rises whenever you do the thing the game is about is a
sound you cannot stop hearing.

**I removed the glide with it and that was one thing too many; user asked for it
back and they were right.** The distinction the first pass missed is the one
that matters: the bed is a LAYER -- always on, rising with speed, no way to stop
hearing it -- and the glide is an EVENT on a 0.42s cooldown that only fires
while he is actually falling. One scores the whole run; the other punctuates a
drop. Taking both left nothing at all in the middle of a flight.

So the air now holds the glide, between `takeoff` leaving the ground, `ceiling`
once on arrival at the roof, and `land`/`scuff` coming down. The wingbeat has
been silent since 2026-09-05.

At peak **0.012** the glide is the quietest thing in the game -- about a third
of a footstep -- because it was mixed to sit UNDER the bed. With the bed gone
there is nothing masking it, so it reads more clearly than it did before rather
than less; worth knowing if it ever needs raising.

**Kept as no-op stubs, not deleted** -- and that decision paid for itself
within the hour. `windStart`/`windSet` still exist and do nothing, because they
are called from the run loop, the menu and the intro, and a half-removed audio
node with live callers is how you get a silent failure inside a try/catch.
Restoring the glide was putting its body back and changing no call site, which
is exactly what the stubs were for.

**Proved, not assumed.** Counting calls cannot show silence -- a no-op stub is
still called, and the first probe cheerfully reported `glide x12` after it had
been silenced. `tools/sfx.py` renders every entry in `S` offline and reports its
peak, and that is the check: it read **glide 0.000** while silenced and
**0.012** with it back, everything else unchanged (takeoff 0.105, land 0.174). Two things in that tool also had to go,
because they asked for a sound that no longer makes one: `wind` was in its
inventory (it threw `S[name] is not a function`) and under its flight montage.
The montage is now takeoff / roof / takeoff / land, which is worth keeping
precisely because it is mostly silence -- a flight with nothing in the middle
only works if its edges are crisp.

There was also a dead line waiting to throw: the offline renderer saved and
restored the wind's audio nodes around each render, and its restore still read
`keep.w.src` after `keep.w` stopped existing.

## The truck has its own music (2026-09-06)

Taking the vehicle already cuts the farm's power and fills the road with
barriers; the one thing it did not do was sound different. `musicScene('ride')`
is a fourth scene, and `musicFor()` returns it whenever `riding()` -- so every
route into the truck gets it, which is the bug that scene-follows-mode exists
to prevent.

**The riff REPLACES the chase rather than layering over it.** Two pieces of
music at once is mud, and the point of the ride is that everything else got out
of the way. It fades in at 4.5/s against the menu's 2.2 -- the riff should
arrive with the truck, not catch up a second later -- and restarts from zero
each time so it lands on the downbeat.

`preload='none'`: 245KB that most runs never reach, wanted a second and a half
after a pickup rather than instantly.

**Generated, with the reference used the way the art references are.** The user
named a specific commercial track (Godsmack, "Cryin' Like a Bitch") as the
feel. The prompt asks for the QUALITIES -- down-tuned palm-muted chug, ~100 BPM,
swaggering rather than dark -- and names no artist and no song. The point is
that the truck sounds enormous, not that it sounds like somebody else's record.

`tools/cut_ride_music.py` cuts it. **The generator returned 175 SECONDS**, not
the ~30 the studio used to give, so the tool takes a 32s slice -- a ride lasts
until you are hit, often ten or twenty seconds, and three minutes would be a
megabyte nobody hears the end of. It trims leading and trailing silence FIRST
(the menu track shipped with ~100ms of silence at the front and audibly
breathed once every loop) and then **measures the seam**: head RMS 6393, tail
5068, ratio 0.79, which is well inside healthy. Do not trust that "cut on a
musical length" implies gapless -- measure it.

`?dbg` now publishes `musicFor`, `musicScene` and `music()`. The tracks read
null until a real gesture starts the AudioContext, which is correct rather than
broken, so the scene LOGIC is what the probe checks.

### Still open

The three pickup stings (mystery egg, truck collect, truck jump) are generated
but NOT cut or wired -- and only two of three exist, because Gemini's audio
capacity failures land on whatever is last in the queue. They also need a
sample-playback path the game does not have: every other sound in `S` is
synthesised WebAudio, which is why the game has no audio assets and why every
sound starts on the exact frame it is asked for. Worth deciding between
finishing the sample path and synthesising the three, rather than defaulting.

## How a sound gets made (2026-09-06) -- THE RULE

> **SUPERSEDED.** See **The sound is the user's own recordings now**. Kept as
> an accurate record of what was tried and why, not as the current rule: the
> truck, the footsteps and the gate are recordings the user supplies, and
> generation is stopped.

**Every sound in this game is SYNTHESISED in WebAudio, in `S`.** A few
oscillators and a noise burst per entry. That is why the game is one HTML file
with no audio assets, why every sound starts on the exact frame it is asked
for, and why retuning one is changing a number.

This was tested against the alternative rather than assumed. Three pickup
stings were generated through Gemini Studio first, on request, and it is the
wrong tool for the job:

- the studio returns a TRACK (30s when this was written up, 175s the last time
  it ran), and a game wants a gesture;
- a gesture cut out of a track is a fragment of somebody's music, arriving a
  frame late through a decoder;
- and it costs a fetch, a decode and a buffer that the synth version does not.

Two of the three stings did not even generate -- Gemini's audio capacity
failures land on whatever is last in the queue.

**MUSIC IS THE EXCEPTION, and the line is exactly this:** if it is a piece of
music that loops, generate it (`audio/music_*`, `tools/gen_sfx.py music`); if
it is a thing that happens, synthesise it. The truck's metal riff is generated
and right to be. `megg`, `truckget` and `truckjump` are synthesised and right
to be.

Levels are checked, not guessed: `tools/sfx.py` renders every entry in `S`
offline and prints its peak. megg 0.182, truckget 0.142, truckjump 0.222.

### VROOM: one engine, two moments

`vroom(len, f0, f1, vol, at)` is a primitive next to tone/wob/noise, and BOTH
truck sounds are it -- arriving is long and low (58->205Hz over 0.9s, with a
second blip on top), jumping is the same voice short and high (118->355Hz over
0.4s). That is the point: the player hears the truck arrive once and then hears
the same engine on every press, so a jump is the truck doing something rather
than a new noise.

**The wobble IS the engine.** A clean pitch sweep is a synth rising; firing
cylinders are anything but clean, and the lumpiness is what makes it a motor.
Four layers, each doing one job: the rev (sawtooth climbing, chugging hard),
the size (the same an octave down, so it has a chest), the exhaust (broadband
roar opening as the revs climb), and a short crack at the front so it STARTS
rather than fades in.

### The three, and what shape each is

- **megg** -- a reward, so it goes UP: four notes of a major pentatonic
  climbing over a bell that rings past them. Pentatonic on purpose -- the egg
  streak already walks that ladder, so it lands as the same world, and there is
  no interval in it that can clash with the music underneath.
- **truckget** -- heavy first, bright second: a dead clunk, an engine catching
  and rising on a `wob` (a clean sweep sounds like a synth; an engine is
  lumpy), then a brass stab so it reads as good news rather than a breakage.
- **truckjump** -- deliberately a cousin of `takeoff()` rather than a new idea:
  the same rising shape an octave down with twice the weight, so a player who
  knows the chicken's hop hears the truck's as the same verb done by something
  enormous.

## I deleted the truck by tightening one guard (2026-09-06)

Reported as "wheres the monster truck skill, you removed it!" and it was exactly
that: **zero pickups in three minutes of play.**

The ask was "don't put an obstacle in front of the mystery egg". I made
`dropClearAt` demand nothing between the PLAYER and the egg. But the egg is
placed more than a screen ahead -- `lead` is `(VW - PX + 260)/speed + 0.3` --
and there is essentially always something in that span, so all forty placement
attempts failed on every attempt and `spawnBasketDrop` returned false forever.
The ability did not break; it stopped existing.

The window that matters is **the approach**, not the screen: `DROP_RUNUP` (1.15s
of road immediately before the egg) is enough to line up and commit. Anything
further back is just the game, and dodging it on the way to a reward is the
good part.

### The real lesson is what the tests did not ask

`?ridetest` passed cleanly on the broken build. Every check in it tests the
truck once you are IN it -- jump windows, spacing, the grid going down -- and
not one asked whether you can GET the thing they are testing. A feature that
cannot be reached is not a feature.

There is a check for it now, and it is **mutation-tested**, which is the only
reason it is worth having: with the bug restored it reads

    TRUCK: 1 PROBLEMS
    UNREACHABLE  the pickup can be placed: 0/40 spots clear -- THE TRUCK WILL NEVER APPEAR

and with the fix, 40/40. Generally: **when a guard is tightened, ask what it now
refuses that it used to allow, and count.** A clearance rule with no upper bound
on how much it clears will eventually clear everything.

## The content census: what ships but never appears (2026-09-06)

After the truck went missing, the question was "what else is like this". The
answer needs a census, not spot checks -- so: instrument `drawImage` and `S`,
play a long run through every zone, and list what is loaded but never drawn and
what is defined but never spawned.

**Three false alarms first, all the harness's fault, and each worth knowing:**

- Driving the player by TELEPORTING him onto eggs means he never flies, never
  jumps and never gets hit, so a third of the character's frames looked dead.
- `?auto=1&demo=1` fixes that but the demo pilot **dies every few seconds**, so
  `dist` and `runT` reset and nothing gated on distance -- crows, the pickup,
  tiers 1-4 -- ever gets a chance. Only tier-0 obstacles appeared.
- Making it immortal by calling `startRun()` on each death then reset `dropT`,
  which suppressed the pickup all over again.

**If a census says half the game is dead, suspect the census.** The real
conditions have to be STAGED: the intro playing out, a death, a jump in the
truck, an NPC passed close.

### What is actually true

- **All 18 obstacles are reachable** -- 12 on foot at the top tier (`e_hang3`
  and `zap_m` need tier 4), 6 in the truck. `?obtest` asserts this now, by
  walking PAT and RIDE_PAT and resolving the `#tokens`, and it is
  mutation-tested: an obstacle in no pattern reports `UNREACHABLE`.
- Crows, eggs, the pickup, every character state, the truck's launch frame and
  all six flames, the NPC panic cycles and the score-card hens all draw when
  their condition happens.

### Two things that ship and are never seen

- **`cos-shades.webp` and `cos-scarf.webp`** -- ~92KB loaded every session, and
  `equip()` is called from exactly one place: the `?wear=` debug flag. The
  cosmetic SYSTEM is complete (slots, pivots, draw order) and nothing in the
  game ever puts anything in a slot. This is a design gap, not a bug: there is
  no way to earn or choose them, which is the same hole as eggs buying nothing.
- **`spyalert` and the farmer's rage** -- gated off by `NPC_REACT = false`,
  which is DELIBERATE and documented right there: background NPCs should be a
  continuous band of movement, not a series of encounters. The frame sets are
  still loaded and sliced. Turning the switch on is one word; the download is
  paid either way.

## The vroom fired every time and could not be heard (2026-09-06)

Reported as "wheres the VROOM sound". It was firing perfectly: **40 presses
from the ground, 40 `truckjump` calls**, and the pickup fires `megg` +
`powerdown` + `truckget`. It is also the LOUDEST sound in the game --
truckjump 0.26, truckget 0.23, against hit at 0.25.

**It was masked, and by something I put there myself.** The engine is a low
sawtooth revving from 58Hz, and the ride's metal riff is a down-tuned
palm-muted guitar -- the same octave -- and I had them start on the SAME FRAME
with the music at 0.60 against a peak of 0.24. That measures as working and
plays as missing, which is the worst kind of bug to chase.

Three fixes, in order of how much they are worth:

1. **The riff waits.** `RIDE_MUSIC_WAIT` (0.85s) holds the music down after
   the pickup so the engine lands in clear air. Clunk, VROOM, *then* the music
   -- which is how every good power-up in the genre is staged and costs one
   number.
2. **The music sidechains to the engine.** `game.rideDuck` dips the riff to 30%
   for 0.25s on every truck jump. Making the vroom louder or brighter is
   guesswork against a moving target -- whether one masks the other depends on
   the bar -- and getting out of the way for the length of the hit is the
   answer the whole industry already reached. The fade rate had to go from
   4.5/s to 11/s, because a 4.5/s ramp cannot complete a 0.25s duck.
3. **The rev speaks in the upper mids too**, where the guitars are not: a
   harmonic an octave and a fifth up, and the exhaust rasp pushed out of the
   mud. The weight stays underneath; the part that CUTS is the top.

### And a real bug the probe surfaced on the way

The two timers were written INSIDE `if(RIDE_TRACK)`. That track's own error
handler sets it to `null` when it fails to load -- so on any device that could
not fetch the riff, `rideMusicT` would never reach zero, and `musicScene('ride')`
reads that forever as "the engine is still landing, keep the riff down". **A
missing audio file would have silently disabled the ride music permanently, on
exactly the devices that could not load it.** Game state does not belong behind
an asset check.

## Sounds are GENERATED again, and the riff that never played (2026-09-06)

> **SUPERSEDED for the sounds** -- see **The sound is the user's own
> recordings now**. The riff half is still true and still load-bearing.

**The rule reversed, at the user's instruction:** "all sounds i ask you about
should be gemini studio generated, even the kick of the cage and the Boom".
The earlier "synthesise them" note is superseded. `tools/gen_sfx.py` makes
them, `tools/cut_sfx.py` cuts them, and the game plays them as samples through
`A.sfxGain`.

### The riff was never playing, twice over

First: `RIDE_TRACK.play()` sat inside `if(rideWanted > 0)`, and the 0.85s engine
hold sets rideWanted to 0 on the ONE frame `musicScene` runs -- and musicScene
only runs when the scene CHANGES. play() was never reached. The delay I added
to make the engine audible had removed the music entirely.

Then, having fixed that: the hold takes the volume to zero, and the
pause-when-silent line then PAUSED the element, with nothing left to start it
again. It played for a frame and stopped. **A fade that can reach zero and a
"pause when silent" rule are a trap together**; trackTick now restarts the
track whenever it should be audible and is not, and only pauses once the scene
has actually left the truck.

### Why the synthesised vroom never sounded like an engine

It was built out of `wob`, which bends an oscillator's PITCH -- and a wavering
pitch is a siren or a swanee whistle, never a motor. **An engine is a pulse
train: what rises when it revs is the RATE OF THE BANGS.** The synth version
was rebuilt to gate amplitude at the firing rate (a saw through a wave shaper
opening a gain), which measured correctly -- 5 bangs/sec rising to 11 -- and it
is now only the fallback, because the user asked for the real thing.

### Getting audio out of the studio at all

- **"MUSIC STING" is the phrasing.** "sound effect" returns a written Foley
  recipe; even "audio sting" got routed to chat on 9 of 26 attempts.
- **Capacity failures take whatever is LAST in the queue**, so these are asked
  for one at a time (`vroom-only`, `kick-only`, `boom-only` groups exist for
  exactly that).
- **The gesture is not at the front of the track.** The studio returns ~60s
  with the sound somewhere inside -- truckjump's was at 15.08s. `cut_sfx.py`
  finds the loudest point and walks BACKWARDS to where it starts, because the
  first onset is usually a false start the model wandered through.

### `SMP_HAVE` is a list on purpose

A generated sound arrives when it arrives, and half of them fail. The game must
not request a file that has not been made: that is a 404 on every load. The
available set is declared, `loadSample` refuses anything outside it, and each
entry in `S` falls back to its synth version until the sample lands. One line
to edit when a new one arrives.

**Landed so far: megg, truckjump. Still failing: vroom, kick, boom.**

## Three things that were still the farm (2026-09-06)

All three are the same shape as the ones already written up under **Things that
were quietly still the farm**: a value read ONCE PER RUN in a world that changes
with DISTANCE. That family is not finished -- when you add anything that picks a
colour, a flag or a position at the top of a run, ask what it says at 3000m.

### The canvas was cleared to the farm's blue, underground

`render()` cleared to `C.skyA`, and `C` is stamped by `applyTheme()` from the
theme the run STARTED in. Below ground that is a bright daylight blue behind
everything the sky surface does not cover -- and it covers from y=0 down, while
`game.camY` lifts to **+90** as he climbs. So a band the height of the camera
lift is bare canvas, and it is not a corner case: it is what the top of the
screen looks like every time you fly high.

Measured at 2170m with camY 82, the top row read `0D64CB`. It reads `0E0A15`
now, which is the deep zone's own `skyA` under the vignette. One word:
`themeNow().skyA`.

### `?dist` and `?zone` moved the odometer and left the world behind

**The two flags built to look at the map were the only things that could never
show you a boundary.** `startRun` set `game.dist` from the preset and then
`player.x = 0; cam.x = -PX`. Everything that reads DISTANCE jumped -- the zone,
the palette, the layer set -- and everything placed by WORLD POSITION stayed at
metre zero: the gateways, the signs, the mounds, and `drawBgLayers`'s own seam,
all of which are drawn at `m*UPM - cam.x`. Measured: `?dist=2000` gave
`dist 2005.7m` against `cam.x -4.3m`.

That is why the empire's root formation and the lab door had never been seen
except by playing to them. `?dist=1120` now runs you into the tunnel mouth with
the farm still on the left of the screen.

**The escape had to be dealt with, and the interesting part is which way.** The
handover at `T_OUT` does `player.x = cageExitX()`, and the whole escape is
measured from world zero -- the cage parked at `-CAGE_RUNOUT`, `camIntroX`
framing that spot. So it put the last pose at world 0 with the odometer 2000m
away, restoring the bug one line after the fix. Moving the CAGE to the preset
was the other option and it is the worse one: those positions are a mix of world
and screen space (`breakCage` and the feather burst both take `game.cageX`
through `cam.x`), and anchoring the scene 70,000 units out multiplies every one
of those by the distance. So a preset run is a RETRY -- `startIntro` hands
straight to `startQuick` when `game.presetDist` is set. You cannot be kicked out
of a barn 2000 metres from the barn, and "start me there" never meant "release
me there". A plain run still opens with the escape; `?dist=0` and `?zone=farm`
still do too, because the guard is on a truthy preset.

### The sky birds flew through the ant lab

Clouds and the sun multiply by `outdoor()`; the three bird silhouettes did not,
so they glided through a sealed city at farm strength. Multiplied, not gated,
for the same reason as the rest: a bird that pops out of existence between two
frames is worse than one that should not be there.


## The shell around the game (2026-09-06)

The front door: a strip, three doors, a daily card, a four-tab shop and a
loading screen re-laid onto the menu's own skeleton. The brief was "Vehicles
(skills), power ups, Appearance, remove ads for 1.99$, a reward section that
lets you watch an ad each 24h, and a section that lets you see how much golden
eggs you have on the top left and top somewhere your best score".

**NOTHING HERE TRANSACTS.** No egg is spent, no purchase is made, no ad is
played, and every price and level in it is placeholder copy. It is the layout
and the states, built so the shape could be judged before the economy is
written against it. The two things that ARE real are the two numbers: the egg
count and the best distance come straight out of the same state the run uses,
so the strip is never a lie about what you have.

| What | Marker |
|---|---|
| The whole shell | `THE META SHELL` (once in the CSS, once in the script) |
| Open / close / which tab | `const META = {`, `META.open` |
| The strip's numbers, and first-run | `function metaSync` |
| The ladder | `const DAILY`, `function dailyDraw` |
| Every listener | `function metaBind` |
| The shop markup | `<div id="shop"`, `data-pane=` |
| The loading screen | `#boot`, `.bootCol`, `body.booting` |

### PLAY did not move, and that is the whole constraint

Five destinations went onto a menu that had one button. Everything added is
either smaller than PLAY, outlined instead of filled, or in a corner PLAY does
not occupy. Three rules hold it:

- **Filled gold is reserved.** Only PLAY and the daily claim are filled. Every
  other new control is an outline, *including both of the ones that sell
  things*, so nothing out-shouts the button the player came for.
- **Gold means currency, cream means score.** The egg count is gold; BEST is
  cream AND a different shape (a plate hanging off the top edge, not a pill), so
  a glance can never read one as the other. Coral is real money and nothing
  else.
- **The eggs do not move.** They sit in the corner `#hudTL` already puts them in
  during a run, so the number stays put when the game starts.

There is a fourth, about where a thumb is. This game is landscape, so the
bottom-right corner is the dominant thumb -- PLAY and the three doors -- and the
bottom-left is the other one, which is where the daily card went. The top strip
is status, and almost none of it is tappable.

### The two rule chips and the hint are first-run only, and that is the trade

`.rules` and `.hint` used to sit under PLAY on every visit. They are the exact
room the three doors needed, and a returning player has already been told how to
fly. `body:not(.firstrun)` hides them.

**And on the first run the shell is not drawn AT ALL** -- no doors, no daily
card, no egg pill, no BEST plate, no remove-ads. Nothing has been earned,
nothing can be bought, nothing is customisable, and no ad has been seen, so
selling ad removal to someone who has not seen one reads as grabbing. Day one is
the menu this game already had, byte for byte, which is the point: adding a shop
must not cost anything before the player's first run. `game.firstRun` is
**re-read from `dgh.played` inside `metaSync`** rather than cached, because that
key is written the first time you die and the menu you come back to is the
second-visit one.

### The loading screen IS the menu, unlit

Same logo, same tagline, same seat. The bar is PLAY's box, in PLAY's place, in
PLAY's gold -- `.big, .bootBar` share one `min-width` so they cannot drift apart
whatever the label says -- and it fills, and then it is the button. The
crossfade between the two screens does the morph for free.

`boot()` calls `toMenu()` and starts the frame loop **before** `gateStart()`, so
the farm is already being drawn under the loading screen. Dropping the backdrop
from opaque to a wash lets it arrive behind the screen that is waiting for it,
and the handover becomes a sunrise rather than a cut to a different picture.

**That is also where the one real bug was.** A translucent `#boot` shows the
canvas -- and `#menu`, which is a DOM sibling under it. Two logos, two taglines,
a ghost PLAY and a ghost daily card. No z-index can be transparent to the canvas
and opaque to a sibling, so `body.booting` simply does not draw the menu
(`#menu` and `#hud` go `visibility:hidden`), and the class is removed at the
**start** of the half-second fade -- so the menu is revealed underneath a
dissolving loading screen, which is the morph rather than a workaround for it.

The number is drawn twice, cream underneath and ink inside the fill, and the
fill is **the whole button clipped from the right** (`clip-path`) rather than a
bar that grows -- that is what makes the ink copy land exactly on the cream one,
so the figure is legible at every percentage instead of going pale the moment
the gold reaches it. `?noboot=1` still skips everything, and the stall-based
give-up logic is untouched.

### The press filter is the thing that would have broken it

`onBtn` only ever let `#mute` swallow a press; every other tap flies, on
purpose, so PLAY and RETRY start the run *and* flap. Drop a shop onto that and
tapping VEHICLES launches the chicken.

Both `onBtn` and `touchDown` now also pass `#mute,[data-meta]`, and
`data-meta` is on the strip, the doors, the daily card, the whole shop and the
ladder. `touchDown` needed its own arm because it decides `preventDefault`
before `downFrom` ever runs -- swallowing the default on a meta element kills
the click that follows. And **`thrustOn` returns early on `META.open`**, which
is the part no amount of pointer filtering would have covered: without it, Space
starts a run from inside the shop.

### `.big` is taken, and so are `.card`, `.stat` and `.rule`

Everything inside the shop is `s-` prefixed for that reason. One element slipped
through: day seven's rung was `.dday.big`, which picked up the PLAY button's
8px gold under-shadow and drew an orange bar under the last day of the ladder.
It is `.dday.last` now. **Check a new class name against the game-over card and
the menu chips before using it.**

### The daily ladder, and the four decisions inside it

Seven rungs, and the seventh is not eggs -- a ladder is sold by its end, so the
reason to come back on day four has to be visible on day one. `DAILY` holds the
state and `dailyDraw()` renders both halves of it: the claim, and the clock.

- **A locked button with no clock reads as broken, so the clock IS the button.**
  Nothing else on the card moves between the two states.
- **Nothing resets on a missed day.** Resetting the streak punishes exactly the
  lapsed player you are trying to win back. The ladder waits.
- **24 hours from the claim, not from local midnight.** Midnight rollover
  invites clock-changing and punishes a late player for being twenty minutes
  early.
- **Watch-then-claim, as asked.** The higher-converting variant is claim-free
  with a double-it-for-an-ad button; that is a test, not a guess, and it belongs
  with the economy.

### `tools/cut_hats.py` is the one cut script that does not read the archive

There is no Gemini sheet behind the four hats. They were generated as opaque
reference *renders* -- a whole chicken wearing the hat, on flat green, 512x280
RGB -- and `chickens.html` shows them as picture cards, keying the green in the
browser. So the shipped file IS the source, and the script reads `art/`.

The shop needs a hat-shaped icon 54px across instead, and a whole chicken at
that size is a beige smudge, so each render is keyed, its largest blob taken and
the top **44%** cropped. 44% was measured, not guessed: below it the beak goes,
above it the wing comes in. Output is `art/shop/hat_*.webp`, lossless, at 3x the
drawn size.

**Every image in the shop is a CSS background, not an `<img>`.** Two reasons,
both load-bearing: the gate counts `HTMLImageElement.prototype.src`, so a
background does not inflate `LOAD.total` away from the game's own requests; and
a background on a `display:none` pane is not fetched until the pane is shown, so
the whole shop costs the boot path nothing. The three door icons are the
exception and are visible on the menu -- and two of the three (`truck_drive`,
`mystery_egg`) are art the game loads anyway.

### What is not wired

Buying, equipping, the ad, the clock, the economy. `?ridetest`-style proof does
not exist for any of it because there is nothing yet to prove. The build order
that does exist is in the launch plan: currency, then missions, then the shop,
then characters and skills -- anything else writes the economy twice.

### The verification that mattered

`sh check.sh` first, always. Then: one clean load counting requests, 404s and
`window.__errs` (225 / 0 / null); `?selftest ?obtest ?crowtest ?ridetest` all
passing; a run, the ride, the crows and the 2200m zone with no exceptions; the
portrait gate still gating. **Then the same pass against the live URL with a
cache-buster**, which is the one that caught the real problem -- see below.

### The concurrency hazard, in a new and worse shape

The other session **committed and pushed the entire meta shell inside their own
commit** (`6868e3a`, "The truck's five moments") while it sat in the working
tree -- *without* the four `art/shop/hat_*.webp` files it references, because
those were untracked and `git add index.html` does not notice what index.html
asks for. The live site served a shop pointing at four 404s, and **nothing said
so, because a missing image here is a silent fallback by design.** It was caught
by diffing HEAD's file list, not by looking at the screen. `fb62062` fixed it.

So, on top of everything already written under **Two sessions edit this at
once**: after any edit here, check whether HEAD *already contains it* before
assuming your work is uncommitted -- and check that every asset your commit
references is tracked, because the game is built to hide exactly that failure.

### The shell transacts now (2026-09-06, later)

Eggs are spent, levels are owned, the perks reach into the run, a revive is
offered at the death beat and the daily reward runs off a real clock. Search
`THE ECONOMY`.

**The two things that are not real are the two that cannot be.** There is no ad
network and no billing on a static page, so `rewardedAd()` and `iapBuy()` are
the seams: each shows the shape of the pause it makes, says on screen that it
is a placeholder, and resolves. Wiring AdMob and Play Billing later is those
two functions and nothing else in this file. Everything they gate --
the revive, the daily claim, the egg bundles, remove-ads -- is written and
tested against them.

**`game.eggBank` stays the one live counter**, persisted to `dgh_eggs` exactly
as the pickup code always did; `SAVE` (`dgh.save.v1`) holds levels, skins, the
daily clock and the no-ads flag. Two stores rather than one on purpose: the run
writes eggs on a hot path forty times a minute and should not be serialising a
JSON blob to do it. SAVE is merged rather than replaced on load, so a save
written before a perk existed still opens with that perk at zero.

**Every pane is drawn from `SHOP`.** A price, a level and an owned state cannot
be written into static markup and still be true after the first purchase, so
the markup for the four panes is four empty divs and `shopDraw()` fills them.
Adding an item is a row in the catalogue; adding a control is a `data-` name,
because the whole shell runs off one delegated click listener.

### `cost[n]` is the price to reach level n+1, and that bit me

The trolley is the one thing you already own -- it starts at level 1 -- so
every price was read one slot along: the first upgrade billed at the second
upgrade's price, and the top level was unreachable because the array ran out
before the levels did. **It was completely self-consistent on screen**: the
button said 1,800, it charged 1,800, the level went up, the pips filled. Only
counting the eggs against the catalogue caught it. That is why the test asserts
the *amount*, not that something was spent.

### What each perk actually reaches

Everything the run reads comes out of `PERK`, four lines from the shop copy
that describes it, so an effect and its promise cannot drift apart.

| perk | where it lands |
|---|---|
| EGG MAGNET | `updateEggs` -- eggs lean in and accelerate; a snap would read as the counter ticking by itself |
| HEAD START | `game.presetDist`, the same rail as `?dist` |
| LUCKY EGG + trolley level | `PERK.dropRate()` multiplies both mystery-egg timers |
| NERVES OF STEEL | the multiplier on `nearMiss`'s bonus |
| SOFT LANDING | `softSave()`, called first thing in `die()` |
| SECOND WIND | `reviveOffer()`, called first thing in `finish()` |
| trolley level 3+ | `loseRide` absorbs one hit before the basket pops |

**A refusal has to say why.** Not enough eggs dims the button, keeps the price
visible and toasts `NOT ENOUGH EGGS`; it does not hide the item. "You need more
eggs" is the single most useful thing a shop can say.

### The revive, and the two places it had to be wired

`finish()` now does one thing before anything else: offers. Everything below it
writes the best score and flips `dgh.played`, and **a run that is about to carry
on has not ended** -- so the original body is `finishNow()`, and decline or
time out and it runs exactly as it always did.

Two things had to be handled that are not obvious:

- **A tap during the offer restarted the run.** Once `game.mode` is `'dead'`,
  any press is a retry, so impatience threw the offer away and started a new
  run. The offer raises `META.open`, which is already the flag `thrustOn`
  rejects on.
- **Reviving into the piece that killed you is not a revive.** Everything in
  flight is cleared and he is replaced at `game.dist` -- the one position the
  world and the odometer agree on, since the fix that made them advance
  together -- with the 3-2-1 back on and 2.4s of invulnerability that BLINKS,
  because a free hit nobody can see is a bug.

### Appearance is a recolour, because the chicken is painted

`drawChickenFrames` draws one image per frame and never touches the cosmetic
slot rig: the snapback and the shades are IN THE ART. So hats were never going
to show up in play, and a look is a recolour of all 36 frames instead.

**The two regions were measured, not guessed.** Clustering the opaque pixels of
`anim/*.webp` by HSV: the cap is hue 150-205 above 0.28 saturation and is ~5% of
the bird; the body is hue 20-70 between 0.05 and 0.42 saturation above 0.60
value, and is ~43%. Everything else -- the black outline, the orange beak, the
red comb, the white shoes -- is left alone, and that is what keeps every look
recognisably the same character rather than a palette swap.

- **A swapped image, not a canvas filter.** A filter would run per draw, and
  `hue-rotate` cannot tell the cap from the beak.
- **Built a few frames per animation tick**, because two million pixels in one
  task is a visible hitch on a phone. The partial map is safe to draw from:
  `drawChickenFrames` falls back to the original for any frame not rebuilt yet,
  so a look that is still building shows the default bird rather than nothing.
- **One frame is recoloured per card**, so the shelf cannot disagree with the
  bird.
- **A skin card is a `<div>`.** It contains a buy button, and a button inside a
  button is invalid -- the parser closes the outer one, so every price escaped
  its card and stood up as a gold bar between them. It looked like a CSS bug and
  was a markup one.

`SPECTRE` is gated on `game.best >= 3000` before it can be bought at all, which
is the one place the shop reads the run rather than the other way round.

### The slot that was deliberately not for sale, and now is (2026-09-09)

`CROP DUSTER` used to sit here with `dev:true`, rendering as IN DEVELOPMENT --
a placeholder for "the flying one", on the principle that a button taking
12,000 eggs for a vehicle that does not exist is worse than a button that does
nothing. **The `FRIED EGG UFO` is that vehicle, built, and it has replaced the
placeholder.** See *The fried egg UFO* below. Both vehicles now start OWNED
(`SAVE.veh = {trolley:1, ufo:1}`, merged so old saves get it), because what is
sold on this tab is what a vehicle DOES when the run hands it to you, never
whether it is handed to you.

### The death beat, and the score card that follows it (2026-09-06, later)

The score card used to arrive the instant the ragdoll settled. A timed card
comes first now and asks the only question a dead run has left: **carry on, or
finish bigger?** Search `THE DEATH BEAT`.

- **EXTRA LIFE for eggs** (`HEART_COST`, 400) and **EXTRA LIFE for an ad** both
  continue the run. Both land in `reviveNow()`; the only difference is what was
  paid.
- **DYNAMITE** ends it instead -- Jetpack Joyride's final blast, +500/750/1000 m
  from `TNT`, multiplied by `PERK.bang()`.
- **Each of the three is offered once a run and no more.** That is what stops
  the beat becoming a wallet with a retry button attached, and it is why they
  are three booleans on `game` reset in `startRun` rather than anything cleverer.
- Eight seconds on the clock. Decline or let it run out and `finishNow()` runs
  exactly as `finish()` always did.

**The two halves are mutually exclusive at any one death** -- reviving means the
run is not over, and the dynamite only means anything once it is -- so they are
side by side on one card rather than two screens in a row.

`SECOND WIND` is gone from the shop and `BIGGER BANG` replaces it. A paid revive
was selling what this screen now hands out for an ad; the replacement sells the
other half of the screen.

### The blast is solved, not thrown

`updateBlast` drives the distance along an ease-out. The ragdoll's own physics
would have been the obvious way and it is the wrong one: **a body launched a
thousand metres by a spring lands somewhere different at every frame rate**, and
the whole point of the beat is that you bought a specific number of metres and
got them. The arc is `sin(t*PI)`, so the landing and the last metre happen
together.

`game.dist` and `cam.x` advance together -- the same agreement the odometer fix
established -- so the world genuinely scrolls, and **a long enough blast carries
you across a zone boundary**. A 1,000 m stick from the farm lands you in the ant
empire, which was not designed and is the best thing about it.

### `deathDraw` destroyed the element it needed next time

It wrote `'USED'` into the `.cost` node with `textContent`, and the price span
lived *inside* that node -- so one spent life removed `#dthHeartCost`, and the
next death threw on a null **before the card was ever shown**. One revive
silently took the whole offer away for the rest of the session, and the run
carried on looking normal. The node is rebuilt now, never half-edited.

**Generally: never write text into a node that contains an element you look up
later.** The failure is invisible at the moment it happens and surfaces
somewhere unrelated.

`S.doorbreak` was also gone by the time the blast called it -- the sound rework
removed `doorbreak`, `cagebreak` and `megg`. Nothing else still calls them, but
check `S` before reaching for a sound you remember.

### The score card is laid out for a landscape window now

It was a portrait card in a letterbox: a column of centred rows with the number
in the middle and a lot of air either side. The number owns the left, the run
owns the right in a 2x2, the buttons are one row so RETRY sits under the thumb,
and there is a SHOP door on it -- the death screen is the highest-intent moment
a player has.

It gained the eggs collected, and a DYNAMITE row **that only appears when
dynamite was used**. A permanent `+0m` teaches the player the feature exists and
does nothing, which is worse than not mentioning it.

## The sound is the user's own recordings now (2026-09-06/07)

**This supersedes "How a sound gets made -- THE RULE" and "Sounds are GENERATED
again" above.** Both are kept because they are an accurate record of what was
tried, not because they still describe the game. The order went: synthesised ->
generated in Gemini Studio -> and now, for everything the truck and the chicken
do, RECORDINGS THE USER SUPPLIES. Generation is stopped; they said so directly.

What ships as a sample, and where it came from:

| sample | source | plays |
|---|---|---|
| `truckget` | `engine-ignition.wav` | the pickup AND every jump |
| `truckidle` | `engine-idle-loop.wav`, cut from 0:06 | loops the whole ride |
| `truckland` | `truck-land-14.wav` | the truck touching down |
| `step` | `step-4.wav`, trimmed to 0.24s | loops while running on the ground |
| `gatebreach` | `gate-breach-42.wav`, trimmed to 5s | the kick in the intro |

`SMP_HAVE` is still the one line to edit when a file arrives or leaves: a name
in it means the file exists, a name missing means the synth carries it and the
game never asks for a 404.

### What was DELETED, and do not put it back

- the mystery-egg chime, the cage break, `cagerattle`
- every generated truck sound (`vroom`, the old `truckjump`, `boom`, `megg`)
- the riff's sidechain duck on jumps
- the per-footfall `S.step()` in the run cycle

Each was removed on request, and each had a reason worth keeping: the egg chime
was announcing an announcement (`startRide()` is on the next line and brings an
engine and a riff with it); the duck was making room for an engine that had
since been made quiet three times; the footfall trigger would double every step
now that the loop covers it. `S.step` survives ONLY as an impact, for the corn
and the cage.

### Set levels against the game, never by ear

Two rounds of "quieter" by feel failed. Then `tools/sfx.py` rendered the whole
table and the answer was not subtle: the truck was **more than twice the level
of `hit`**, the cue that tells the player they are dead. A recording is far
denser than the oscillators it replaced and it went in at their headroom, which
made it the loudest thing in the game rather than the biggest thing in it.

Where it sits now, and the shape to keep:

```
hit  0.24   <- the ceiling; nothing routine should pass it
truckland 0.22   truckget 0.26   gatebreach 0.30   land 0.19
truckjump 0.045  <- deliberately tiny: see below
```

`truckjump` looks wrong as a number and is right as a sound. It is LAYERED over
the driving bed, so its peak is not what you hear, and the user asked for it at
the bed's level and then below it. Worth knowing why "the same as driving" was
not enough: **equal rms is not equal loudness when one sound is a steady bed and
the other is a transient.** A bed is a floor the ear stops hearing; an event at
the floor's own energy still stands well above it.

### The three measuring tools, and what each is for

- `tools/sfx.py` -- renders every entry in `S` offline through the REAL
  functions and prints peaks. This is the level table. It now warms the samples
  before rendering, because it used to render the first sound that wanted one
  with its synth fallback and every later one with the real file, which showed
  the ignition at twice its shipping level and got acted on.
- `tools/pick_sfx.py` -- scores windows of a generated take against a spectral
  profile. Only useful while generating, which has stopped, but it is also the
  record of three ways a cutter can lie: `-ss` before `-i` silently landing on
  silence, `dynaudnorm` reshaping the balance being scored, and a 30ms lead
  moving a clip from 32/29/29 to 47/18/26 all by itself.
- `tools/opt_audio_sfx.py` -- **run this when any sound is added.** It encodes
  each candidate bitrate, decodes it, compares to the SOURCE across eleven
  bands, and takes the smallest file under 0.5dB. Everything had gone in near
  the encoder defaults: 129kbps for mono engine recordings that are 96% below
  400Hz. It saved 33%. It has FLOORS, and they matter -- band energy is what a
  codec works hardest to preserve, so left alone the script passed a 36-second
  stereo music track at 24kbps. Music is floored to what the soundtrack already
  ships at; a loop is floored like music, because an artefact you hear once is
  a texture and one you hear every second is a fault.

**Re-check levels after any re-encode.** It moves the very peaks every gain was
set against. Last time: peaks within 4%, rms within 1%.

### When the user gives a reference, MEASURE it

Three monster-truck clips turned "it sounds lame" into numbers no amount of
tweaking would have found: a big engine heard from outside has ~0% of its
energy below 100Hz, its fundamental is nearly absent, and **its fifth harmonic
is the loudest thing in it**. The game had the exact inverse -- a 37Hz sub under
a lowpass, which is a distant lorry. Nothing from a reference ever ships; only
the numbers do.

That rebuilt `vroom` as a `createPeriodicWave` from the measured series (`ENG_H`)
with everything under 110Hz filtered off, tuned to D because an FFT of the ride
track puts its strongest partial at 74Hz. It matched the references to two
decimal places -- **and it is now only a fallback**, because the user supplied a
real engine the same day. Leave it: a fallback has to match the level of the
thing it stands in for, or the one player whose fetch fails gets an ignition
nobody else does.

### The two beds: engine and footsteps

Both are ONE long-lived voice built when the state starts and torn down when it
ends -- never a per-frame one-shot, which allocates an oscillator per frame and
is the classic way to stutter a game on its own audio.

- **`ENG`** loops `truckidle` while riding, revving up when the wheels leave the
  ground. It can UPGRADE MID-RIDE: it used to choose its source once, so a ride
  that started before the file decoded ran on the synth for its whole length
  with the recording sitting in memory. Adding a third sample to fetch was
  enough to make that happen.
- **`STEPB`** loops `step` while on the ground, and this one is not free-running.
  An engine idles at its own rate and nothing contradicts it; a footstep that
  does not land when the foot lands is wrong twice a stride. Its playback rate
  comes from the animation's own numbers -- `STEP_LEN*2*game.speed/strideLen` --
  so the clip is stretched to exactly one step per half phase-cycle, which is
  where the run cycle puts a foot down. Measured in the running game: the legs
  want 4.31 steps a second and the loop delivers 4.31. It fades in 60ms, not the
  engine's 300ms, because leaving the ground has to be crisp.

### Fetching does not need a gesture; decoding does

The kick is **1.15s after the press that creates the AudioContext**, so the
biggest sound in the opening was racing a fetch and a decode it could lose --
and losing it meant silence, permanently, because nothing asked again. So the
BYTES are pulled during the loading screen (`prefetchSamples`, fired when the
art gate drains so it never competes with the images the gate is waiting for)
and the decode runs from memory on the first touch. Measured: all five in
memory before any tap, decoded 74ms after it, breach fires at 1169ms against a
kick at 1150 with its buffer ready. `S.gatebreach` also retries for 0.2s if the
buffer is somehow still missing, then gives up -- past that the door is long
open and a bang is a mystery rather than a door.

## The barn intro was skipped on every desktop play (2026-09-07)

`bindDown` attached BOTH `pointerdown` and `mousedown`, and a browser fires both
for one click. So a single press arrived TWICE, and the two presses were not
harmless -- they were read as two taps. On the menu that is: press one starts
the intro, press two lands in the intro's own handler, which exists to let an
impatient player skip ahead to the kick.

**The door, the run-up and the boot going in were gone in a frame, on every
mouse play of this game, for as long as that binding existed.** Nobody noticed
because a phone binds only `touchstart` and was always fine.

Measured before the fix: one press, `downFrom` called twice, `introT` at 1.441
within 400ms with the kick due at 1.15. After: one press, one `downFrom`, intro
intact.

Two guards, because there were two duplications:

- one pointer source, `pointerdown` where `PointerEvent` exists and `mousedown`
  only as a fallback for a browser that somehow lacks it;
- `if(e === game.lastDownEv) return;` in `downFrom`, because `bindDown` is
  called for the window AND the canvas, both in the capture phase, so one press
  walks past two listeners holding the same event object. Comparing the object
  is exact -- no timing window to tune, and a real double-tap is two objects and
  still gets through.

**This is the shape to look for elsewhere.** It was found only because a
user-supplied sound "would not play": it fired 48ms after the press, before it
could possibly be decoded, and reading that as "the sample loads too slowly"
would have been the wrong fix to the wrong problem. `game.rawDown` counts calls
and is the fastest way to check it has not come back.

### Still unreproduced

The user reports the gate breach going silent after a reload. Three reloads in
one profile, warm cache, clicking as fast as the harness can, and with the REAL
autoplay policy rather than the permissive flag the harness had been hiding
behind: it fired every time, context running, buffer ready, and the live site
serves the file and the current `index.html`. The retry above is insurance
against the mechanism, not a fix for a diagnosed fault. If it recurs, the
question that splits it is whether the OTHER samples go quiet at the same time
-- all of them means the audio context, only the gate means the timing race.

### Both paid offers are priced off the run they are ending

A flat 250 bought the same thousand metres whether you died at 200 or at 2,000,
and that is the wrong way round twice over. **At the top of a good run those
metres are the ones you actually want** -- they are the ones between you and a
best -- and at the bottom of a bad one they were the cheapest score in the game.

`TNT[i].cost` is the FLOOR now. `tntMul()` is `1 + reached/1000`, capped at
`TNT_CAP` (4), and `tntCost(i)` rounds the product to ten.

| died at | +500 | +750 | +1,000 |
|---|---|---|---|
| 0 m | 250 | 450 | 700 |
| 500 m | 380 | 680 | 1,050 |
| 1,000 m | 500 | 900 | 1,400 |
| 2,000 m | 750 | 1,350 | 2,100 |
| 3,000 m+ | 1,000 | 1,800 | 2,800 |

Three properties, each load-bearing:

- **Never cheaper than it was.** The multiplier floors at 1, so scaling the
  price cannot accidentally turn a short run into a bargain -- which is the
  failure mode of every "price it off the run" scheme that scales in both
  directions.
- **Capped.** Without `TNT_CAP` a 6,000 m run prices the top tier past anything
  a player could have banked, and an offer nobody can take is the same as no
  offer, except it looks like the game taunting you.
- **Rounded to ten**, so the button reads as a price rather than as a
  calculation. 1,347 is arithmetic; 1,350 is a price.

**The multiplier goes on the label** -- `ONE LAST BANG x3.0`. A price that moves
between runs and does not say why reads as the shop being unreliable.

**`deathTnt` charges `tntCost(i)`, the same function the button was drawn
from.** The trolley already taught that lesson the hard way: a price computed
twice is a price that comes apart, and it stays self-consistent on screen the
whole time it is wrong. The test asserts the exact amount taken against the
exact string rendered, for the same reason.

The floor row of that table is unreachable, incidentally -- `deathOffer` needs
100 m before it shows anything, so the cheapest real price is x1.1.

### And so is the extra life -- on the same curve, deliberately

`tntMul` is **`runMul`** now, and `heartCost()` goes through it too.

| died at | extra life |
|---|---|
| 0 m | 400 (the floor, unreachable -- the card needs 100 m) |
| 500 m | 600 |
| 1,000 m | 800 |
| 2,000 m | 1,200 |
| 3,000 m+ | 1,600 |

**One curve, not two.** The dynamite scaled and the life did not, which left the
card teaching two different rules in the eight seconds it is up -- and the
second one would never have been worked out. The reasoning is the same and if
anything stronger for the life: continuing a 2,000 m run is worth far more than
continuing a 200 m one, because the metres you are protecting are the ones
between you and a best.

**The ad stays free at every distance.** Only the paid option tracks what it is
buying, so the free one never gets worse -- which is the whole reason there are
two of them on the card.

Both column captions carry the multiplier now rather than just the dynamite's,
because both columns hold a price that moved. And the hard-coded `400` that used
to sit in the markup is gone: `deathDraw` rebuilds that whole node anyway, so a
price baked into the HTML was one more thing that could quietly stop being true.


## The run is nine worlds now, and the background travels (2026-09-08)

Farm 0-500, Ant Territory 500-1000, Ant Empire 1000-1500, Prison 1500-2000,
Chernobyl 2000-2500, Secret Military Base 2500-3000, Area 51 3000-3500, Alien
Facility 3500-4000, Space 4000+. Every zone is 500m, which is 25-40 seconds at
this speed curve: long enough to read as a place, short enough that the next
one is always coming.

### A slot can be a SEQUENCE, and that is what fixed the treadmill

The middle distance was one painting tiled forever -- the same barn, silo and
windmill every 75 metres of travel, for as long as you survived. The odometer
climbed and the view did not.

**The mid slot walks a list now.** Panel n is chosen by the tile's own index in
layer space, so it is a property of WHERE YOU ARE: the same metre is the same
field on every run, and the set only repeats after the whole list has gone by.
Every panel is the same pixel size, which is what lets one `g.W` place all of
them and what makes their ground lines meet.

**Panels are keyed by ZONE, not by layer set.** Several zones share a set while
their art is being made -- the prison and the reactor both ran on the deep
city's layers -- so keying by set would have made them the same place.

**The approach is ORDERED and DITHERED; everything else cycles.** Out on the
farm there is no story in which field comes next. The approach to the mouth is
the opposite, so a tile there takes a transition panel with a probability equal
to how far through the approach it stands (smoothstepped, hashed off the tile
index, never Math.random -- the same metre must look the same twice). Early on
the mounds are the odd field among farms; by the mouth there is no farm left.

### CUT-OUT PROPS WERE TRIED FIRST AND ARE THE WRONG KIND OF ART

The first answer to "make every 100m different" was set-pieces on flat green,
placed by metre and drawn at camera parallax over everything. They did not fit,
and the reason is structural rather than taste: a prop at parallax 1.0 crosses
in FRONT of a fence moving at 0.60, at full saturation, at a size set by the
road rather than the horizon. The eye reads that as a sticker on a photograph.
**A middle distance is made of middle distance.** The art and the two tools were
deleted; this paragraph is what is left of them, and it is the useful part.

The same fault, already in the game, is why the ANT MOUNDS were removed from
the lane: fifteen anthills at camera parallax standing on the ground line is a
hazard silhouette, and it was reported as exactly that. The build-up they
existed for moved into the transition panels, where a mound is a landmark.

### What a panel must be, and what a tile must be

Two different jobs, two cutters, and confusing them is how the seams show:

| | panel (`mid`) | tile (`near`, `hang`) |
|---|---|---|
| placed | beside OTHER panels | against ITSELF, forever |
| edges | empty margins, nothing touching | left and right must MATCH |
| cutter | `cut_mid_panels.py` | `cut_layers.py` |
| anchored | bottom edge, on the ground line | `near` bottom, `hang` TOP |

`cut_layers.py` searches for the loop seam the way `bg_layers.py` always has:
score columns near the right edge against columns near the left and crop
between them. The generator will not give you a loop however politely it is
asked.

**A floor tile is scaled BY ITS HEIGHT, so height is resolution.** The prompt
asked for a strip "about one quarter of the image height" and got exactly that:
a 33px band that the game then magnified twelvefold. The clause asks for the
bottom HALF now, the cutter refuses anything under 140px, and a flat floor gets
something tall put in it (the prison's floor got a low wall along the back)
because there is nothing tall in "concrete".

### Things the generator does that cost a round each

- **A row of one subject comes back as three copies of it.** `tr3` was asked for
  "a barn half-buried by a mound" plus the row clause and drew that motif three
  times. Transition panels ask for ONE CONTINUOUS SCENE, each thing exactly once.
- **It draws the ground line literally**, as a solid dark bar across the width.
  In the game that bar is the edge of a rectangle, and the panel reads as a
  cut-out pasted on -- which is what "this house in the background is cutout"
  was. The bar is dark BROWN, not black, and the transition panels spatter soil
  BELOW it, so the test is relative (a full-width row under 55% of the panel's
  own median brightness) and cuts from there down.
- **It stacks two rows** when the subject is a yard of things. Refused by
  measuring the alpha profile for horizontal bands -- but a 20px sparkle in a
  corner is not a row, so bands are told apart by how much WIDTH they span.
- **Some words return text instead of a picture.** "Prison yard", "razor wire",
  "radiation trefoils" all did. No image ever arrives, the tool sees a timeout,
  and it looks exactly like a broken studio. Same silhouette, different
  vocabulary, and both rendered first time.

### The rule about blue is now absolute and measured

Blue is the hazard. `tools/warm_flowers.py` enumerates every background file
(42 panels plus the older sets) and reports anything in the wire's HUE --
165-265 degrees at real saturation, which is the right test; a channel test
flags the hills and the grass. It found bluebells in the farm grass, cyan
mushrooms underground, cyan lighting across the whole lab set, and 359 stray
pixels in four of the new panels. The background is at **zero** now.

### Lossy is right for a panel and wrong for a sprite

`to_webp.py` says lossless, and it is right about sprites: flat cel fill, hard
ink outline, alpha edge, drawn at about the size they were cut. A background
panel is upscaled 2.7x on the way to the screen, so the question is not whether
q84 differs from lossless but whether it differs AFTER the scaler.

Starting from to_webp's own numbers (0.63-1.59 RMSE) rejected every quality and
saved nothing. Measured at draw size these panels are 2-6, so the worst one was
rendered beside its lossless original and looked at: indistinguishable. **65
files, 6.29MB -> 2.31MB.** `tools/opt_panels.py`, and nothing is lost by being
wrong -- the lossless cut is reproducible from the archived render.

### Rendering 40 pictures through a shared studio

`tools/render_panels.py`, and every rule in it was paid for:

- **One at a time, tab closed after each** -- working or failed. The failure
  rate climbs with the tab count.
- **A timeout is retried once; a sign-out stops everything.** Only the user can
  clear "you might be signed out"; a timeout is weather.
- **One panel failing twice is SKIPPED and named**, three in a row stops the
  run. Stopping the whole batch on one bad prompt cost several restarts.
- **THE LIBRARY IS THE SOURCE OF TRUTH, NOT THE JOB STATUS.** `c4` was declared
  failed four times while its picture sat in the library the whole while.
  Always finish by running the cutters over everything.
- **The studio gets restarted under you**, and a run that dies on a connection
  reset leaves sixteen panels unrendered and a stack trace instead of a report.


### The blast is a scene now: it lands, it burns, then it throws him

Buying dynamite used to be a flash and a number going up. Three beats, and the
second and a half before the bang is what turns a purchase into an event.

| phase | for | what happens |
|---|---|---|
| `drop` | 0.42s | a bundle is lobbed in from off the left and lands beside him |
| `fuse` | 0.58s | it sits there, ticking faster and faster, the shake building |
| `fly` | 2.30s | BOOM, and he goes down the road |

**It lands on his LEFT**, because he faces right and it has to throw him right.
The bundle is the tier you bought -- one stick, two or three -- so the thing on
the ground is the thing on the button.

**He bounces rather than arcing.** `HOPS` is four decaying parabolas and each
one announces its own landing with dust, a thud and a shake. One long parabola
is a cannonball, and a cannonball is somebody else's game. `hopY` walks the
hops rather than solving them, because a closed form would give the height
without ever telling us a bounce had happened.

`pickFrame` hands him the **hit** set while he flies -- launched, tumbling,
tumbling, face down -- because without it he leaves the explosion in a running
pose, on the grounds that he is technically on the ground.

### Three things the filmstrip found that reasoning had not

Reasoning got the beats right and every one of these wrong. They were all
invisible in the code and obvious the moment twelve frames were laid side by
side.

- **The boom clock lives inside `updateIntro`**, which does not run in a blast.
  `boomT` sat at zero and the fireball drew its first frame, forever. The blast
  ticks its own now.
- **A damped camera cannot follow this.** He covers a thousand metres in 2.3s --
  **twenty-six thousand world units a second** -- and a damp at rate 9 settles
  about three thousand units behind it, so the entire animation played a screen
  and a half off the right edge. `rag.x` and `player.x` advance by the same
  delta every frame, so the camera is *pinned* to him and the FRAMING is what
  eases, 0.52 to 0.34 over the first third of a second. Cutting straight to the
  flight framing threw him a fifth of a screen sideways on the frame of the
  explosion, which reads as a jump rather than a launch.
- **A fireball anchored where the charge went off is correct and invisible.** At
  that scroll speed it is off the left edge eighty milliseconds in and nobody
  ever sees the thing they paid for. It hangs just behind him instead and lasts
  its full half second, which reads as the blast still throwing him -- which is
  what it is.

**Generally: anything that is not attached to the player is off-screen almost
immediately during a blast.** Distance-per-second here is two orders of
magnitude above a normal run, and every instinct about camera work is wrong at
that speed.

### The icons, and the two scripts that make them

`tools/gen_icons.py` -> `tools/cut_icons.py` -> `art/shop/{tnt1,tnt2,tnt3,heart}.webp`.

The card is a decision made in eight seconds, and eight seconds is decided on
silhouettes -- so the three tiers are one stick, two and three rather than three
identical text buttons, and the escalation is the picture. The tiers lost the
word METRES because the picture already says it.

- **Three separate prompts, not one strip of three.** A strip is what the flame
  wanted, because every cell there is the same object at a different moment;
  here the cells are the escalation, and asking one image for "1, then 2, then 3
  of the same thing" is the sheet-of-props failure exactly. Three prompts cost
  three times the quota and come back cuttable.
- **The mystery egg is the attachment.** It is the closest thing the game has to
  an ICON already -- one shiny object drawn to read small -- so it anchors the
  style better than a piece of scenery.
- **The choosing is in `cut_icons.py`, by name**, so the pick is recorded rather
  than remembered, with a note on what each rejected take got wrong. One `tnt3`
  take came back blue and gold on a starfield, in somebody else's game
  entirely, which is why three takes are asked for.
- **Largest blob only.** Gemini leaves a small sparkle mark low-right on these
  and the biggest-component rule drops it without anybody having to notice.
- The bundles are **lazily loaded with a drawn fallback**, so they cost the
  loading gate nothing and a missing one still reads as dynamite.

The ad button keeps its triangle. A triangle is already the clearest thing a
play button can be, and a painted one would only be bigger.

## The fried egg UFO -- the second vehicle (2026-09-09)

The mystery egg now contains one of two things. The trolley is the ground half
of Jetpack Joyride's contract; this is the flying half, and it is the vehicle
the `CROP DUSTER` slot was holding open.

**It came out of the Studio from two attachments** (`tools/gen_ufo.py`), and
which is which is *stated in the prompt* -- with one reference "in the EXACT
style of the attached picture" is unambiguous and with two it is not:
`art/truck_drive.webp` for the game's style AND the pilot (same bird, same teal
cap, same shades), and the user's own fried-egg saucer render for the design,
with an explicit *redraw this, do not match its shading* because the reference
is a soft 3D render. Three takes; the best came back as three saucers at three
sizes in a staggered layout rather than the row that was asked for, which is
the usual outcome and why nothing slices by column.

**It ships as ONE picture**, `art/ufo.webp`, 142 KB. That is the wheel's
decision again: a saucer's lean has a rule (it leans with its vertical speed)
and its underlight has a rule (it burns with the button), so both are solved in
code. Three baked tilts would be three times the bytes, wrong at every angle
between them, and -- the part that matters -- a baked flare cannot answer a
press on the frame it happened, which is the only frame the player is looking
at. `tools/cut_ufo.py` takes the largest blob off the sheet and **measures the
three lamps**, printing their centres and radii as fractions of the finished
picture straight into the shape `UFO_LAMPS` wants. `--check` draws them back
onto the sprite, because every anchor in this project that was estimated by eye
was wrong.

### What is actually different about flying it

- **Same movement model, three constants.** `UFO_G 0.42`, `UFO_D 1.00`,
  `UFO_T 0.50`. Drag is the BIRD'S on purpose: the ease is not what makes this
  feel different, the SPEEDS are. Terminal is about ±750/1100 against his
  ±1780/1920, so it crosses the band in about 0.6s up and 0.9s down while
  answering the button in a fifth of a second. It goes where it is pointed and
  stops there; he darts and overshoots.
- **The trolley's thrust multiplier is now ZERO rather than a condition.** The
  term used to read `p.thrusting && !riding()`, which would have needed a third
  clause the moment a vehicle wanted to be held. It is a number in the same
  place the other two constants are.
- **`riding()` vs `onWheels()` vs `inUfo()`.** `game.ride` still answers "is he
  in something" and everything true of any vehicle still reads it, unchanged.
  `game.veh` says which. Making it `game.ride = 1|2` instead would have left
  every truck-specific `riding()` silently firing for the saucer.
- **THE GRID STAYS LIVE.** `wireHot` asks `onWheels()`. The blackout is the
  trolley's whole moment and is spent once; and a flying vehicle with nothing
  electric left to dodge is the game with the game taken out.
- **`UFO_PAT` is the flying roster, not a new one** -- the opposite decision to
  `RIDE_PAT` and right for the same reason. Every piece the bird meets, the
  saucer can answer; what it cannot answer is the bird's SPACING, because it is
  246 units wide against his 96 and sits in a column two and a half times as
  long. So the tokens are identical and the numbers are not: tails ~20% longer,
  gaps inside a pattern 1.35-1.55s against his 0.85-1.15, and `CLEAR_UFO` 380.
  No corn -- a saucer stopped by a maize plant is the trolley's joke with
  nobody laughing.
- **`clearNow()`.** `rollZap` read the bare `CLEAR` for as long as only one
  thing flew; the trolley never meets a zapper so nothing noticed. Both it and
  the hang clamp ask the vehicle now.
- **Vertically it is EASIER than the bird** -- 117 tall against his 142 -- and
  its ceiling is its belly, with half the dome allowed over the top edge. The
  first version kept the whole craft inside the play area, which cost 200 units
  off a band the hazards are still laid across the full height of. His own rail
  is his FEET, with a hundred units of him already above it.
- **It never lands.** Its floor is `UFO_LOW` 30, so the whole touchdown branch
  is unreachable while it is up: no `onGround`, no run cycle to fall back into.

### The beam is the reward

`eggAim()` replaced four numbers written into the collection test (the bird's
chest at +74, a 46x62 grab box, the magnet's radius and pull). The saucer's
reward is that it does not pick eggs up, it hoovers them: a radius wider than
the craft, at more than twice the pull. The magnet perk still stacks by
`Math.max`, because a player who paid for reach should never watch it shrink
when they take a vehicle.

The three shafts are drawn, for the same reason the exhaust is, and they
**stop at the road** -- `len` is capped at the distance from the lamp to the
ground, so the beam pools on the dirt as he comes down instead of punching
through it. At the hover floor the craft is 30 units up, so any fixed length
punched through. Motes climb the beam off `game.t` and an index: no particle
allocated, culled or carried, and it is what sells suction rather than torch.

**No abduction.** It was designed and dropped: `NPC_REACT` is `false`, every
background reaction is deliberately switched off, and the run is nine worlds
now rather than a farm. Adding a livestock reaction would have been fighting an
explicit decision to get a joke that only lands in world one.

### The rest

- **`pickVeh()` ALTERNATES rather than rolls.** A run that finds two eggs
  should show both vehicles, and a fair coin gives the same one twice a quarter
  of the time. Which one the run opens with is the coin flip.
- **The egg still does not say which.** That is why the pickup is a mystery egg
  rather than a picture of the reward, and it is worth twice as much now.
- **The free hit moved to the pickup.** `game.rideTough` was set once per run
  from the trolley's level, which with two vehicles spends the saucer's charge
  on the trolley and leaves a second pickup with nothing. `vehTough()` is asked
  when a vehicle arrives.
- **`S.ufoget()` is a theremin** -- one continuous rise with nothing struck in
  it, against the trolley's three beats of weight. There is no recording behind
  it, so the synth IS the sound rather than a fallback. Level set with
  `tools/sfx.py`: **0.243**, against `truckget` 0.296 and `hit` 0.216. Never by
  ear.
- **`?ufo=1`** starts a run already in it. `?ride=1` still gives the trolley.
- **`?ridetest` reports 6 TIGHT roadblocks with a 0px window, and it did so at
  `109ded3` too** -- verified by serving `git show HEAD:index.html` side by
  side. It is not from this work, and it is the next thing worth chasing.

### `rag.y` is a SCREEN coordinate, not a height

This is the one to remember. `rag.build` stores `y - CK.standH` off a `y` that
is already `GROUND - player.y`, so **rag.y counts DOWN from the top of the
canvas**: small means high, large means lying on the road.

`rag.y = hopY(t)` therefore inverted the entire flight. He skimmed along the top
of the screen, every bounce "landed" in mid-air, and the dust went up off a road
he never came near. It survived three separate filmstrips because the dust looked
like landings and he looked like he was arcing -- **it was only obvious once the
numbers were printed next to the pictures.** It is `ragGround() - hopY(t)` now.

**And `ragGround()` is a function, not a constant.** `GROUND` is recomputed by
`resize()`, so `const RAG_GROUND = GROUND - CK.standH` captured a canvas that had
no size yet: it came out at -80 and threw him clean off the top of the screen.
Anything derived from `GROUND`, `VW`, `VH` or `SCALE` at module scope is derived
from nothing.

### Weight in the bounces

Every landing announces itself three ways, and before this it announced itself
none: he passed through the road at the right heights and nothing about him
noticed.

- **Squash.** `game.blastSquash` is set to 1 by the landing and eased out over a
  sixth of a second, driving `rag.pose.sx/sy` -- wide and flat at the bottom, a
  touch stretched while it recovers. It is reset before `finishNow()`, because a
  squashed pose handed to the score card stays squashed.
- **Spin DECAYS, it is not scheduled.** It used to be a fixed rate scaled by
  progress through the flight, which spins him identically whether or not he has
  touched anything. `rag.vrot` loses 56% per contact and decays continuously, so
  the last two hops read as a body sliding to a stop rather than a wheel that
  happens to be slowing down.
- **Dust lies down.** `dustSheet()` throws a low wide sheet backwards; the round
  puff `smoke()` makes is right for an impact and wrong for a landing, and using
  it for both was why the bounces read as polite.

### The explosion has its own fire now

`tools/gen_boom.py` -> `tools/cut_boom.py` -> `art/fx/blast0..5.webp`.

It was borrowing the CAGE's explosion -- five frames cut for a barn door being
kicked out, scaled three times up -- which reads as a yellow star and is over in
half a second, a fifth of the flight it is supposed to have caused. The six new
frames are white-hot core, burst, fireball with debris, then three of smoke, so
**the fire ends as smoke instead of simply stopping**.

- **"EXACTLY 6 SEPARATE PICTURES IN A ROW"** is the wording that gets a cuttable
  cycle out of this model, the same as the exhaust flame. The other two takes
  came back as two rows of five, which `col_split` cannot read -- and that is
  the whole reason three takes get asked for.
- **Registration here is the easy case**: an explosion is radially symmetric, so
  each frame's own bounding box IS the blast centre. Every frame is pasted into
  a square the size of the biggest, so all six draw at one scale off one anchor.
  (Compare the crow, where the bbox is mostly wing and had to be thrown away for
  the beak tip.)
- **The art already grows** -- frame three is the biggest -- so the code adds
  only a slow drift outward. Doubling up on growth balloons it and then snaps it
  back on the frame the smoke starts.

**Lazy loading has to be lazy EARLIER than the moment of use.** Asked for on the
frame the charge goes off, the fireball spent its first three hundred
milliseconds waiting for a decode -- most of a 0.78s cycle -- so the explosion
the player had just paid for did not appear at all. `warmBlastArt()` runs when
the death card opens: seconds of warning, and still nothing on the boot path the
loading gate counts.

### Two more particles, and a trail that comes off him

- **`ring()`** -- a shockwave is the fastest thing on screen and half of what
  sells an explosion. Stroke width falls with radius so it does not read as a
  bubble, and it is squashed vertically so it sits IN the world. Two of them a
  beat apart: one reads as a graphic, two read as pressure, because the second
  is still arriving while the first has gone.
- **`dustSheet()`** -- described above.
- **The trail hangs off his body**, not off the ground. It was seeded at ground
  level whatever height he was at, so a body forty feet up left smoke round its
  ankles. It is also denser: one particle every twenty-five milliseconds is a
  dotted line, not a trail.
- **A smoke column stays where it happened.** Everything else in this scene
  leaves at twenty-six thousand units a second, so without something anchored
  the road behind is spotless one frame after the biggest event in the run.

## POWER and CONTROL: the two vehicles pulled apart (2026-09-09, later)

The brief, in the user's words: *"Your Monster Truck Basket and Egg UFO should
feel almost like two completely different mini-games... Basket = POWER and UFO
= CONTROL. That distinction is exactly what will make people have favorite
vehicles."* Everything below is that, and each vehicle was given a weakness on
purpose, because otherwise the saucer is simply a better Nugget.

### The trolley: heavy, and it commits

- **`RIDE_G` 0.27 -> 0.46.** Nearly twice the pull, and the whole arc now takes
  **1.11s where it took 1.49** (`?ridetest`). 0.27 was chosen when the arc had
  to cover a 392-wide hay wagon at the slowest speed in the game and hang time
  was the only lever; with smashables back the arc does not have to be long, it
  has to be POWERFUL.
- **The apex did not move, and that is the whole payoff of having SOLVED for
  the impulse.** `rideImpulse` bisects for the launch speed that reaches
  `RIDE_TOP` under whatever gravity it is handed, so raising the pull raised
  the launch to match and bought a snappier arc at the same height for free.
  A typed-in impulse would have made this a tuning session.
- **TAP OR HOLD** (`RIDE_CUT`, `RIDE_TAP`) -- one line in `thrustOff`, not a
  second jump. Releasing while still climbing cuts the remaining upward speed,
  with a floor under it. Measured through the real input path:
  **tap 346, half-hold 593, hold 593.** And per piece (`?ridetest`):

  | piece | top | hold window | tap window |
  |---|---|---|---|
  | r_trough | 126 | 420px | 150px |
  | r_tyres | 164 | 390px | 150px |
  | r_drums | 176 | 570px | 210px |
  | r_wagon | 230 | 450px | 60px |
  | r_bales | 238 | 360px | **0px** |
  | r_crates | 250 | 360px | 30px |

  That split is the design: low things can be tapped, waist-high and up need
  the hold. `RIDE_TAP` was 0.55 first and measured **tap:0px on all six** -- a
  tap that clears nothing is not a short jump, it is a wasted press, and "the
  button did not register" is exactly what a player would report.
- **THE SUSPENSION IS A SPRING, not a pose** (`RIDE_SQ_K/C`, `game.tSquash`).
  Free, resting at zero, moved only by impulses: the landing kicks it *down*
  scaled by impact, the launch kicks it *up* because weight coming off a spring
  extends it, and a smash gives it a jolt. So a hard landing wobbles hard and
  rolling off a tap barely shows, without anything deciding what "compressed"
  means. `drawTruck` now scales the rig about **the contact line** -- squash it
  about its centre and the wheels sink into the road on every landing.
- **The rattle, the wheelie and the spit.** Two sines of a couple of pixels
  while it is on the ground (a trolley at speed is not a still picture
  sliding); a hard nose-up rotation on the press that decays over a quarter
  second, which reads as the front wheels leaving before the back ones; and a
  sparse brief flare in `flameLen` that turns the exhaust from breathing into a
  badly tuned engine. The landing blows fire too -- everything else about a
  landing goes down, and the one thing that answers upward is the exhaust.
- **It winds up.** `game.boost` eases at 3.2 for the trolley against 5.5 for
  everything else, so it takes about a second to reach 1.34 and the same second
  to give it back. A hovercraft has no flywheel; a runaway trolley does.

### Smashables are back, and the ambiguity is not

The all-electric roster was built to remove exactly one thing -- *"some
electric barriers can be rammed"* -- and that is still removed. The way out is
that the new pieces are **not barriers**:

    blue, crackling, on posts, striped plinth   ->  JUMP IT
    plain brown farm junk, no stripes, no glow  ->  GO THROUGH IT

One rule, read off the picture, and "if it crackles do not touch it" is still
true of every crackling thing on the board. `junk()` builds `r_crate` and
`r_hay` out of the farm props with `wired:false` and `smash:true`. **No hazard
stripe, deliberately**: the stripe exists so a bale you can DIE on is told apart
from the bales painted into the background, and a bale you cannot die on has no
such problem.

`hit` is gated on `onWheels()` and that is the safety catch -- a ride can END
with one on screen, and the bird dying on a stack of crates three seconds after
the trolley left is the old bug in a new hat. Off the wheels they are scenery.

`smash()` knocks `game.boost` down 6% and the ease returns it over a third of a
second: *"the vehicle barely slows"* as a number rather than an adjective.
Nothing at all felt like driving through a hologram.

The pattern table got its rhythm back with them. Barrier-to-barrier still needs
a whole arc plus a beat (**2.45-2.55s**, down from 3.10-3.25 now the arc is
shorter); anything-to-smashable needs only long enough to SEE it
(**1.25-1.40s**). With every piece a barrier the trolley's stretch could only
ever be a metronome.

### The saucer: it drifts

- **`UFO_D` 1.00 -> 0.50** and that one number carries the feel. The first pass
  kept the bird's drag on the theory that the SPEEDS make a vehicle and the
  ease does not; that was the wrong half. At his drag it settled in 0.21s, so
  releasing reversed it almost at once -- not a craft, a cursor.
  Time constant is now **0.42s**, and **measured**: after a 0.6s hold, letting
  go still climbs **70 more units over 0.27s** before it turns round.
- **`UFO_G` 0.42 -> 0.18, `UFO_T` 0.50 -> 0.19.** Terminal 640 down / 765 up,
  reached over more than a second. **1.3s to cross the band** against the
  bird's 0.37 -- and that IS the weakness. You can go anywhere; you cannot go
  there *now*, so the corridor has to be chosen a second before it arrives.
- **THE WHITE WOBBLES AND THE YOLK DOES NOT**, and it is one sprite drawn
  twice with a clip at the waist (`UFO_RIM`, measured by `cut_ufo.py`). The
  obvious answer was to cut the dome into its own file; the clip is better
  because both halves come from the same picture through a transform that is
  **the identity at the waist**, so they cannot separate, cannot disagree about
  their edges, cost no bytes, and nothing had to repaint the white the dome is
  currently covering.
  It is a real spring (`UFO_WOB_K/C`), not a damp, because **overshoot is the
  entire effect** -- the lip has to go past level and come back. Driven by
  vertical speed: rising stretches it down, sinking pushes it up, a direction
  change whips it through the middle, and arriving at the hover floor kicks it
  with an impulse scaled by the drop. The lamps and the beams are moved by the
  same transform, because beams that stayed put while the hull they come out of
  stretched would be the flame-on-the-grass mistake all over again.

### The beam takes the livestock

- **`ufoReach()` is the rule and `ufoBeamLen()` is the picture.** The beam only
  takes what it is visibly standing next to: *fly low, or hold the button*,
  which the player reads off the screen rather than being told. The flicker is
  deliberately kept OUT of the rule -- an animal at the edge being taken or not
  depending on where a 19Hz sine was on that frame is a coin toss dressed as a
  mechanic. The horizontal catch (`ufoBeamHalf`) is computed from the lamp
  table, so widening the cone widens the catch.
- **The animation is the animal's own panic frames at 22Hz**, and that is the
  better picture rather than a shortcut: the one thing a cartoon abduction has
  to show is legs still running in mid air, and a purpose-drawn dangling set
  would have thrown that away and cost three sheets to do it. Lift, turn and
  shrink are staggered so it does not read as a sprite being scaled.
  **The pull in x runs ahead of the lift** and has to: the world scrolls at
  nine hundred units a second, so anything tracking its own world position for
  even a moment is gone before it has risen. It is being pulled to a SHIP.
- **`riding()` was giving the saucer a bumper it does not have.**
  `drawSpectators` read `riding()` for the trolley's bumper and its exhaust
  scorch, which was correct for exactly as long as there was one vehicle; fly
  low past a cow and the cow was bowled by thin air. Both are `onWheels()` now.
  Every rule that belongs to a PARTICULAR vehicle has to name it.

### The saucer's own music

`UFO_MOVEMENTS`/`UFO_TRACKS`, and `pickRideTrack` chooses the pool from the
vehicle -- everything downstream keeps pointing at `RIDE_TRACK` and never
learns there are two lists. It was borrowing the trolley's metal, which is the
wrong music by the width of the galaxy.

Generation was **explicitly asked for** ("generate alien type music when i get
the UFO") -- the standing rule is that it stopped in favour of the user's own
recordings. Three takes through `mode:"music"`, and the one that ships was
chosen **by measuring the join** (`cut_ufo_music.py`): head RMS against tail
RMS over 60ms, take 3 at a ratio of 0.96 against 0.60 and 0.78. Levelled to
**RMS 5388** against `music_ride` 5512 and `music_ride_b` 5261 -- both vehicles
play through the same element at the same 0.60, so a decibel of difference
would make one vehicle feel louder than the other and nobody could say why.

`S.abduct()` is the pickup's shape in miniature and deliberately much quieter:
**0.064**, sitting with `egg` at 0.066, because the pickup happens once and
this can happen four times in a low pass.

### The test that was lying (and had been for a while)

**`?selftest` reported apex=0 for every hold and `?ridetest` reported a 0px
window for all six barriers -- and neither was a physics fault.** Both fire on
a 40ms timer, `thrustOn()` opens with `if(!LOAD.ready) return;`, and the
loading gate holds boot until the art is decoded. Every press the tests made
was silently dropped. A warm cache hides it entirely, which is why it survived:
the same page passes in a browser that has been there before and fails on a
cold headless probe, and the cold probe is the one that reports. `whenLoaded()`
now gates both.

`?ridetest` also had to learn that a press is a HOLD --
`thrustOn(); thrustOff();` on one frame is a tap, and a test that taps measures
the short jump and calls the roster unclearable. It reports the tap window
separately now.

## Six vehicles, and a table instead of a boolean (2026-09-10)

Four more out of the mystery egg — Corn Rocket, Eggshell Hopper, Magnet Spoon,
Toaster Jumper — from the user's own concept sheets, with the physics for each
taken from the brief in `dgh/ref/veh-brief.txt` rather than invented.

### The refactor came first, and it had to

Two vehicles could be told apart with a boolean. Six cannot: every
`inUfo() ? a : riding() ? b : c` in the file was a place where the fourth,
fifth and sixth would be silently forgotten. So `VEH` is a table keyed by id,
`V()` is the spec of whatever is being ridden, and `game.veh` is a STRING now
rather than 0/1.

What is in the table is **data** — gravity, drag, thrust, boost, ease, which
pattern table, which music pool, clearance — plus six **hooks** for the places
a vehicle behaves differently rather than merely being tuned differently:
`press`, `release`, `land`, `feel`, `start`, `draw`. A vehicle that does not
override a hook simply does not have it, and the default applies. That is how
the two flyers get the bird's hold for free (no `press`) and how the two of
them stay unable to land (no `land`) without anybody writing that they cannot.

`onWheels()` still means **the trolley specifically**, and kept that meaning
even though the hopper and the toaster plainly have wheels: every one of its
callers is about something only the trolley has — the blackout, the bumper, the
exhaust scorch, the tap-or-hold jump. Widening it would have handed three of
those to two vehicles that own none of them. `V().kind === 'ground'` is the
question about wheels; `onWheels()` is the question about the trolley.

### The four, and what each one's weakness is

| | control | feel | weakness |
|---|---|---|---|
| **Corn Rocket** | hold to climb, release to dive | fastest thing in the game (boost **1.62**), drag **0.40** so the time constant is 0.52s | you aim it and live with the aim |
| **Eggshell Hopper** | press *as it lands* | bounces whether you press or not; apex 0.30 → 0.62 of the play area on the timing | cannot choose to stay down, or up |
| **Magnet Spoon** | tap to flip the poles | signed gravity, ~0.5s to cross, snaps onto whichever surface the coils point at | two heights exist and nothing between |
| **Toaster Jumper** | hold to charge, release to pop | charge 0 → 1 in 0.8s, apex 0.24 → 0.80, reusable for ever | the power is paid for in ground time |

Measured, four seconds each with real obstacles: rocket `y 26..588`, hopper
`y 0..510`, spoon `y 0..604`, toaster `y 0..361`, all six clean.

**The spoon is the only thing in the game with a surface above it.** `sgn()` in
its spec is the whole of how a gravity flip is expressed in a movement model
written assuming there is one answer to "which way is down" — `acc` gains one
multiplier and everything else is unchanged. Arrival is a snap rather than the
bird's ceiling bounce, and it is the same event on either surface, deliberately:
the ceiling is not a special place, it is the other floor.

**The hopper never rests.** `land` is what launches it, so `feel` also bounces
it if it ever finds itself on the ground — a death, a revive, a debug flag.
Without that line the first version measured `y 0..0, contacts 0`: the pickup
was taken while he was already standing, `onGround` was still true, and the
landing that starts the whole rhythm never happened.

**`hopArm` is a continuum, not a window.** A press sets it and it decays; the
landing reads how much is left. Pass/fail would have been easier and worse —
this is a skill a player should be able to feel themselves getting better at,
and the bounce's pitch rises with it so the timing has a sound as well as a
height.

### The art: four sheets, four stills, and one that had to be magenta

Same two-attachment shape `gen_ufo.py` proved, and the prompt says which is
which: `truck_drive.webp` for the game's style AND the pilot (the brief is
emphatic that Nugget is not to be redesigned, so he goes in as a picture rather
than as adjectives), and the concept sheet for the design — with "take the
vehicle, ignore the page", because those sheets are marketing boards with
logos, captions and several poses on them.

**The corn rocket is shot on MAGENTA** and the other three on green, for the
same reason the parallax layers are: nothing in the art may be the key colour,
and a corn husk is bright green. Nugget's teal cap survives a green key — that
was measured on the saucer sheet — but a saturated leaf does not.

**What was asked NOT to be drawn is the interesting half.** No flame on the
rocket, no spring or base under the eggshell, no lightning on the spoon, no
toast in the toaster's slot. Every one of those has a rule — it burns with the
button, it compresses with the landing, it arcs on the flip, it rises with the
charge — and a painted one cannot answer an input on the frame it happens. They
are drawn in code, the way the trolley's exhaust and the saucer's beam are.
The rocket's flame is literally `drawExhaust`, reused whole: it already draws
fire pointing left out of a root on the right, which is what a rocket
travelling right needs.

`tools/cut_veh4.py` cuts them and measures the anchor each one needs, with
`--check` drawing the answer back onto the sprite. Two of those measurements
were wrong first time and the proof caught both:

- The toaster's slot came back at the very top of the picture, on Nugget's cap,
  because "the highest covered row of the middle third" is the CHICKEN.
- Rewritten as "the whitest pixels" it was wrong again — Nugget's cream body is
  240,235,215 and sails through any threshold the casing passes. It is the
  **largest white connected component** now, which is a fact about the sprite
  rather than a threshold that needs tuning per render.

### The music: one loop each, and the window is searched for

`gen_veh_music.py` and `cut_veh_music.py`. Every prompt names an instrument and
a tempo rather than a mood, for the same reason the art prompts say what the
shape is: surf rock and a banjo for the rocket, tuba and slide whistle for the
hopper, an arpeggio and a switch-throw sweep for the spoon, honky-tonk ragtime
for the toaster.

Two things this cost:

- **Music mode sometimes hands back the VIDEO.** A generated track is a
  `<generated-music>` block wrapping a `<video>` and the MP3 lives behind its
  own "Audio only" entry; when that is slow, what lands in the library is a
  1.4 MB .mp4 of the cover art. Three of the four arrived that way. `-vn` and
  ffmpeg, and nothing about the audio is different.
- **Three of four jobs failed the first time** with "No audio appeared before
  the timeout", two of them after logging "First audio appeared". Retried one
  at a time, they all came back. It is intermittent, not the prompt.

**The loop window is SEARCHED FOR rather than taken from the start.** Cutting
the first 30 seconds gave the rocket a seam ratio of 2.30 — the slice opened
quiet and closed loud, so every time round it fell off a cliff. The generator
hands back a minute or more, so the track is decoded once and a 30s window is
slid over the samples comparing 60ms of head against 60ms of tail at every half
second. All four now land at **0.98–1.01**, from offsets of 18.7s, 18.1s, 9.1s
and 21.5s — not one of them was the start.

All six are levelled to **RMS 5400** against `music_ride` 5512 /
`music_ride_b` 5261, because every vehicle plays through the same element at
the same 0.60.

Sounds, measured with `tools/sfx.py` as always: the four pickups at
**0.248–0.255** beside `ufoget` 0.243 and under `truckget` 0.296; the ones that
repeat — `hopbounce` 0.054–0.086, `spoonflip`/`spoonsnap` 0.057, `toastpop`
0.100–0.150 — down in the `egg`/`near` band, because a sound that fires twice a
second at pickup level becomes the run's texture.

### Two things the six-vehicle economy needed

- **`pickVeh` is a shuffled bag.** With two vehicles alternating was right; with
  six a coin shows you the same one twice before you have seen half of them,
  and a fixed rotation is learnable — which the mystery egg must not be. Deal
  all six in a random order, hand them out one at a time, reshuffle when empty.
- **`dropRate` takes the BEST vehicle's "turns up more often", not the
  product.** Six of them multiplied would hand a fully upgraded garage an egg
  every four seconds. The egg is shared, so the best one wins, which is what a
  player means by it.

`?veh=NAME` starts a run in any of them. `?ride` and `?ufo` still work, because
they are in every note written before today.

## Next

- **Nothing spends the eggs yet** -- the shop exists and none of it
  transacts. See **The shell around the game**; the build order is
  currency, missions, shop, then characters and skills.
- The crows have no music cue. A stab under the lock, ducking the track for
  half a second, is the obvious next thing — `musicScene` already ducks.
- The electric set has no sound of its own beyond `S.zap()` on a death. A hum
  that rises as you close on a live wire is the obvious next thing, and the
  near-miss meter already knows the distance.
- There is one map on purpose. A second one is a `THEME` plus a builder plus a
  deliberate way in, never a timer that swaps the world out mid-run.
- Every image is already lossless WebP and the music is already Opus. The
  next real size win is the five music tracks the game never plays, and
  that is a bundle-time exclusion rather than a code change.

## Why the map looked boring, and the four rules that came out of it

The map was called "boring", "an unpolished asset flip". It was not a bug in the
game: every one of the 65 pictures passed every check in `tools/audit_map.py`
while it looked that way. It was the PROMPT, and four separate faults in it.

**1. An interior is not a row of props.** The `ROW` clause asks for things
"evenly spaced with clear empty gaps between them". Right for a farm -- you
should see sky between the barns -- and wrong for the inside of a prison, which
rendered as four detached cell doors floating on the sky wash. Interiors now get
`INTERIOR`: one unbroken back wall, everything set INTO it, plus a recess to see
into and something crossing in front so the picture has depth. Run
`python tools/joins.py` to see any world's panels butted as the game tiles them
-- floating props are obvious there and invisible in a single panel.

**2. Panels BUTT, so a margin is a hole.** The draw loop steps by exactly one
panel width. `EDGES` asks for empty magenta margins and the cutter enforced 4%
more, which on a continuous wall is a hole punched to the sky at every join --
reported as "the walls suddenly appear". Interiors get `JOIN` instead: the wall
is cut off by the frame and runs on into the next picture, its top named as a
straight line at two thirds height so four independent renders line up. They are
cut full-bleed, with no margin and **no edge fade**.

**3. One world, one palette.** This only became visible once the walls joined
up: while the panels were floating objects, nothing made the guard station and
the canteen agree about colour and nothing had to. Butted together, a cream room
against a grey one is a hard colour step at every join. Each world's colours are
now named in `PALETTE` and pasted into the prompt.

**4. Never ask for magenta in the artwork.** Magenta is the key colour.
`key_magenta` deletes any pixel with r>150, b>150, g<110. Three prompts asked for
magenta lighting, a magenta nebula and magenta accents -- instructions to punch a
hole through the picture. Green and warm amber are the accents these worlds get.

`audit_map.py` grew the check that would have caught all of this: **VOID**
measures how much of an interior's frame actually has anything in it, and
**WALL STOPS** whether the wall reaches its edges. Interiors are exempt from the
margin, edge-fade and ground-rule checks, which test them for being the thing
that made the map cheap.

### Two other things worth knowing

**The far layer was one picture for 3500m.** Every world past the empire owned
only its floor and ceiling; the largest area on screen never changed from the
empire to the end of the run, which is exactly the reported "the background dont
change, just the props change". Six per-world `far` tiles are written in
`LAYERS`; `index.html` still lists `near`+`hang` only and flips to
`underSet(['far','near','hang'])` once the files exist.

**Gemini Studio is shared with other sessions.** It runs one job at a time, and
another session's batch sits in front of yours. `render_panels.py` used to start
its patience when it QUEUED a prompt, so a panel that was merely waiting got
declared dead and retried into the back of the same queue. The clock now starts
when the studio picks the job up. And `close_thread(all=True)` is the only lever
these jobs offer -- they carry no threadId -- so the tab sweep waits until
nothing else is running rather than closing someone else's conversation.

`python tools/join_page.py prison cia > page.html` builds the before/after
review page; stages live in `tools/_before/` and `tools/_step1/`.

### The join fix that worked, and the one that did not

**Panels OVERLAP, they do not butt.** `MID_OVERLAP` is 7%: the draw loop steps by
`g.W * (1 - MID_OVERLAP)` and every panel carries an alpha ramp down its LEFT
edge, baked once at load in `rampLeft()`. A panel's soft edge therefore dissolves
onto the picture BEHIND it instead of onto the sky. This is what finally made the
joins invisible -- fading the ends and butting them, which is what the cutter used
to do, punches a hole through an interior wall at every join. Only the left edge
is ramped; the right is the one that gets covered. Everything downstream keys off
`step`, not the panel width, including which metre a panel thinks it stands at.

**Attaching the previous panel does NOT work, and it was measured twice.** The
obvious fix -- upload panel N, ask Gemini to continue it into panel N+1 -- is
implemented and working in `tools/render_chain.py`, and on the prison it scored:

    without it   colour 67.5   profile  0.0%
    with it      colour 90.4   profile 21.7%
    with the height rule restated to fight it   123.6 / 99.6%

Given a reference the model REFRAMES. The style matches beautifully and the wall
comes back lower, leaving a gap of sky above it -- and a profile step is a hole,
which is worse than a colour step. Keep the tool; do not reach for it before
reading this.

`python tools/joins.py -v` scores every join in the map, including the WRAP (the
last panel is followed by the first again, and no left-to-right chain can fix
that one). It measures the FILES; since the game overlaps them, treat the numbers
as a worst case and a ranking, not as what a player sees.

`python tools/mapshot.py 1700 2600` photographs the map from inside the running
game. It needs `python -m http.server 8899` in the project root, and it works
because of two flags: `?noboot` (the loading gate runs on requestAnimationFrame,
which headless Chrome throttles -- without it every shot is the loader frozen at
97%) and a real TAP (nothing is on `window`, so there is no function to call).

`python tools/harmonise.py --write` pulls each world's panels onto one tone by
partial Reinhard transfer. It runs BEFORE `opt_panels.py`, never on the farm or
the approach -- those are meant to be separate buildings with sky between them.

## The far layer and the floor (the `dont-get-hit-art` brief)

A brief arrived on the Desktop as `dont-get-hit-art/PROMPT.md` with a style bible
and three gaps. Its numbers all check out against the repo -- UPM 60, ANT_H 52,
Nugget 190, all nine zone starts. Four things in it are wrong or stale and are
worth knowing before following it:

**Its reference frames are OLD.** `style-reference/` shows the prison as four
cell doors floating with sky between them and the ant empire's dirt-mound
horizon standing behind six zones. Both were fixed. Attaching those frames to a
generation request teaches the model exactly the composition that was removed --
which is the whole point of attaching a reference. `tools/restyle_refs.py`
re-shoots the same metre marks from the running build into
`style-reference-current/`, beside the originals so the pairs still line up.

**"Magenta/violet is allowed" is wrong.** Magenta is the key colour. See the
rule above; it cost the alien facility its containment chamber.

**Gap A was half-solved before it was raised.** Six `far` tiles now exist and the
six late worlds list `far` alongside `near` and `hang`. But the far band is
y 304-394 and the mid band is y 192-450, so far draws INSIDE mid -- and the
interiors are full-bleed walls, which cover it. The tiles read where a zone shows
sky: the Area 51 airstrip, the launch pad, the moon surface. In the prison, the
reactor, the base and the alien facility the horizon is behind a wall, which is
what a wall is for. The symptom the brief describes -- ant mounds behind the
prison -- had already gone when the cell doors stopped being four objects with
gaps between them.

**Gap B needed code, not just art.** The floor runs at f=0.60, the fastest layer
on screen, and every world had ONE tile repeating. Two DIFFERENT tiles have no
shared edge -- a tile is cut to loop against ITSELF via `bg_layers.loop_seam` --
so variants butted would be a hard vertical line in the fastest layer. A world
with variants therefore switches to the same 7% overlap and left-edge ramp the
mid panels use (`NEAR_SEQ`, `nearTileAt`, `NEAR_SETS`); a world without them
keeps butting, because one tile overlapped with a 93%-offset copy of itself
ghosts the whole pattern.

Two rules for floor variants:

- **A variant must be the EXACT pixel size of the `near.webp` it stands in for.**
  `bgGeom` reads the geometry off one image and draws every tile in the slot at
  that size, so an odd-sized variant is not drawn wider, it is drawn STRETCHED
  and its ground line lands somewhere else. `cut_layers.py` fits them.
- **A floor tile is scaled BY ITS HEIGHT.** Under ~140px it is magnified into
  mush; the cutter says so.

Tiles live where the game has always loaded them: `art/bg/` for the farm and the
approach (which share a floor), `art/ant/` for the empire, `art/panels/<world>/`
for the six after it.

