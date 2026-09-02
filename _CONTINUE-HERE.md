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

He is **a painted head on a procedural body**. That split is the whole design:

- `art/head-snapback.png` / `art/head-bucket.png` — the hat, comb, face and beak,
  cut out of the Gemini Studio hero renders. This carries the identity.
- Body, wings, tail, legs and sneakers are **drawn in code** (`drawChicken`), so
  they can squash, flap, plant and ragdoll.

So: **swapping the hat is swapping one PNG** (`loadHead('bucket')`), and legs or
accessories become new draw calls, not new art. That is the customisation plan
from the brief, already wired.

The heads were produced by `art/snapback.png` → key green → keep the largest
connected blob of the top 40%. If you regenerate art, redo that step.

## Where things are (search these strings)

| What | Marker |
|---|---|
| Chicken rig constants | `const CK = {` |
| Head loading / hat swap | `function loadHead` |
| All poses | `function poseRun` … `function poseCheer` |
| Flap-driven flight pose | `function poseFly` |
| Character renderer | `function drawChicken` |
| Wing shape | `function drawWing` |
| Death tumble + egg | `const rag = {`, `function layEgg` |
| Feathers | `function featherBurst` |
| Flight physics | `const GRAV`, `// ---- flight ----` |
| Portrait framing | `function resize()` |
| Obstacles (16) | `const OB = {` |
| Difficulty tiers | `function tierNow`, `function spawnPattern` |

## Feel numbers that matter

- `GRAV 2950`, `FLAP_ACC 5100`, `FLAP_HZ 5.6`. Lift arrives **in pulses on the
  downstroke**, not as constant thrust — that is what stops it feeling like a
  jetpack. `VY_UP/VY_DOWN` clamp the climb and the dive.
- Speed ramps `430 → 730` over 85s. Much slower than the old jump version: you
  are steering continuously, not reacting once.
- Portrait: `SCALE = min(CH/1300, CW/700)`. Narrower view than landscape on
  purpose — a bigger bird matters more than lead time when the challenge is
  altitude. If you widen it, the bird shrinks.
- `CEIL` is the altitude cap; air hazards spawn at random heights inside it.

## Debug flags

`?auto=1` start a run immediately · `?demo=1` auto-flap · `?flap=0.5` freeze the
wings at one point in the cycle (0–1) for inspecting the pose.

## Known rough edges

- Only one expression. The face is baked into the head PNG, so shock/dizzy are
  done with cartoon marks (`p.shockT`) and body language instead. If expressions
  turn out to matter, generate 2–3 more head crops and swap on state.
- Obstacles are still the ones designed for the jump game. They work, but a
  flyer wants gates and vertical gaps — that is the next real design pass.
- `chickens.html` keys green in-browser, so it only works over http(s), never
  `file://` (tainted canvas).

## Deliberately not built yet

Shops, currencies, missions, customisation UI, multiplayer, ads, IAP, login.
