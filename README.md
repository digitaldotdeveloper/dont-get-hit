# DON'T GET HIT

A landscape one-button arcade flyer. **Hold to flap, release to fall. Don't hit
anything.** Understandable in about three seconds.

**Play:** https://digitaldotdeveloper.github.io/dont-get-hit/
Target is Android with ads; GitHub Pages is the test rig.

## The game

Nugget kicks his way out of a barn cage and runs east across Cluck County, a
painted farm somebody has wired up out of insulators, warning signs and a car
battery. The wire is the hazard. Ground props you jump; electric pieces you fly
through. Crows come at you horizontally and announce themselves first. A pickup
truck turns up as a mystery egg and **cuts the farm's power** while you drive it.

He flies with his own wings on purpose — lift arrives in pulses on each
downstroke, so altitude is something you keep working at rather than a thrust
button you hold. No jetpack.

## Running it

Open `index.html`. No build step, no dependencies.

    ?auto=1     skip the menu and start a run
    ?dbg=1      publish the internals as window.DGH
    ?ob=KEY     park one hazard on screen
    ?hit=1      draw the lethal shapes over the art
    ?ride=1     start already in the truck
    ?dist=N     start a run N metres in
    ?obtest=1   check openings, spacing and transits
    ?sfx=1      render the sounds offline instead of playing them
    ?noboot=1   skip the loading gate (harnesses that drive runs directly)

The full list is in `_CONTINUE-HERE.md`. Controls: tap / click / <kbd>Space</kbd>.
Portrait shows a turn-your-phone gate and freezes the run.

## What is in here

    index.html          the whole game, one file
    art/                what ships: character parts, props, backgrounds, FX
    anim/               136 character and NPC frames
    audio/              three tracks, Opus 64k + MP3 96k fallback
    tools/              the art pipeline and the test harness
    chickens.html       the character/hat picker
    PIPELINE.md         how the art is made, and how to make a second map
    _CONTINUE-HERE.md   the deep handover — read before touching the cage,
                        the crows, the truck or the metre

The raw Gemini sheets, the reference art and the music masters are **not here**.
They live in the Studio that made them, at
`Gemini Prompt Sender/dashboard/dgh/`, and are reachable from the DGH section of
the dashboard. `tools/paths.py` is what points the cut scripts at them.

## The character

A **painted head on a procedural body**. Hat, comb, face and beak are cut from a
Gemini render; body, wings, tail, legs and sneakers are drawn in code. That split
is why the wings can flap, the body can squash and ragdoll, and swapping the hat
is swapping one PNG. `chickens.html` is the picker.

## Scale

Distance is in metres: `UPM` is world units per metre and it is **60**. A screen
is about 22 m across and he covers 10 m/s off the line, 23 m/s flat out. Score is
one point per metre. Anything measured in metres is `* UPM`, never `* 10`.
