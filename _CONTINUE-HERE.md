# DON'T GET HIT — handover

Live: https://digitaldotdeveloper.github.io/dont-get-hit/
Repo: https://github.com/digitaldotdeveloper/dont-get-hit
Local: C:\Users\it\Desktop\jj

Everything is in **index.html**. One file, no build, no assets, no dependencies.

## Where things are (search these strings)

| What | Marker |
|---|---|
| Palette | `const C = {` |
| Canvas / virtual resolution | `function resize()` |
| Audio + music groove | `const A = {`, `function musicTick()` |
| Skeleton lengths | `const RIG = {` |
| Leg IK | `function legIK` |
| Run cycle foot path | `function footPath` |
| All 20 animations | `function poseRun` … `function poseScared` |
| Faces / expressions | `const FACES = {`, `function drawFace` |
| Character renderer | `function drawCharacter` |
| Death ragdoll | `function Ragdoll()` |
| Obstacles (16) | `const OB = {` |
| Parallax bake | `function buildLayers()` |
| Difficulty tiers | `function tierNow`, `function spawnPattern` |
| Near-miss + combo | `function nearMiss` |
| Menus / HUD | the `<style>` block and `.screen` divs |

## Coordinate system

World units, not pixels. `SCALE = min(cssH/880, cssW/1300)` guarantees at least
1300×880 units are visible, so reaction time is identical on every device.
`GROUND` is the ground line. Character height ≈ 200 units.

Character local space: **origin = hip**, +x forward, +y down.

## Tuning numbers that matter

- `GRAV = 5250`, `JUMP_V = 1774` (apex 300), `JUMP_CUT = 1485` (apex 210 on a quick tap).
- Speed ramps `620 → 1080` over 85s (`game.diff`).
- Air obstacles sit at `base:210, h:230`. The band is deliberately taller than the
  max jump apex so a jump can **never** sneak over them — that keeps the rule
  "don't jump into stuff" honest. If you change `JUMP_V`, re-check this.
- Ground obstacles are 26–158 units tall; even the shortest tap clears them.

## Deliberately not built (yet)

Shops, currencies, missions, customisation, multiplayer, ads, IAP, login.
The slice exists to prove the loop is fun first.

## Ideas parked for next pass

- A second environment (the parallax bake already supports swapping tile painters).
- Coins/pickups along the jump arcs to hint safe lines.
- A "so close" callout when a run ends within a few hundred points of the best.
- Daily seed / ghost of your best run.
