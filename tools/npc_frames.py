# -*- coding: utf-8 -*-
"""Cut the green-screen NPC sheets into game frames.

   Each sheet is one character in six poses on a flat green field. Two things
   make this less trivial than a colour key:

   - **The characters wear green.** The cow's polo and the goat's hoodie are
     both green, so keying every green pixel strips their clothes. The
     background is keyed by growing in from the border instead, which cannot
     reach anything enclosed by a black outline.
   - **The frames are not evenly spaced.** They are cut on the empty columns
     between them, so a character keeps its own dust puff and nothing lands
     half in the next frame.

   Frames are trimmed horizontally but share one ground line, and `ay` records
   where that line sits in each frame -- so a pose that leaves the ground stays
   off the ground instead of being shoved back down onto it.

     python tools/npc_frames.py            # -> anim/<name>N.webp + frames.json
"""
import io, json, os, sys
from collections import deque
from PIL import Image

SHEETS = [                      # (file, set name, standing height in game px)
    ('ref/npc-cow-walk.png', 'cow',      164),
    ('ref/npc-cow-panic.png', 'cowrun',   164),
    ('ref/npc-pig-walk.png', 'pig',      156),
    ('ref/npc-pig-panic.png', 'pigrun',   156),
    ('ref/npc-goat-walk.png', 'goat',     160),
    ('ref/npc-goat-panic.png', 'goatrun',  160),
]
STEP = 46          # per-step tolerance while growing the background
GAP = 3            # a column with this many opaque pixels or fewer is a gap


def key_background(im):
    """RGBA with the green field grown away from the border."""
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()
    orig = im.copy().load()          # the field's own colour, before any keying

    def green(c):
        return c[1] > c[0] + 18 and c[1] > c[2] + 18

    seen = bytearray(w*h)
    q = deque()
    def seed(x, y):
        if not seen[y*w+x] and green(px[x, y]):
            seen[y*w+x] = 1; q.append((x, y, px[x, y]))
    for x in range(w): seed(x, 0); seed(x, h-1)
    for y in range(h): seed(0, y); seed(w-1, y)
    while q:
        x, y, c = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if not (0 <= nx < w and 0 <= ny < h) or seen[ny*w+nx]: continue
            d = px[nx, ny]
            if d[3] == 0 or not green(d): continue
            if abs(d[0]-c[0]) + abs(d[1]-c[1]) + abs(d[2]-c[2]) > STEP: continue
            seen[ny*w+nx] = 1; q.append((nx, ny, d))

    # Pockets: background trapped between an arm and a body, or under a raised
    # hoof, is not reachable from the border and survives the grow. Those are
    # the *sheet's own* green, so they can be keyed by colour against the
    # border's median -- which the cow's polo and the goat's hoodie are nowhere
    # near -- and only where the patch is small enough to be a gap rather than
    # a garment.
    ref = []
    for x in range(0, w, 7): ref.append(orig[x, 0]); ref.append(orig[x, h-1])
    for y in range(0, h, 7): ref.append(orig[0, y]); ref.append(orig[w-1, y])
    ref.sort(key=lambda c: c[1])
    bg = ref[len(ref)//2]
    def like_bg(c):
        return abs(c[0]-bg[0]) + abs(c[1]-bg[1]) + abs(c[2]-bg[2]) < 70
    lab = bytearray(w*h)
    limit = (w*h)//900                     # a pocket, not a shirt
    for sy in range(h):
        for sx in range(w):
            if lab[sy*w+sx] or px[sx, sy][3] == 0 or not like_bg(px[sx, sy]): continue
            comp, dq = [], deque([(sx, sy)])
            lab[sy*w+sx] = 1
            while dq:
                x, y = dq.popleft(); comp.append((x, y))
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = x+dx, y+dy
                    if (0 <= nx < w and 0 <= ny < h and not lab[ny*w+nx]
                            and px[nx, ny][3] and like_bg(px[nx, ny])):
                        lab[ny*w+nx] = 1; dq.append((nx, ny))
            if len(comp) <= limit:
                for x, y in comp: px[x, y] = (0, 0, 0, 0)

    # Despill: the last pixel before the key is half green, which reads as a
    # lime halo once the frame is over a dark background.
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if c[3] == 0: continue
            if c[1] > c[0] + 12 and c[1] > c[2] + 12:
                touching = any(0 <= x+dx < w and 0 <= y+dy < h and px[x+dx, y+dy][3] == 0
                               for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)))
                if touching:
                    g = (c[0] + c[2])//2
                    px[x, y] = (c[0], min(c[1], g + 10), c[2], c[3])
    return im


