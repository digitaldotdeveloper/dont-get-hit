# How the art gets made

Everything you can see in this game that is not drawn with `ctx.lineTo` came
down the same road:

```
  a prompt in Gemini Studio          tools/gen_*.py, or the DGH section
        |                            of the Studio dashboard
        v
  a raw sheet on a flat key colour   -> dgh/sheets/vN/*.png   (the archive)
        |
        v
  a cut script                       tools/cut_*.py
        |                            keys the background out, splits the sheet,
        |                            trims, registers, writes lossless WebP
        v
  art/ and anim/                     what the game actually loads
        |
        v
  a few lines in index.html          a FRAME_DATA row, or a piece in OB
        |
        v
  a debug flag that proves it        ?ob=KEY  ?hit=1  ?obtest=1  ?ridetest
```

Nothing in that chain is clever. What makes it work is that **each stage is
allowed to be wrong and the next stage measures rather than assumes.** The
generator will not give you a loopable tile, four frames the same size, or a
sprite anchored where you need it — so the cut scripts search for the seam,
scale off a landmark, and find the tyre by casting rays. Read that as the
theme of this whole document.

---

## Where the sources live

The raw generations are **not in this folder**. They are 145 MB of PNG that the
game never loads, so they sit with the tool that made them:

```
C:\Users\it\Desktop\Gemini Prompt Sender\dashboard\dgh\
    sheets/v2   the farm: props, electric hardware, the barn, the truck, eggs
    sheets/v3   the parallax layers and the barn re-shoot
    sheets/v4   the crows
    ref/        the key art, and the references attached to prompts
    audio/      the 192 kbps music masters
    concept/    the pre-pivot human-runner concepts (kept for history)
    frames/     early sprite contact sheets
    anim_src/   pre-cut character frames
    art-unused/ cut art the shipped set no longer uses
```

`tools/paths.py` resolves that path; every `cut_*.py` reads from it and every
`gen_*.py` writes into it. Set `DGH_ARCHIVE` if the Studio ever moves. The same
folder is the **DGH section** in the Studio dashboard, so a sheet can be looked
at, re-cut or re-generated from one place.

This folder holds what ships plus the scripts that rebuild it: **11 MB**.

---

## The three rules the prompts obey

All of it was learned by getting it wrong first.

**1. The background is a flat key colour, and nothing in the art may be that
colour.** Sprites and props are asked for on `#00FF00`; parallax layers are
asked for on flat **magenta** instead. The colour is not the point — the point
is that *the game draws one sky behind everything*, so no layer ever has to
agree with another about what colour the sky is. The old three farm panels each
had their own painted sky, at three different blues, and they had to be
cross-faded into each other to hide it.

Magenta for the layers specifically because the farm palette contains green:
key green out of a field and you take the grass with it. Where a *character*
wears green (the cow's polo, the goat's hoodie), `tools/npc_frames.py` keys by
**growing in from the border** instead, which cannot reach anything enclosed by
a black outline.

**2. Exactly one thing per image, unless you are asking for a cycle.** Ask for a
"sheet of props" and the model quietly duplicates and varies the item, and the
pieces cannot be cut apart. Ask for a 2x2 flap cycle and say *the same bird,
same size, same angle, same colours, differing ONLY in the wings* — and it still
draws one cell smaller than the rest, which is what registration exists to fix.

**3. Say what the shape is, not what the mood is.** At phone size the silhouette
is the only thing that reads.

The standing style block, used verbatim everywhere so two frames cannot drift
apart:

> 2D side-scrolling mobile game sprite art, bold black outlines, flat cel-shaded
> colours, clean vector cartoon look, bright and saturated, no text, no
> watermark, no logo, no border, no frame, no grid lines.

---

## The one thing that separates a cycle from a set of props

**Registration.** A prop only has to be cut out. A frame in an animation has to
land in the same place as the frame before it.

Cutting each crow flap frame to its own bounding box and drawing them centred
made the bird lurch around the screen — because the box is mostly wing, and the
wing is the thing that moves. The fix is to find **the one feature that is
identical in every frame** and hang everything off that:

| cycle | the datum | why |
|---|---|---|
| crow flap | the open orange beak | the only part that never changes shape |
| truck poses | the axle line (red rims, found by fan of rays) | the tyres are what sit on the road |
| exhaust flame | the blunt root in the pipe | the tip whips about, the root does not |
| NPC walk/run | one shared ground line | a character trimmed to its own box bobs |

