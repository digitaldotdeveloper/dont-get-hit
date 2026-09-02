# DON'T GET HIT — handover

Live: https://digitaldotdeveloper.github.io/dont-get-hit/
Hat picker: https://digitaldotdeveloper.github.io/dont-get-hit/chickens.html
Repo: https://github.com/digitaldotdeveloper/dont-get-hit
Local: C:\Users\it\Desktop\jj

Portrait one-button arcade flyer. **Hold to flap, release to fall.** The bird
flies with its own wings — deliberately not a jetpack, so the game reads as its
own thing rather than a Jetpack Joyride clone. Target is Android with ads later;
GitHub Pages is only the test harness.

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
| Portrait framing | `function resize()` |
| Gates | `function spawnGate`, `OB.tower`, `OB.hanger` |
| Gate members fill their hitbox | `crateStack`, `CAP_H` |
| Obstacles (16) | `const OB = {` |
| Difficulty tiers | `function tierNow`, `function spawnPattern` |

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
- Portrait: `SCALE = min(CH/1450, CW/790)`. Narrower view than landscape on
  purpose — a bigger bird matters more than lead time when the challenge is
  altitude. If you widen it, the bird shrinks.
- `CEIL` is the altitude cap; air hazards spawn at random heights inside it.

## Debug flags

`?auto=1` start a run · `?demo=1` auto-flap · `?flap=0.5` freeze the wings at one
point in the cycle · `?hold=0` glide · `?zoom=1.7` zoom on the bird ·
`?dbg=1` altitude readout · `?stage=1` drop three gates in front · `?solo=1` character only,
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
- Each sheet comes back at its own scale, so each is normalised by its median
  figure height, and every frame stores `lift` - pixels above the sheet's shared
  ground line - so poses stay registered to the floor.

`SPR` converts frame pixels to world units. `pickFrame` maps state to frame.
**Every frame is optional**: if an image fails to load, `FR.ready` stays false and
the procedural puppet draws instead.

**Cosmetics do not apply while frames are in use** - the cap, shades and chain are
drawn into the frames. That is the trade for hand-drawn art, and it is why the
puppet path is still worth keeping.

## Environments

Two themes in `THEMES` (`city`, `farm`), rotated per run by `startRun`. Both are
drawn in code so the parallax layers tile perfectly and nothing extra downloads.
`?theme=farm` forces one.

## Music

`audio/theme.mp3` is generated through Gemini Studio (`mode:"music"`). It plays
on a loop through `initTrack`/`trackVol`, and the old synthesised groove stays as
an automatic fallback if the file fails to load (`musicTick` returns early when a
track exists). The mute button controls both.

## Known rough edges

- Expression is one eye plus a brow, driven by `p.shockT`. It reads at portrait
  size but there is room for more.
- Wearing every slot at once gets visually busy. Tuning, not architecture.
- At the bottom of the flap (`?flap=0.375`) the near leg draws over the wing tip.
  One line of draw order in `drawChicken` if it starts to matter.
- **No jetpack cosmetics.** The bird flies with his own wings; a jetpack would
  undercut the one idea that keeps this from being a Jetpack Joyride clone.
- Gate gap size is the difficulty dial: `lerp(500, 290, game.diff)` in
  `spawnGate`. Everything else about the curve follows from it.
- `chickens.html` keys green in-browser, so it only works over http(s), never
  `file://` (tainted canvas).

## Deliberately not built yet

Shops, currencies, missions, customisation UI, multiplayer, ads, IAP, login.
