# DON'T GET HIT

A one-tap arcade runner. **Tap to jump over stuff. Don't jump into stuff.**
That's the whole game — understandable in about three seconds.

**Play:** https://digitaldotdeveloper.github.io/dont-get-hit/

## What this is

A polished vertical slice built to answer one question: *is the basic loop fun?*
No shops, no currencies, no missions, no IAP, no login — just
`RUN → JUMP → AVOID → SURVIVE → HIGH SCORE`.

Single file, zero dependencies, zero image assets. Everything is drawn
procedurally on a 2D canvas and every sound is synthesised with the WebAudio API.

## The character

He is not a sprite sheet. He is a **skeletal rig** — IK-solved legs (so his feet
actually plant on the ground instead of skating), FK arms, and spring-driven hair
and jacket hem that lag behind his motion. Every animation is a pose function, so
they blend into each other with automatic follow-through.

Animations in the build: idle, run, sprint, jump anticipation, jump, fall, land,
bad-landing stumble, near-miss reaction, impact, backward launch, verlet ragdoll,
funny death, recovery, celebration, plus shocked / confused / angry / scared /
confident acting beats.

**Signature move:** on a near miss he snaps his head around to stare at whatever
nearly killed him with a shocked face, then immediately gets back to running.
A 2D head-turn cheat (`scaleX = cos(π·t)`) makes the flip read as one snappy
cartoon smear.

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
