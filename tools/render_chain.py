# -*- coding: utf-8 -*-
"""Render a world's panels as ONE PLACE, each continuing the one before it.

    python tools/render_chain.py prison
    python tools/render_chain.py                 # every world with panels

Three things were tried to stop a join reading as a seam, and only this one
addresses the join itself:

  naming the palette   put a world on one set of colours. Necessary, not
                       sufficient: two renders of "pale grey breeze block" came
                       back warm grey and white subway tile.
  harmonise.py         moves the four panels onto one tone arithmetically. Fixes
                       the STEP IN BRIGHTNESS and cannot fix anything else.
  this                 attaches the previous panel and asks for the continuation.

Measured with `python tools/joins.py`, the first two left the joins stepping by
60-100 RMSE, because a wall that ends on a doorway beside a wall that starts on
a bench is not one wall however well the two agree about grey.

The chain runs left to right: panel 1 is rendered on its own, cut, and then
handed to panel 2 as the picture it must continue; panel 2 is cut and handed to
panel 3. Each link therefore needs the one before it FINISHED, so this is slow
by construction -- render, wait, cut, upload, render.

THE WRAP JOIN IS THE ONE THIS CANNOT FIX. The game cycles the panels in a ring,
so the last one is followed by the first again, and no left-to-right chain can
make both ends of a strip meet. That join stays tone-matched only, and joins.py
reports it like any other so it is never a surprise."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio                                   # noqa: E402
from gen_mid_panels import WORLDS, prompt_for, TOKEN        # noqa: E402
from render_panels import render, close_tabs, looks_signed_out   # noqa: E402
import cut_mid_panels as CUT                                # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cut_one(name):
    """Cut just this panel and return the file the game will load."""
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'cut_mid_panels.py'), name],
                       capture_output=True, text=True, encoding='utf-8')
    sys.stdout.write(r.stdout)
    f = os.path.join(CUT.dest_dir(name), name + '.webp')
    return f if os.path.exists(f) else None


def main():
    want = [a for a in sys.argv[1:] if not a.startswith('-')] or list(WORLDS)
    s = Studio(TOKEN)
    for world in want:
        names = sorted(WORLDS[world])
        print('%s: chaining %s' % (world, ' -> '.join(names)), flush=True)
        prev = os.path.join(ROOT, 'art', 'panels', world, names[0] + '.webp')
        if not os.path.exists(prev):
            print('  %s has no first panel yet; render it before chaining' % names[0])
            continue
        for name in names[1:]:
            try:
                ref = s.upload(prev)
            except Exception as e:
                print('  could not upload %s: %s' % (os.path.basename(prev), str(e)[:80]))
                return 1
            print('  %-4s continuing %s ...' % (name, os.path.basename(prev)), flush=True)
            ok, why = render(s, name, prompt=prompt_for(name, chained=True), attach=[ref])
            note = close_tabs(s, name)
            if note:
                print('       %s' % note)
            if not ok:
                print('  %-4s FAILED: %s' % (name, why))
                if looks_signed_out(why):
                    print('STOPPING -- the studio is signed out; only the user can clear that.')
                    return 1
                # the chain cannot skip a link: panel 4 must continue panel 3,
                # and continuing a panel that was never re-rendered would hand
                # it the OLD picture and quietly break the run it is reporting
                # as fine.
                print('  %s: chain stops here; %s and after are unchanged'
                      % (world, name))
                break
            f = cut_one(name)
            if not f:
                print('  %-4s cut produced nothing; chain stops' % name)
                break
            prev = f
        print('', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