Each frame is scaled to the median size of that feature, then anchored on it.
`ay` in `FRAME_DATA` is that anchor, in pixels from the top of the frame.

**And if the motion has a rule, solve it instead of baking it.** The truck's
wheel is ONE image (`art/fx/wheel.webp`) spun off `game.dist` — exact at every
angle and every speed. Twelve baked frames would be bigger, blurry between the
stills, and wrong at any pace they were not timed for. Bake frames only for
things with no rule, like fire.

---

## What a map actually is

There is one map, Cluck County, and it is six things. To build a second one you
build a second set of these — not a timer that swaps the world out mid-run.

**1. `THEME`** (index.html, ~line 377). A palette object: five sky stops, sun,
three foliage greens, road and rim. The sky colours are **sampled off the
painted panels**, so the drawn sky and the sky in the art are the same blue and
the layers fade into it rather than sitting on it.

**2. Three parallax layers**, `art/bg/{far,mid,near}.webp`, declared in `BG`
with a parallax factor `f`, a height fraction `hf` and a `base` offset. Made by
`tools/gen_bg.py` (prompt → magenta field) and `tools/bg_layers.py` (key,
find the loop seam, tile). **Each layer has to loop**, and a generator will not
give you that: the seam is *searched for* by scoring columns near the right
edge against columns near the left.

**3. A prop set**, `art/farm/*.webp`, loaded on demand by `loadProp`. Generated
as sheets, cut by `tools/cut_obstacles.py` — which keeps the **N largest blobs**
rather than everything over a pixel floor, so a stray grass tuft at the foot of
a fence cannot shift the whole naming by one.

**4. Hazard pieces** in `OB`, built by `elecSpec` / `roadblock`. Each declares
its geometry in world units, which art it needs (`art:`), and a `free()` that
says where the safe air is. **Art a piece uses must be in its `art:` list or it
is never requested at all** — a missing prop image is a silent fallback by
design, so it will just draw as a flat block and never tell you.

**5. `PAT`**, the spawn table: tiers, and sequences with spacing **in seconds,
not pixels**. Obstacles are placed a fixed number of seconds ahead but arrive at
the screen edge, so as speed rises the reaction time falls as 1/speed.

**6. An intro.** The cage is `art/cage_scene.webp` + `art/cage_door.webp`, and
`CAGE` in index.html is a set of **fractions measured off the art**, printed by
`tools/cage_art.py`. That is what puts his feet on the straw instead of near it.

### Two rules that govern any hazard you add

- **Lethal everywhere it is solid; the opening is empty air.** In a side view a
  lethal upright is a wall for its whole height, so nothing draws a post across
  its own opening.
- **Never stack two hazards at the same x with a slot between them.** That is a
  keyhole: one answer, found in the fraction of a second before arrival. The
  `elecLadder` family was deleted for this. One-sided pieces staggered a beat
  apart in `PAT` instead — which moves the fairness question *between* two
  pieces, which is what `?obtest`'s `flyReach`/`transitOk` check now asks.

---

## The tools, in the order you would use them

**Generate** — these talk to Gemini Studio on `127.0.0.1:4321` via
`dashboard/client.py`. A render costs roughly **0.55% of the daily window**;
check Settings before queueing a pack.

| | |
|---|---|
| `gen_bg.py` | parallax layers, on magenta |
| `gen_crow.py` | the flap cycle + the badge head, on green |
| `gen_truckfx.py` | the wheel and the flame strip |

**Cut** — key, split, trim, register, write lossless WebP.

| | |
|---|---|
| `cut_farm.py` | rebuilds every farm + cage asset from `sheets/v2` |
| `cut_obstacles.py` | the prop and electric-hardware sheets (`--contact` for a numbered contact sheet) |
| `cut_crow.py` | the flap cycle, registered on the beak tip |
| `cut_truck.py` / `cut_truckfx.py` | the rig on its axle line; the wheel and flames |
| `cut_eggs.py` | the golden egg's spin from a painted turnaround |
| `npc_frames.py` | the cow/pig/goat sheets, keyed from the border |
| `bg_layers.py` | the three layers, cut to loop |
| `imglib.py` | the shared green key |

