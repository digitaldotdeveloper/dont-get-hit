# -*- coding: utf-8 -*-
"""Generate PANELS of the farm's middle distance -- the layer, not props on it.

    python tools/gen_mid_panels.py mid1 mid7      # queue just these
    python tools/gen_mid_panels.py --fetch        # pull what is ready

WHY PANELS AND NOT SET-PIECES. The first attempt at "make every 100m feel
different" was cut-out props on flat green, placed by metre and drawn at camera
parallax over the top of everything. They did not fit, and the reason is
structural rather than a matter of taste: a prop at parallax 1.0 crosses in
FRONT of a fence that is moving at 0.60, at full saturation, at a size set by
the road rather than by the horizon. The eye reads that as a sticker on a
photograph. The middle distance has to be made of middle distance.

So these are drawn to `art/bg/mid.webp`'s own spec, because they are shown
through the same slot as that painting and share its geometry:

  * MAGENTA #FF00FF key, not green. The game draws ONE sky behind every layer,
    so no layer may carry one -- and magenta specifically because the farm is
    full of green and keying green takes the fields with it.
  * ONE STRAIGHT GROUND LINE ALONG THE VERY BOTTOM EDGE. The slot anchors a
    panel by its bottom edge, so that line is what makes two panels meet.
  * EMPTY MARGINS LEFT AND RIGHT. These do not loop against themselves like
    the old single tile; each one sits between two others, and content running
    off an edge butts into whatever the next panel starts with.
  * NOTHING BLUE. Blue is the hazard colour in this game -- see the THEME note
    in index.html -- and the background is the last place to spend it.
  * ONE SCALE. Buildings about two thirds of the frame, so a barn is a barn in
    every panel. The cutter measures rather than trusting this, but a prompt
    that asks for it needs less correcting.

Panels are indexed, and the index IS the order you meet them in: mid1..mid5 are
the working farm, mid6..mid8 are it going wrong, which lines up with the ant
mounds already growing from 600m."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import sheets                                    # noqa: E402

sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio                                   # noqa: E402

TOKEN = os.environ.get('GEMINI_STUDIO_TOKEN',
                       '1a64c4bc884692a41e0bf84ed3fb4729a4a650484f264530')
OUT = sheets('v7')

STYLE = ("2D side-scrolling mobile game background art, bold black outlines, flat "
         "cel-shaded colours, clean vector cartoon look, bright and friendly, wide "
         "banner composition, no text, no watermark, no people, no animals. ")

ROW = ("MIDDLE LAYER ONLY. They stand side by side in a row on ONE STRAIGHT GROUND "
       "LINE along the very bottom edge of the image, evenly spaced with clear empty "
       "gaps between them, all the same distance away, all the same scale -- a red "
       "barn would be about two thirds of the image height. "
       "ONE ROW ONLY: do NOT stack a second row of buildings above them, nothing floats above the ground line, and there is empty background above everything. ")

EDGES = ("The far LEFT and the far RIGHT of the image are EMPTY FLAT MAGENTA for a "
         "wide margin and nothing touches either edge, because this picture is placed "
         "in a row beside other pictures like it. ")

MAGENTA = ("Everything that is not one of the described structures is SOLID FLAT "
           "MAGENTA #FF00FF, completely empty -- no sky, no clouds, no gradient, no "
           "hills, no fence, and no ground below the line. ")

NOBLUE = ("NOTHING in the artwork is blue, cyan, turquoise or teal -- no blue roofs, "
          "no blue paint, no blue shadows. Warm reds, browns, cream, straw yellow, "
          "weathered grey and rust only. ")

# The transition panels get a different composition clause from the farm ones,
# and tr3 is why: asked for "a barn half-buried by a mound" plus the ROW clause,
# the model drew that one motif THREE TIMES side by side. It is the documented
# failure -- ask for a row and you get duplicates -- and it is worse here than
# on a prop sheet, because a panel of three identical mounds is precisely the
# repetition these panels exist to remove. A transition panel is ONE SCENE.
# SAYING "LEAVE A MARGIN" IS NOT THE SAME AS SAYING "DO NOT CUT ANYTHING OFF",
# and the approach panels are where that difference shows. EDGES asks for empty
# magenta at the sides, and a mound is a shape that sprawls: the model obeys the
# margin around the picture and still draws the bank running out of frame, so
# the panel arrives ending in half a mound sliced by a straight vertical line.
# That is the fault reported from a screenshot three times. The cure is to name
# the object rather than the margin -- every thing in the picture is whole.
BOUNDED = ("EVERY OBJECT IN THE PICTURE IS COMPLETE AND FREE-STANDING. Each mound, shed, "
           "fence and tunnel is drawn WHOLE, with its far side visible, and none of them "
           "touches or runs off the left or the right side of the image -- nothing is cut "
           "in half by the edge of the picture. Draw the scene SMALLER if that is what it "
           "takes to fit all of it in with empty space at both sides. ")

SCENE = ("MIDDLE LAYER ONLY. This is ONE CONTINUOUS SCENE spread across the picture, "
         "NOT a row of repeated copies: each thing described appears exactly ONCE and "
         "they are all different from each other. Everything stands on ONE STRAIGHT "
         "GROUND LINE along the very bottom edge, all the same distance away, at the "
         "scale where a red barn is about two thirds of the image height. "
         "ONE ROW ONLY: do NOT stack a second row of buildings above them, nothing floats above the ground line, and there is empty background above everything. ")

PANELS = {
    # ---- the working farm ------------------------------------------------
    'mid1': "A small apple orchard: four round leafy fruit trees in a line, a stack of "
            "wooden fruit crates full of red apples, a wooden ladder leaning into one "
            "tree, and a small open-fronted fruit shed with a shingled roof.",
    'mid2': "A long open-sided pole barn stacked to the roof with golden straw bales, a "
            "smaller tractor shed with its doors open, and a wooden hay elevator on "
            "wheels standing beside them.",
    'mid3': "A two-storey cream farmhouse with a red shingled roof, a covered porch and "
            "a brick chimney; beside it a round stone well with a little roof and a "
            "bucket, a washing line of shirts on two poles, and a wooden dog kennel.",
    'mid4': "A low milking shed with a corrugated roof and a wide door, a wooden stand "
            "holding four steel milk churns, a long water trough, and a tall wooden hay "
            "rack half full of hay.",
    'mid5': "A machinery yard: a big harvester with a wide cutting reel, a plough with "
            "curved blades, a rusty fuel tank up on steel legs, and an open workshop "
            "shed with tools on the back wall.",
    # ---- and it going wrong ----------------------------------------------
    'mid6': "A row of four wooden chicken coops on legs with wire-mesh runs in front of "
            "them, sacks of feed stacked between them, and a small conical grain hopper "
            "on a frame.",
    'mid7': "A derelict corner of a farm: a leaning wooden windmill tower with two of "
            "its blades snapped off, a rusted pickup truck up on stacks of bricks with "
            "no wheels, three dented oil drums, and a collapsed shed with its roof "
            "caved in.",
    'mid8': "The farm being taken over from underneath: great mounds of crumbly brown "
            "earth pushed up between an old barn and a silo so that both lean, a broken "
            "post-and-rail fence, and two tall towers of small wooden crates lashed "
            "together with rope, with little ladders and tiny warm amber lanterns hung "
            "on them.",
}

# ---------------------------------------------------------------------------
# THE TRANSITION, and it is ORDERED rather than cycled.
#
# The farm does not become the ant empire at a line: it gets undermined. These
# four panels are the approach, and the run meets them in this order over the
# ~620m between the territory beginning and the tunnel mouth -- mounds in the
# field, then a shed shoved over, then the farm half-buried and built ON, then
# a wall of earth with the city already showing through it.
#
# This is where the anthills went after they were taken out of the lane. In the
# middle distance a mound is a landmark; at camera parallax on the ground line
# it is a hazard silhouette, which is what got them removed.
TRANSITION = {
    'tr1': "Three low mounds of crumbly red-brown earth pushed up out of a farm field, "
           "each with a dark round tunnel hole in it, standing between a small wooden hay "
           "shed and a leaning fence post; the buildings are still upright and the biggest "
           "mound is about half the height of the shed.",
    'tr2': "Big mounds of crumbly red-brown earth, the largest as tall as the wooden shed "
           "beside it and pushing that shed over so it leans hard; snapped fence rails, "
           "loose soil spilling across the ground, and three dark tunnel mouths.",
    'tr3': "A small red barn half buried and tilted over by a huge mound of earth, with an "
           "ant-built ramp of planks and small wooden crates lashed to the mound with rope, "
           "little ladders, tiny warm amber lanterns hung on posts, and several dark tunnel "
           "mouths at the foot of it.",
    # The first take ended in a razor-straight vertical cut where the picture
    # ran out, and a wall of earth that stops dead in mid-air reads as a
    # cropping error rather than a landform. So the bank is asked to come back
    # DOWN to the ground at both ends -- which is also what lets it sit beside
    # a farm panel without a step.
    'tr4': "A great bank of packed red-brown earth with pale tree roots threading "
           "through it, the broken tops of two farm fence posts and a buried cartwheel "
           "sticking out of it, and towers of small crates with tiny warm amber lanterns "
           "built up its face. The bank RISES TO A ROUNDED CREST in the middle of the "
           "picture and SLOPES BACK DOWN TO THE GROUND at both the left and the right "
           "ends, so no part of it is cut off by the edge of the image and it ends in "
           "soil rather than in a straight vertical line.",
}
PANELS.update(TRANSITION)


# ---------------------------------------------------------------------------
# THE REST OF THE RUN. Four panels per world, same frame and same rules as the
# farm's: one row, one ground line on the bottom edge, magenta key, empty
# margins, nothing blue. The world's own light comes from its THEME in
# index.html -- these are the things standing in it, not the lighting.
WORLDS = {
 'empire': {
  'e1': "A row of big rounded earth chambers in an ant city: one stacked with white sugar "
        "cubes, one with golden biscuit crumbs, a small wooden crane between them and a "
        "plank walkway across the top, warm lanterns hanging on hooks.",
  # The first take came back as a flat red RECTANGLE with shelves on it -- a
  # slab, not a chamber, and a rectangle in a world made of rounded earth reads
  # as a cut-out pasted on. So the SHAPE is now the first thing described and
  # the thing it must not be is named outright.
  # Re-rolled twice. First take was a flat red slab; second obeyed the shape but
  # the ROW clause drew the chamber twice. It is in SINGULAR now, and the rest
  # of the frame is described so there is something OTHER than the chamber for
  # the picture to contain.
  'e2': "ONE big rounded dome-shaped nursery chamber hollowed out of packed red-brown earth, its mouth a tall smooth arch, with three tiers of wooden shelves inside holding rows of pale cream eggs on straw and a ladder leaning between the tiers. The chamber is a ROUNDED MOUND with soft curved edges -- never a rectangle, never a flat wall. To its LEFT a stack of round straw bundles and a small wooden water trough; to its RIGHT a low earth bank with a rope handrail going up it and one hanging lantern on a post. The chamber appears ONCE and nothing in the picture is repeated.",
  # The rope hoist came back as an unreadable pole with a hook floating beside
  # the wheel. Named as a proper wooden crane with a visible arm instead: a
  # thing that reads at a glance beats a thing that is technically described.
  'e3': "An ant workshop in a rounded earth chamber: a huge wooden gear wheel standing in a "
        "timber frame, a wooden crane with a clear angled arm and a rope hanging from its "
        "tip holding a biscuit crumb, a rack of oversized tools behind them, and heaps of "
        "sawdust and timber offcuts on the ground.",
  'e4': "The queen's hall of an ant city: one tall arched earth chamber with a raised throne "
        "of packed earth and a red leaf canopy over it, tall lanterns either side, and two "
        "smaller arches beside it.",
 },
 'prison': {
  'p1': "A row of four prison cell fronts set into grey concrete: heavy vertical steel bars, "
        "a bunk and a bucket visible inside one, worn numbers stencilled over each door, a "
        "bare bulb on a wire above.",
  'p2': "A prison guard station: a barred gate standing open, a wooden desk with a lamp and "
        "a mug, a board of hanging keys, a filing cabinet and a swivel chair.",
  # Reworded after two straight timeouts while every panel either side of it
  # rendered first time. "Prison yard" and "razor wire" read as a content
  # trigger: the model answers in text and no image ever arrives, which reaches
  # the tool as a timeout and looks exactly like a broken studio. The silhouette
  # is what matters here, and a tall wall with coiled wire on top is the same
  # silhouette without the words.
  'p3': "A tall plain wall of grey breeze blocks with a few coils of wire along the very "
        "top, a floodlight on a tall pole beside it, a painted white line on the ground, "
        "and a battered grey metal door set into the wall.",
  'p4': "A prison canteen: two long steel tables with benches bolted down, a serving counter "
        "with trays and a steam tray, and fat steam pipes running along behind it.",
 },
 'cherno': {
  'c1': "A reactor hall wall: enormous grey pipes with flanged joints and big red valve "
        "wheels, a control panel of dials and levers, and a yellow and black hazard stripe "
        "along the base.",
  'c2': "An abandoned control room: a curved desk of dead screens and switches, two tipped "
        "office chairs, scattered papers, and a rack of gauges with cracked glass.",
  'c3': "The foot of two rusted concrete cooling towers, close up: peeling paint, a steel "
        "ladder up one, a fallen warning sign leaning against the base, weeds in the cracks.",
  'c4': "A corridor of heavy grey doors set into concrete, a stack of rusted metal drums "
        "with faded yellow markings stencilled on them, a small forklift with a flat tyre, "
        "and a grey instrument cabinet on the wall.",
 },
 'cia': {
  'b1': "A row of tall grey server racks with cable trays running overhead, a map table with "
        "a lit glass top between them, and coiled cables looping down the fronts.",
  'b2': "A supply store: steel lockers in a row, stencilled wooden crates stacked two high, "
        "a rack of hard hats and coiled rope, and a workbench with tools laid out on it.",
  'b3': "A secure corridor: three heavy grey doors with card readers and small windows, a "
        "camera on a bracket over each, and a stencilled floor stripe running past them.",
  'b4': "A briefing room: rows of folding chairs facing a big board of pinned photographs "
        "and a projector on a trolley, with a lectern to one side.",
 },
 'area51': {
  'a1': "A hangar interior: a large craft hidden under a heavy canvas tarpaulin on a wheeled "
        "cradle, two floodlights on tripod stands aimed at it, a rolling toolbox, and a "
        "gantry stair.",
  'a2': "The edge of a desert airstrip at night: three fuel drums, an open-top jeep, a "
        "windsock on a pole, a chain-link fence panel and a low sandbag wall.",
  'a3': "An aircraft maintenance bay: a steel gantry on wheels, a robotic arm on a pedestal, "
        "stencilled crates, and a rack of long tools.",
  'a4': "A radar dish on a wheeled trailer beside a small guard hut with a lit window, "
        "sandbags stacked around them and a generator on skids.",
 },
 'alien': {
  'x1': "A row of tall glass specimen tanks filled with glowing GREEN liquid, odd rounded "
        "shapes suspended in two of them, a console of switches between the tanks, and a "
        "cable bundle running along the floor.",
  'x2': "A laboratory bench room: a long steel bench under a big domed lamp, a tray of "
        "glassware on a stand, two screens on a trolley, and a wheeled sample cabinet.",
  # NEVER ASK FOR MAGENTA IN THE ARTWORK. The key deletes any bright pink or
  # purple pixel -- r>150, b>150, g<110 -- and then desaturates whatever purple
  # is left to a 190 alpha, because that is how the sky is removed. So "lit from
  # inside in MAGENTA" was an instruction to punch a hole through the middle of
  # the picture: x3 measured the emptiest panel in the whole map. It survived at
  # all only because the model drew a muted purple rather than the flat key
  # colour. Green is the accent these worlds actually get to keep.
  'x3': "A containment chamber: a thick curved glass wall in a heavy metal frame, lit from "
        "inside with a glowing GREEN light, an empty metal slab inside it, and a card panel "
        "beside the door.",
  'x4': "Alien machinery grown into the room: smooth curved organic shells of dull bronze, "
        "glowing GREEN conduits threading between them, and a ring of standing stones of "
        "metal.",
 },
 'space': {
  's1': "A launch gantry: a white rocket standing against a steel service tower with folded "
        "access arms, a flame trench at its foot, and floodlight masts either side.",
  's2': "A space station corridor: a row of round viewport windows showing BLACK space with "
        "a deep ORANGE and dull RED nebula and small warm stars, handrails along the wall, "
        "and equipment "
        "lockers between the windows.",
  's3': "A docking bay: a small shuttle on a cradle with its ramp down, stacked supply crates, "
        "a robotic loading arm, and a lit control booth.",
  's4': "A grey moon surface: a four-legged lander with a ladder, a small rover with wire "
        "wheels, a planted flag, and a cluster of instrument boxes, with low grey hills "
        "behind them.",
 },
}
for _w in WORLDS:
    PANELS.update(WORLDS[_w])


# ---------------------------------------------------------------------------
# AN INTERIOR IS NOT A ROW OF PROPS, and this clause is the fix for the single
# biggest thing wrong with the map.
#
# ROW says "evenly spaced with clear empty gaps between them". That is right for
# a farm -- you see sky between the barns -- and completely wrong for the inside
# of a prison. Rendered with it, every indoor world came back as four detached
# objects standing on a ground line with the sky wash showing between them: cell
# doors with no wall around them, a desk, a filing cabinet, a lectern. Butt those
# four panels together (tools/joins.py draws exactly that strip) and you get
# furniture floating in a void. Nothing was BROKEN -- the cut is clean, the key
# is clean, the blend works -- it just looks cheap, and no amount of edge-fading
# fixes props standing in nothing. Asked to judge real frames, Gemini called it
# "an unpolished asset flip", and it was reading this clause's output.
#
# An interior has to read as ONE CONTINUOUS SPACE with things set INTO it, and it
# needs somewhere for the eye to go PAST the front plane -- a recess, a lit
# opening -- or it is still a flat wall of stickers. Both halves matter: the
# first stops the gaps, the second stops it reading as a painted backdrop.
INTERIOR = ("MIDDLE LAYER ONLY, and this matters more than any single object listed: this "
            "is the INSIDE of a place and must read as ONE CONTINUOUS SPACE. A back wall "
            "runs UNBROKEN from the far left of the artwork to the far right, standing "
            "from the ground line up to at least two thirds of the image height, and "
            "everything described is SET INTO that wall or BUILT AGAINST it -- recessed "
            "doorways, alcoves, mounted fittings, built-in shelving. There are NO gaps of "
            "empty background between the things and NOTHING stands alone in space. "
            "DEPTH: put at least one darker RECESS or lit opening in the wall that the eye "
            "can see back into, and run one pipe, beam, cable or rail across in FRONT of "
            "it, so the picture has a front, a middle and a back instead of one flat "
            "plane. Each thing described appears exactly ONCE. ")

# EDGES IS THE WRONG RULE FOR A WALL, and this is its opposite.
#
# EDGES asks for empty magenta margins so a panel can sit beside a different
# panel without their contents colliding, and the cutter enforces a 4% gap on
# top of that. Correct for a farm: two barns should not touch. But panels BUTT
# in the game -- the draw loop steps by exactly one panel width -- so on an
# interior those margins are a hole punched through the wall to the sky every
# time one panel ends, which is the "walls suddenly appear" seam reported from
# a screenshot. A wall has to be CUT OFF by the frame and continue into the
# next picture, and the two ends have to meet at the SAME HEIGHT or the join
# steps. That height is named outright rather than left to the model, because
# four panels are rendered independently and nothing else makes them line up.
JOIN = ("The back wall REACHES BOTH the far LEFT edge and the far RIGHT edge of the image "
        "and is CUT OFF by them -- this picture is placed in a row beside other pictures of "
        "the SAME wall and it must run on into them, so do NOT leave an empty margin and do "
        "NOT finish the wall with a corner or a return. The TOP of the wall is a STRAIGHT "
        "HORIZONTAL line at exactly TWO THIRDS of the image height, at the same height where "
        "it meets the left edge and where it meets the right edge. ")

# The outdoor panels of the later worlds have the opposite problem and a milder
# fix: gaps between things are FINE at night in a desert, what is not fine is a
# ground line that stops. So they keep SCENE's one-of-each rule and gain a
# continuous mass along the back to sit against.
OUTDOOR = (SCENE + "The GROUND runs unbroken from the far LEFT edge of the artwork to "
           "the far RIGHT edge and is CUT OFF by them, and a continuous mass of land -- "
           "dunes, banked earth, distant hills -- runs along behind everything and also "
           "reaches BOTH edges, so the picture never shows a hole straight through to "
           "nothing and can be placed beside another picture of the same place. The land "
           "meets the left edge and the right edge at about the SAME HEIGHT. ")

# ONE WORLD, ONE PALETTE -- and this only became a fault once the walls joined up.
#
# While every panel was an object floating on the sky wash, the wash separated
# them and it did not matter that the guard station was cream and the canteen
# was red: you never saw the two touch. Butt them into a continuous wall and the
# mismatch is the loudest thing in the frame -- four rooms from four different
# buildings, with a hard vertical colour step at every join. Fixing the gaps
# created this, which is worth writing down: the panels were always this
# inconsistent, the gaps were hiding it.
#
# Four panels are rendered independently and nothing else makes them agree, so
# the colours are named per world rather than left to the model, the same way
# the wall height is.
PALETTE = {
 'empire': "packed red-brown earth, dark timber, pale straw and warm amber lantern light",
 'prison': "warm neutral grey concrete and pale grey breeze block with NO blue tint of any "
           "kind and NO blue-grey, dull grey-green steel doors, brown rust stains and warm "
           "amber lamp light -- NO cream or white walls, NO red walls",
 'cherno': "grey concrete, olive green, orange rust, faded yellow markings and dull steel "
           "-- NO cream or white walls",
 'cia':    "warm grey-brown concrete, olive drab, dull grey steel, stencilled yellow and "
           "warm amber lamp light -- NO cream or white walls, NO red walls",
 'area51': "sand beige, grey steel, olive drab and warm amber work lights",
 'alien':  "dull bronze, near-black metal, glowing green and warm amber accents",
 'space':  "off-white wall panelling, grey steel, warm amber lights and black space",
}
WORLD_OF = {n: w for w in WORLDS for n in WORLDS[w]}

# WHICH PANELS ARE INSIDE SOMETHING. Named one at a time rather than by world,
# because two worlds are mixed: Area 51 is a hangar and a maintenance bay INDOORS
# and an airstrip and a radar dish OUTSIDE, and the space set is a corridor and a
# docking bay indoors against a launch pad and a moon surface out in the open.
INTERIORS = set(list(WORLDS['empire']) + list(WORLDS['prison']) + list(WORLDS['cherno'])
                + list(WORLDS['cia']) + list(WORLDS['alien']) + ['a1', 'a3', 's2', 's3'])
OUTDOORS = {'a2', 'a4', 's1', 's4'}


# ---------------------------------------------------------------------------
# THE FLOOR AND THE CEILING. These are not panels -- they are the world's own
# looping TILES, so they obey the opposite composition rule to everything
# above: their left and right edges must MATCH, because each one is tiled
# against itself forever rather than placed beside a different picture.
#
# `near` is the band along the bottom the player runs past, closest and
# fastest. `hang` drops from the top and is the only slot in the game anchored
# to the ceiling -- and it carries the rule that outranks every reference
# image: the top stays OPEN. Things dangle into frame with air between them,
# because Nugget flies up there and a roof drawn across it forbids the exact
# space the whole control scheme is about.
LOOPS = ("The LEFT EDGE and the RIGHT EDGE must match in height and content so the image "
         "can repeat seamlessly side by side forever. ")

# "About a quarter of the image height" is what the first pass asked for, and it
# is a trap: the game scales this tile BY ITS HEIGHT, so a thin band of pixels
# gets magnified to fill the floor. alien_near came back 33px tall and would
# have been stretched about twelvefold. The band needs to be a big share of the
# picture, because the picture is only ever as good as the pixels in the band.
NEAR_SHAPE = ("This is a NEAR FOREGROUND STRIP seen close up: it fills the BOTTOM HALF of "
              "the image, full width, edge to edge, with strong saturated colour and heavy "
              "black outlines and plenty of detail in it. Only the top half of the image is "
              "empty. ")

HANG_SHAPE = ("ONLY things hanging DOWN from the top edge of the image, each hanging "
              "separately with WIDE EMPTY GAPS between them and nothing joining them across "
              "the top. Each shape stops well before the bottom, and the BOTTOM HALF of the "
              "image is completely empty. ")

# THE BACK OF THE SCREEN, and until now there was only one of it.
#
# Every world past the empire owned its floor and its ceiling and nothing else,
# on the reasoning that "the haze behind it is the same cavern seen from the
# same distance". That reasoning is why the run reads as one place with the
# props changing -- which is exactly the complaint: "the background dont change,
# the scene still the same and just the props change". The far slot is the
# largest area on screen and it held ONE picture from the empire to the end of
# the run, over three thousand metres.
#
# A far tile is a SILHOUETTE. It sits at f=0.10, barely moving, behind
# everything, and it is the wrong place for detail: what it has to do is give
# each world a different skyline.
FAR_SHAPE = ("This is the FAR DISTANCE seen through thick haze. Draw it as SIMPLE FLAT "
             "SILHOUETTE SHAPES in ONE OR TWO muted, pale, desaturated colours, with NO "
             "black outlines, NO small details, NO texture and NO lighting -- only the "
             "outline of the shapes matters at this distance. The shapes make a CONTINUOUS "
             "band standing along the BOTTOM of the image, full width, edge to edge, with "
             "an uneven skyline of different heights across it; the top third of the image "
             "is completely empty. ")

LAYERS = {
 # A flat floor is a thin band however firmly the shape clause asks for half
 # the picture -- there is simply nothing tall in "concrete". So this one is
 # given something with HEIGHT in it: a low wall along the back of the strip.
 # The tile is scaled by its height, so the art has to contain some.
 'prison_far':  "a distant block of stacked cell galleries three tiers high with narrow "
                "walkways along them, and one taller square watchtower to one side",
 'cherno_far':  "distant wide cooling towers with sloped waists, a tall chimney stack, and a "
                "low tangle of pipework and gantries between their feet",
 'cia_far':     "a distant back wall of tall equipment cabinets and a raised gantry walkway "
                "crossing in front of it, with two square vent housings above",
 'area51_far':  "a distant row of huge rounded hangar doors, a square control tower with a mast, "
                "and low flat-topped desert mesas behind them",
 'alien_far':   "distant smooth organic arches and tall tapering spires with rounded tops, "
                "growing into each other like a coral reef",
 'space_far':   "the distant far wall of a station hangar with one huge open bay door, a docked "
                "craft on a cradle in silhouette and two gantry towers",
 'prison_near': "a low wall of grey breeze blocks running along the back at about waist "
                "height with chipped paint and a dark stain down it, a worn concrete floor in "
                "front of it with a painted white line, two square drain grates, and a "
                "battered metal bucket standing against the wall",
 'prison_hang': "caged ceiling bulbs on short chains, lengths of grey electrical conduit with "
                "elbow joints, and one long loose chain",
 'cherno_near': "a strip of cracked grey concrete floor with weeds pushing through the cracks, "
                "scattered rubble and broken tile, a fallen yellow warning sign lying flat, "
                "and a rusted pipe half buried in it",
 'cherno_hang': "torn hanging cables, a broken square ventilation duct with its end open, one "
                "cracked emergency lamp with a wire cage, and loose strips of peeling ceiling",
 'cia_near':    "a strip of riveted dark metal floor plating with a yellow stencilled edge "
                "line, a low cable tray full of cables running along it, and two flush floor "
                "hatches with recessed handles",
 'cia_hang':    "long rectangular ceiling strip lamps glowing warm, bundles of cables looping "
                "down, a square duct coming down and turning, and one small camera on a bracket",
 'area51_near': "a strip of pale desert sand meeting the edge of grey tarmac, with a painted "
                "yellow runway marking, small rocks, a low sandbag row and tyre tracks",
 'area51_hang': "heavy steel hangar roof trusses seen from below with chains hanging from "
                "them, two big floodlights on brackets, and a hanging hook block",
 # The first take came back with RED-ROOFED WOODEN SHEDS and a straw bale on
 # it -- farm buildings, in an alien facility, repeating along the floor every
 # tile. Context bleed from the farm prompts earlier in the same session is the
 # likeliest cause, so the things it must not contain are now named: a
 # generator that has just drawn twenty barns needs telling.
 'alien_near':  "the polished interior floor of an alien facility: dark tiles with thin glowing "
                "GREEN seams between them, two round metal floor ports lit from below in green, "
                "a low bronze skirting with smooth organic curves along the back, and a scatter "
                "of small green-lit studs. Absolutely NO wooden buildings, NO barns, NO sheds, "
                "NO straw and NO farm structures of any kind -- this is a smooth indoor floor "
                "and nothing stands on it",
 'alien_hang':  "smooth curved organic bronze tendrils hanging down, thin glowing GREEN "
                "conduits threading between them, and one bell-shaped hanging lamp glowing "
                "warm amber",
 # FLOOR VARIANTS. One tile per world repeated forever is the most obvious
 # repeat in the game -- the floor runs at f=0.60, the fastest thing on screen,
 # so the same rocks come round twice a frame. Each world gets two more, and
 # they are written as the SAME strip with different things lying on it rather
 # than as different floors: the ground has to stay continuous across a join.
 'farm_near2':   "a strip of green farm grass verge, thick and tufty along the whole back, "
                 "with a worn bare patch of brown earth in the middle of it, a fallen wooden "
                 "fence rail lying in the grass and a scatter of small stones",
 'farm_near3':   "green farm grass along the whole back of the strip with little yellow and "
                 "white wildflowers in it, loose straw scattered over the grass, a dropped "
                 "wooden bucket on its side and a shallow tractor rut of brown earth",
 'empire_near2': "a strip of packed red-brown earth floor with pale root threads in it, two "
                 "small round tunnel mouths at the back, scattered crumbs of biscuit and a "
                 "spilled heap of sugar grains",
 'empire_near3': "a strip of packed red-brown earth floor with a LOW EARTH BANK standing along "
                 "the whole back of the strip at knee height, pale root threads hanging out of "
                 "it, a broken wooden crate slat leaning against it and a scatter of seed husks",
 'prison_near2': "a strip of worn concrete floor with a painted white line, a square drain "
                 "grate, a scrubbing brush and a coiled hose against a low breeze block wall "
                 "at the back",
 'prison_near3': "a strip of worn concrete floor with a long crack running through it, two "
                 "chipped floor tiles, a dropped tin mug and a low breeze block wall at the back",
 'cherno_near2': "a strip of cracked grey concrete with weeds in the cracks, a fallen length "
                 "of rusted handrail, a scatter of broken tile and a shallow puddle",
 'cherno_near3': "a strip of cracked grey concrete with a LOW BROKEN CONCRETE KERB WALL standing "
                 "along the whole back of the strip at knee height, a toppled rusted drum lying "
                 "against it, loose rubble and dry weeds",
 'cia_near2':    "two flush floor hatches with recessed handles set into riveted dark metal "
                 "plating, a coiled cable loom beside them, a yellow stencilled edge line and "
                 "a low kick plate along the back",
 'cia_near3':    "an open inspection hatch lying back on its hinge in a floor of riveted dark "
                 "metal plating, rows of bolt heads, a scatter of dropped tools and a low kick "
                 "plate along the back",
 'area51_near2': "a strip of pale desert sand meeting grey tarmac with a painted yellow "
                 "marking, tyre tracks, a low sandbag row and two small rocks",
 'area51_near3': "a strip of pale desert sand with dry scrub tufts, a half-buried tyre, "
                 "wind-blown ripples and a scatter of pebbles",
 'alien_near2':  "one round floor port lit from below in GREEN, set into an alien floor of DARK "
                 "BRONZE-BROWN and near-black tiles with thin glowing green seams running "
                 "between them, and a low bronze skirting along the back. The tiles are BROWN "
                 "and BLACK -- never blue, never navy, never indigo, never grey-blue. NO wooden "
                 "buildings, NO barns, NO straw",
 'alien_near3':  "an alien facility floor running the full width: DARK BRONZE-BROWN and "
                 "near-black tiles with thin glowing GREEN seams between them, three small "
                 "green-lit studs set flush in the floor, and a low bronze skirting standing "
                 "along the whole back of the strip. It is a FLAT FLOOR seen close up, not one "
                 "big round object. The tiles are BROWN and BLACK -- never blue, never navy. "
                 "NO wooden buildings, NO barns, NO straw",
 'space_near2':  "a bolted-down equipment crate standing on dark metal grating floor, yellow "
                 "and black hazard chevrons along the edge of the grating, a recessed light and "
                 "a low tubular rail along the back",
 'space_near3':  "a strip of dark metal grating floor with a circular access hatch, hazard "
                 "chevrons along its edge and a low tubular rail with a coiled tether on it",
 'space_near':  "a strip of dark metal grating floor with yellow and black hazard chevrons "
                "along its edge, two recessed lights, and a low rail of tubular steel",
 'space_hang':  "docking clamps and folded robotic arms hanging down, bundled cables, one "
                "wide spotlight on a bracket, and a short ladder hanging from the top",
}


# WHICH CLAUSE A PANEL GETS IS A PROPERTY OF ITS SUBJECT, not of which group
# it happens to sit in. "They stand side by side in a row" is exactly right for
# a row of chicken coops and exactly wrong for one chamber: asked for a nursery
# with the row clause, the model drew the nursery TWICE. Anything singular goes
# in here and gets the scene clause instead.
SINGULAR = {'e2', 'e4'}


# WHAT MAKES TWO PANELS ONE PLACE, and it is the thing tone-matching cannot do.
#
# Naming the palette got each world onto one set of colours, and harmonise.py
# closed the rest of the gap arithmetically. Neither makes the WALL line up:
# panel three still ends on a doorway and panel four still starts on a bench,
# because they were painted by two renders that never saw each other. Measured,
# the joins were still stepping by 60-100 RMSE after both fixes.
#
# So the previous panel is ATTACHED and the new one is asked to carry on from
# it. This is the same trick the character sheets use to keep one chicken across
# forty sprites, pointed at a wall instead of a bird.
CONTINUE = ("The ATTACHED PICTURE is the scene immediately to the LEFT of the one you are "
            "drawing, and your picture must continue it EXACTLY. Your LEFT edge carries on "
            "from the attached picture's RIGHT edge: the same wall at the same height, the "
            "same colours, the same materials, the same floor line and the same lighting, "
            "so that placing the two side by side reads as ONE UNBROKEN PLACE with no seam. "
            "Do NOT redraw or repeat what is in the attached picture -- continue past it "
            "with the new things described below. "
            "CRITICAL: the wall in your picture is EXACTLY as TALL as the wall in the "
            "attached picture -- its top is the same straight horizontal line at two thirds "
            "of the image height, running the full width and reaching both edges. Do not "
            "lower it, do not raise it, do not leave a gap of empty background above the "
            "wall at either edge. ")


NEEDLE = 48


def _check_needles():
    seen = {}
    for name in list(PANELS) + list(LAYERS):
        key = (PANELS.get(name) or LAYERS[name])[:NEEDLE]
        if key in seen:
            raise SystemExit(
                'PROMPT COLLISION: %s and %s both begin "%s". '
                'The library is searched by that phrase, so both names resolve to the '
                'same render and one picture is written into two files. Reword one of '
                'them so the first %d characters differ.' % (seen[key], name, key, NEEDLE))
        seen[key] = name


_check_needles()


def prompt_for(name, chained=False):
    """The full prompt for any name in PANELS or LAYERS -- one source of truth,
       because the composition rules differ per KIND and a caller that
       assembles its own prompt will eventually assemble the wrong one."""
    if name in LAYERS:
        shape = (HANG_SHAPE if name.endswith('_hang') else
                 FAR_SHAPE if name.endswith('_far') else NEAR_SHAPE)
        return (STYLE + 'A seamless side-scrolling background layer showing ' +
                LAYERS[name] + '. ' + shape + LOOPS + MAGENTA + NOBLUE)
    if name in INTERIORS:
        pal = ('COLOURS: the whole picture is painted in %s. '
               % PALETTE[WORLD_OF[name]])
        cont = CONTINUE if chained else ''
        return (STYLE + PANELS[name] + ' ' + INTERIOR + JOIN + pal + cont
                + MAGENTA + NOBLUE)
    if name in OUTDOORS:
        pal = 'COLOURS: the whole picture is painted in %s. ' % PALETTE[WORLD_OF[name]]
        return STYLE + PANELS[name] + ' ' + OUTDOOR + pal + MAGENTA + NOBLUE
    comp = SCENE if (name in TRANSITION or name in SINGULAR) else ROW
    bound = BOUNDED if name in TRANSITION else ''
    return STYLE + PANELS[name] + ' ' + comp + EDGES + bound + MAGENTA + NOBLUE


def main():
    want = [a for a in sys.argv[1:] if not a.startswith('--')] or list(PANELS)
    bad = [w for w in want if w not in PANELS]
    if bad:
        raise SystemExit('unknown panel(s): %s; have %s' % (', '.join(bad), ', '.join(PANELS)))

    s = Studio(TOKEN)
    os.makedirs(OUT, exist_ok=True)
    if '--fetch' not in sys.argv:
        print('quota before: %s' % s.usage().get('current'))
        for name in want:
            print('queueing %s ...' % name)
            # ONE take each. The last round burned a day's window on three
            # takes of ten prompts and half of them failed on capacity anyway;
            # a panel that comes back wrong is cheaper to re-queue by name.
            s.generate(prompt_for(name), runs=1, model='Pro')
        print('queued %d panel(s). Run with --fetch, or cut with '
              'tools/cut_mid_panels.py' % len(want))


if __name__ == '__main__':
    main()
