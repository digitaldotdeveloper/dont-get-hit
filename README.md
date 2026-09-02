# DON'T GET HIT

A portrait one-button arcade flyer. **Hold to flap. Don't hit anything.**
That's the whole game — understandable in about three seconds.

**Play:** https://digitaldotdeveloper.github.io/dont-get-hit/

## What this is

A polished vertical slice built to answer one question: *is the basic loop fun?*
No shops, no currencies, no missions, no IAP, no login — just
`RUN → JUMP → AVOID → SURVIVE → HIGH SCORE`.

Single file, zero dependencies, zero image assets. Everything is drawn
procedurally on a 2D canvas and every sound is synthesised with the WebAudio API.

## The character

A **painted head on a procedural body**. The hat, comb, face and beak are cut
from a Gemini Studio render; the body, wings, tail, legs and sneakers are drawn
in code. That split means the wings can actually flap, the body can squash and
ragdoll, and swapping the hat — or later the legs and accessories — is a one-line
change rather than new art.

He flies with his own wings on purpose: lift arrives in pulses on each
downstroke, so altitude is something you keep working at rather than a thrust
button you hold. No jetpack.

Animations: idle, peck and strut menu beats, ground run with the head locked in
space the way a real chicken's is, flap, glide, dive, landing squash, near-miss
flinch with a shock pop, impact, tumbling death with a feather burst — and he
gets hit hard enough to lay an egg.

## Obstacles (16)

*Jump over:* traffic cone · delivery boxes · banana peel · shopping cart ·
rolling barrel · office chair · giant coffee cup · vacuum cleaner ·
bouncing basketball · giant rubber duck · rolling pizza · birthday cake

*Do **not** jump — run under:* pigeon flock · newspaper swirl · beach balls

*Falls from the sky (telegraphed with a shadow):* sofa · street sign

## Difficulty

Five tiers over ~72 seconds. The first 13 seconds are single, generous, slow
obstacles so the opening always feels good. After that: frequency, speed and
combinations ramp, and ground→air combos start appearing.

## Feel

Screen shake, hit-stop, slow-motion pulses on near misses, squash and stretch,
particles, combo multiplier, score popups, a groove that speeds up with the run,
and instant restart.

## Running it

Open `index.html`. No build step.
`index.html?auto=1` skips the menu and starts a run — useful for testing.

Controls: tap / click / <kbd>Space</kbd>. Hold slightly longer for a higher jump.

## Character direction

`chickens.html` is a scratch page for picking the character — four chicken designs, each with its own run cycle, all driven by the same IK rig the game uses. Live at /chickens.html