**Fix up** — the jobs the generator would not do.

| | |
|---|---|
| `build_apex.py` | reconstructs the barn's roof apex; Gemini would not zoom out far enough, three rounds running |
| `farm_seams.py` / `farm_strip.py` | search for where three panels should join, then join them once, offline |
| `thin_bales.py` | splices bale-free stretches into the near layer — **nothing is deleted**, so no inpainting is needed |
| `title_art.py` | extends the 16:9 key art into portrait title art |
| `to_webp.py` | lossless WebP + proves nothing changed (lossy rings on ink outlines and alpha edges) |
| `opt_audio.py` / `loop_menu.py` | Opus 64k + MP3 96k; cut the menu track to one loop of itself |

**Prove it** — because "it loads without throwing" is not "it is right".

| | |
|---|---|
| `probe.py` | run a `?...test=1` flag and report the panel |
| `obshot.py` | contact sheet of hazards, spawned in a real run (`--hit` draws the lethal boxes) |
| `crowshot.py` | the four moments of a crow attack |
| `clip.py` | a real-time GIF over `Page.startScreencast` — keeps the game's actual timing, which screenshot-per-frame does not |
| `shot.py` | CDP screenshot with real device metrics (`--screenshot` crops) |
| `prof.py` | ms/frame per draw section |
| `sfx.py` | renders every sound to WAV through `?sfx=1` and flags silent/clipping ones |
| `audio_report.py` | what is actually inside an MP3, with no ffmpeg on the box |

---

## Recipe: add a hazard

1. Write the prompt against the style block above, on flat green, **one object**.
   Queue it from the Studio's DGH section, or add it to a `gen_*.py`.
2. Sheet lands in `dgh/sheets/v2`. Cut it: `python tools/cut_obstacles.py --contact`
   and look at the numbered contact sheet — **the row order a sheet comes back in
   is not the order you asked for.**
3. Add the piece to `OB` with `elecSpec` or `roadblock`. List its art in `art:`.
4. `?ob=KEY` parks it on screen. `?hit=1` draws the lethal shapes over the art —
   the only way to check "the sprite fills its hitbox" rather than assert it.
5. Put it in `PAT` at a tier. `?obtest=1` checks openings, spacing, and whether
   the bird can transit from this opening to the next in the time you left him.
6. **Test it at its own tier's pace.** Obstacles are fixed world units and speed
   rises with `game.diff`; a standing-start test fails wide tier-2 pieces at a
   speed the player never meets them at. This looked exactly like a bad
   difficulty curve once and was not one.

## Recipe: a second map

1. New `THEME` object — sample the sky stops off the new panels.
2. `gen_bg.py` with new prompts → `bg_layers.py` → `art/bg2/{far,mid,near}.webp`.
   Keep the magenta field.
3. A prop sheet and an `art/<theme>/` folder; cut with `cut_obstacles.py`.
4. New pieces in `OB`, new rows in `PAT`. Obey the two hazard rules above.
5. A new intro scene if it needs one, with its fractions printed by a
   `cage_art.py`-shaped script rather than guessed.
6. Do **not** make the run travel between maps. That existed — a leg every 26s,
   farm → city → block, crossfaded — and all of it was deleted. A second map is
   its own THEME plus its own builder, chosen before the run starts.

---

## Things that will bite you

- **Measure loading against the CDN, not localhost.** Props used to queue behind
  all 129 character frames; the first prop landed at 20.2 s, so every hazard drew
  as a flat block for most of a run. Locally that is invisible. `IMQ` loads 6 at
  a time in three lanes for this reason.
- **A missing image is silent.** Every piece falls back to a drawn shape on
  purpose — art can never make a hazard invisible — which also means a typo in a
  filename shows up as "that obstacle looks a bit plain".
- **Reading anchor points off a grid by eye does not work.** Three of four
  truck exhaust anchors came out wrong that way. Draw a crosshair at the
  candidate point onto the art and look at whether it is on the metal.
- **Sound cannot be screenshotted.** `?sfx=1` + `tools/sfx.py` renders it. That
  is what caught the glide rustle at peak 0.005.
- **`git status` is only true at the instant you read it.** Other sessions have
  edited this folder mid-task more than once. Re-read the file and re-find your
  anchors right before patching, and never `git add -A`.