def columns(im, n=6):
    """The x ranges that hold each pose.

       Clean gaps first. On the running sheets there often are none -- the dust
       trail behind one animal reaches the next, and a couple of the walk poses
       throw an arm into their neighbour -- so the fallback puts a cut near each
       of the n-1 even divisions and slides it to the emptiest nearby column.
       Cutting through the thinnest part of a dust puff is invisible; cutting a
       character in half is not, and equal slices do exactly that."""
    w, h = im.size
    px = im.load()
    solid = [sum(1 for y in range(0, h, 2) if px[x, y][3] > 40) for x in range(w)]
    spans, start = [], None
    for x in range(w):
        if solid[x] > GAP and start is None: start = x
        elif solid[x] <= GAP and start is not None:
            if x - start > 12: spans.append((start, x))
            start = None
    if start is not None: spans.append((start, w))
    if len(spans) == n: return spans

    used = [x for x in range(w) if solid[x] > GAP]
    if not used: return spans
    lo, hi = used[0], used[-1] + 1
    step = (hi - lo)/float(n)
    cuts = [lo]
    for i in range(1, n):
        want = int(lo + i*step)
        rad = max(6, int(step*0.34))
        a, b = max(lo+1, want-rad), min(hi-1, want+rad)
        cuts.append(min(range(a, b), key=lambda x: (solid[x], abs(x-want))))
    cuts.append(hi)
    return [(cuts[i], cuts[i+1]) for i in range(n)]


def cut(sheet, name, height, out_dir='anim'):
    im = key_background(Image.open(sheet))
    spans = columns(im)
    if len(spans) != 6:
        print('  %-8s WARNING: found %d frames, not 6' % (name, len(spans)))
    full = im.getbbox()
    ground = full[3]                                  # one ground line for the set
    tallest = 0
    boxes = []
    for x0, x1 in spans:
        cell = im.crop((x0, 0, x1, im.height))
        b = cell.getbbox()
        boxes.append((cell.crop(b), b))
        tallest = max(tallest, b[3] - b[1])
    k = height/float(tallest)                          # one scale for the whole set
    meta = []
    for i, (frame, b) in enumerate(boxes):
        w2 = max(1, int(round(frame.width * k)))
        h2 = max(1, int(round(frame.height * k)))
        f = frame.resize((w2, h2), Image.LANCZOS)
        path = os.path.join(out_dir, '%s%d.webp' % (name, i))
        f.save(path, 'WEBP', quality=92, method=6)
        meta.append({'f': '%s%d.webp' % (name, i), 'w': w2, 'h': h2,
                     'ay': round((ground - b[1]) * k, 1),
                     'b': os.path.getsize(path)})
    print('  %-8s %d frames, %s' % (name, len(meta),
          ' '.join('%dx%d' % (m['w'], m['h']) for m in meta)))
    return meta


def main():
    js = 'anim/frames.json'
    data = json.load(io.open(js, encoding='utf-8'))
    for sheet, name, height in SHEETS:
        if not os.path.exists(sheet):
            print('  %-8s MISSING %s' % (name, sheet)); continue
        data['sets'][name] = cut(sheet, name, height)
    io.open(js, 'w', encoding='utf-8').write(json.dumps(data, indent=1))
    print('frames.json updated: %s' % ', '.join(sorted(data['sets'])))


if __name__ == '__main__':
    main()
