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

**One animated chicken, drawn entirely in code, plus interchangeable cosmetic
layers.** There are no per-outfit animations and there never should be.

An earlier version glued a painted head onto a code body; it read as assembled
parts and was scrapped. Keep the base character in one drawing language.

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
| Cosmetic registry / slots | `const SLOTS`, `defineCosmetic`, `equip` |
| Cosmetic draw hook | `function drawSlot` |
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

- `GRAV 2600`, `FLAP_ACC 11000`, `FLAP_HZ 4.6`. Lift arrives **in pulses on the
  downstroke**, not as constant thrust — that is what stops it feeling like a
  jetpack. **The mean of a half-sine is 1/pi**, so peak lift must be about 3.1x
  the average you actually want; getting this wrong once made holding the screen
  push him *down* and the game looked dead. `VY_UP/VY_DOWN` clamp climb and dive.
- Speed ramps `430 → 730` over 85s. Much slower than the old jump version: you
  are steering continuously, not reacting once.
- Portrait: `SCALE = min(CH/1300, CW/700)`. Narrower view than landscape on
  purpose — a bigger bird matters more than lead time when the challenge is
  altitude. If you widen it, the bird shrinks.
- `CEIL` is the altitude cap; air hazards spawn at random heights inside it.

## Debug flags

`?auto=1` start a run · `?demo=1` auto-flap · `?flap=0.5` freeze the wings at one
point in the cycle · `?hold=0` glide · `?zoom=1.7` zoom on the bird ·
`?dbg=1` altitude readout in the tab title ·
`?wear=head:hat_bucket,face:shades_art,neck:scarf_art` set a loadout.

## Known rough edges

- Expression is one eye plus a brow, driven by `p.shockT`. It reads at portrait
  size but there is room for more.
- Wearing every slot at once gets visually busy. Tuning, not architecture.
- **No jetpack cosmetics.** The bird flies with his own wings; a jetpack would
  undercut the one idea that keeps this from being a Jetpack Joyride clone.
- Obstacles are still the ones designed for the jump game. They work, but a
  flyer wants gates and vertical gaps — that is the next real design pass.
- `chickens.html` keys green in-browser, so it only works over http(s), never
  `file://` (tainted canvas).

## Deliberately not built yet

Shops, currencies, missions, customisation UI, multiplayer, ads, IAP, login.
