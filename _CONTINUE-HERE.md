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
`?wear=head:hat_bucket,face:shades_art,neck:scarf_art` set a loadout.

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

## Music

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

`lockLandscape()` runs on the first gesture, from `audioInit`. It is
best-effort and every failure is swallowed: a phone only honours an orientation
lock from inside fullscreen and only off a user gesture, and desktop is left
alone entirely (`TOUCH` guard). The `#rotate` gate is what actually guarantees
landscape; the lock is a convenience.

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
bait. Ten-frame spin sheet. Taken eggs fly to the counter; the pickup pings up a
semitone per egg in a streak. `game.eggBank` persists in `localStorage` under
`dgh_eggs`.

## NPCs

Cricket guards in suits, `cricket0..5`, a six-frame panic loop with the antennae
whipping. `drawSpectators` plays the loop only while a chicken is going past at
speed and holds frame 0 otherwise. `drawLilChicken` is the flat fallback if the
frames have not loaded.

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
    python tools/build_apex.py              # rebuild the barn's roof from sheets/v2/barn_raw.png

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

## Next

- Nothing spends the eggs yet.
- There is one map on purpose. A second one is a `THEME` plus a builder plus a
  deliberate way in, never a timer that swaps the world out mid-run.
- The three wall panels are ~345 KB each, so first load pulls about 1 MB of
  background. Re-encoding to WebP would take it under 300 KB total.
