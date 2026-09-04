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
    python tools/npc_frames.py              # recut the cow, pig and goat frames
    python tools/farm_seams.py              # where the farm panels should be cut
    python tools/gen_bg.py                  # generate the parallax layers (Gemini)
    python tools/bg_layers.py               # key, loop and trim them
    python tools/cage_art.py                # recut the intro barn and its door
    python tools/farm_strip.py              # the old one-image background
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

## The basket -- the vehicle

Jetpack Joyride's contract, and every part of it earns its place: a vehicle is
picked up mid-run, it **replaces** the control you already know, the level
changes to suit it, and **a hit takes the vehicle rather than the run**. That
last one is why vehicles feel like a reward instead of a handicap -- riding is
strictly safer than not, so you chase the pickup.

Here it is a wicker basket under a bunch of balloons (`art/basket.webp`,
`art/balloons.webp`, both generated by the same magenta-key route as the
background):

- **Control.** The flap is gone: hold to rise, release to sink, and both gently.
  It is the *same three lines* of movement code with gravity and thrust cut to
  about a third and drag nearly doubled (`RIDE_G/RIDE_T/RIDE_D`) -- a second
  movement model would be a second thing to keep in step with the first. It
  floats where the bird darts, and that contrast is the whole vehicle.
- **Level.** `RIDE_PAT` replaces the pattern table while riding: gates and wires
  only, no corn. Corn is ankle-high clutter a floating basket sails over, and a
  hazard you cannot fail is worse than no hazard.
- **Clearance.** `CLEAR_RIDE`, because the rig is far bigger than the bird.
  **Measure it rather than guessing**: basket plus balloons stands about 410
  units tall, so the first value of 430 left twenty units of slack and the ride
  was a punishment. 560 is the one in the game.
- **Hitbox.** Only the lower half of the balloons is solid. They are the tallest
  part of the rig and the least believable thing to lose it to -- clipping the
  top of a balloon on a wire you were never near reads as a bug, not a mistake.
- **Ending.** Fourteen seconds or one hit. Either way the balloons pop and
  `RIDE_GRACE` seconds pass before he is solid again; without that he is
  vulnerable inside the same gap that just took the basket.

`?ride=1` starts a run already in it, which is the only sane way to look at a
vehicle that otherwise turns up once every twenty seconds. The pickup itself is
placed by `eggFree`, the same "is this bit of sky safe" test the eggs use,
because a reward you cannot reach without dying is a punishment.

## Next

- Nothing spends the eggs yet.
- The crows have no music cue. A stab under the lock, ducking the track for
  half a second, is the obvious next thing — `musicScene` already ducks.
- The electric set has no sound of its own beyond `S.zap()` on a death. A hum
  that rises as you close on a live wire is the obvious next thing, and the
  near-miss meter already knows the distance.
- There is one map on purpose. A second one is a `THEME` plus a builder plus a
  deliberate way in, never a timer that swaps the world out mid-run.
- The three wall panels are ~345 KB each, so first load pulls about 1 MB of
  background. Re-encoding to WebP would take it under 300 KB total.
