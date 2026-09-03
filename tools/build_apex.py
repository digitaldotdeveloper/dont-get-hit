"""Give the barn its missing roof apex.

Gemini would not zoom out far enough to fit the gable in frame - three rounds
came back with the same crop - so the apex is reconstructed instead.

The two roof edges ARE in the art, and measuring them says the real point is
412px above the top of a 572px image. Building that is useless: the doorway has
to stay a fixed size so Nugget stays a fixed size, and a barn that much taller
than its doorway simply will not fit a phone in landscape with him still
readable. So the ridge is brought down to a plausible gambrel peak instead --
the upper pitch steepens, which is what a gambrel roof does anyway. Nobody
measures a cartoon barn; everybody notices a building with its top sliced off.

The wedge is filled by smearing the wall upward, which is exactly right for
vertical planks, and the trim is drawn along the two edges with the art's own
colours sampled out of it.
"""
import os, sys, numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, r"C:\Users\it\Desktop\jj\tools")

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "sheets", "v2", "barn_raw.png")
PAD = 150                       # headroom added above the art, in source pixels
RIDGE = 118                     # how far above the art the peak sits

im = Image.open(SRC).convert("RGB")
a = np.asarray(im).astype(int)
H, W = a.shape[:2]
r, g, b = a[..., 0], a[..., 1], a[..., 2]
trim = (r > 185) & (g > 165) & (b > 120) & (r - b > 35) & (r - g < 60)


def band(y, side):
    xs = np.nonzero(trim[y])[0]
    if len(xs) < 4: return None
    runs, s, p = [], xs[0], xs[0]
    for x in xs[1:]:
        if x - p > 6: runs.append((s, p)); s = x
        p = x
    runs.append((s, p))
    runs = [q for q in runs if q[1] - q[0] > 8]
    if not runs: return None
    q = runs[0] if side == "L" else runs[-1]
    return (q[0] + q[1]) / 2.0, float(q[1] - q[0])


(Lc0, Lw), (Lc1, _) = band(8, "L"), band(64, "L")
(Rc0, Rw), (Rc1, _) = band(8, "R"), band(64, "R")
Ldx, Rdx = (Lc1 - Lc0) / 56.0, (Rc1 - Rc0) / 56.0
Lx0 = Lc0 - Ldx * 8                       # each edge where the art starts, y=0
Rx0 = Rc0 - Rdx * 8
print("left  x0=%.1f dx/dy=%.3f w=%.0f" % (Lx0, Ldx, Lw))
print("right x0=%.1f dx/dy=%.3f w=%.0f" % (Rx0, Rdx, Rw))
print("true apex would be %.0f px above the art" % ((Rx0 - Lx0) / (-Ldx + Rdx)))

apex_x = (Lx0 + Rx0) / 2.0 + (Lx0 - Rx0) / 2.0 * (Ldx + Rdx) / (Rdx - Ldx)
NH = H + PAD
ay = PAD - RIDGE

out = np.zeros((NH, W, 3), np.uint8)
out[PAD:] = a.astype(np.uint8)
out[:PAD] = a[0].astype(np.uint8)          # vertical planks: the top row IS the texture

# the gable: apex down to the edges where the painted art takes over
mask = Image.new("L", (W, NH), 0)
dm = ImageDraw.Draw(mask)
dm.rectangle([0, PAD, W, NH], fill=255)
dm.polygon([(apex_x, ay), (Rx0 + Rw, PAD + 2), (Lx0 - Lw, PAD + 2)], fill=255)

canvas = Image.fromarray(np.dstack([out, np.asarray(mask)]), "RGBA")
dr = ImageDraw.Draw(canvas)
TRIM = tuple(int(v) for v in a[trim].mean(0)) + (255,)
INK = (30, 22, 20, 255)
for x0, dx, w in ((Lx0, Ldx, Lw), (Rx0, Rdx, Rw)):
    dr.line([(apex_x, ay), (x0 + dx * 44, PAD + 44)], fill=INK, width=int(w) + 8)
for x0, dx, w in ((Lx0, Ldx, Lw), (Rx0, Rdx, Rw)):
    dr.line([(apex_x, ay), (x0 + dx * 44, PAD + 44)], fill=TRIM, width=int(w))
dr.ellipse([apex_x - Lw*0.6, ay - Lw*0.6, apex_x + Lw*0.6, ay + Lw*0.6], fill=TRIM, outline=INK, width=4)

canvas.save(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "sheets", "v2", "barn_apex.png"))
bg = Image.new("RGB", canvas.size, (60, 150, 240)); bg.paste(canvas, (0, 0), canvas)
bg.save("apex_preview.png")   # eyeball this before trusting it
print("apex at (%.0f, %.0f)   image now %dx%d" % (apex_x, ay, W, NH))

# the landmarks the game needs, re-expressed for the taller image
old = {"floor": 0.8811, "dx0": 0.3613, "dx1": 0.7129, "dy0": 0.2902, "dy1": 0.8392}
f = lambda v: (v * H + PAD) / NH
print("floorFrac %.4f  doorway fy %.4f..%.4f  fx %.4f..%.4f" %
      (f(old["floor"]), f(old["dy0"]), f(old["dy1"]), old["dx0"], old["dx1"]))
print("roof apex  fx %.4f  fy %.4f" % (apex_x / W, ay / NH))
