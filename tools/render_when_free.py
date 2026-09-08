# -*- coding: utf-8 -*-
"""Wait until the Studio is nobody else's, then render a set of panels.

    python tools/render_when_free.py e1 e2 ...

The studio is shared. A product-cataloguing pipeline was using it, and 28
background panels fired into that queue would have taken their turn slowly,
timed out one by one against a five-minute patience, and slowed the other work
down for the privilege. So this waits for an EMPTY queue first -- other
people's jobs and mine alike -- and only then starts.

It does not jump the queue and it does not retry into a busy one: if the wait
expires it says so and renders nothing, because the alternative is discovering
an hour later that half a world is missing."""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_mid_panels import TOKEN                              # noqa: E402

sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio                                     # noqa: E402

WAIT_MAX = 90 * 60          # give the other pipeline an hour and a half
QUIET_FOR = 45              # ...and require the queue to stay empty this long,
                            # so a gap between two of its jobs is not mistaken
                            # for the end of it


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not names:
        raise SystemExit('name the panels')
    s = Studio(TOKEN)
    t0 = time.time()
    quiet_since = None
    while time.time() - t0 < WAIT_MAX:
        try:
            busy = [j for j in s.state().get('jobs', [])
                    if j.get('status') in ('queued', 'running')]
        except Exception as e:
            print('studio unreachable while waiting: %s' % str(e)[:80], flush=True)
            return 1
        if busy:
            quiet_since = None
            time.sleep(15)
            continue
        if quiet_since is None:
            quiet_since = time.time()
            print('queue empty, holding %ds to be sure...' % QUIET_FOR, flush=True)
        if time.time() - quiet_since >= QUIET_FOR:
            break
        time.sleep(5)
    else:
        print('the studio was still busy after %d minutes -- rendered nothing.'
              % (WAIT_MAX // 60))
        return 1

    print('studio is free after %.1f min; rendering %d panels'
          % ((time.time() - t0)/60.0, len(names)), flush=True)
    return subprocess.call([sys.executable,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         'render_panels.py')] + names)


if __name__ == '__main__':
    sys.exit(main())
