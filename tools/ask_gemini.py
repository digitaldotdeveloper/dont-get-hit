# -*- coding: utf-8 -*-
"""Ask Gemini to look at the game and say what is wrong with it.

    python tools/ask_gemini.py shot1.png shot2.png ... -- "the question"

The studio is used for GENERATING art everywhere else in this pipeline; this
uses it the other way round, as a second pair of eyes. It attaches real frames
and reads back the TEXT reply (`job.responseText`), which the studio has always
captured and nothing here had used.

Why bother: the audit checks construction -- edges, hue, seams, ramps -- and
passes a map that is technically clean and dull to look at. "Is this any good"
is not a property you can measure with numpy, and asking is cheaper than
guessing."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_mid_panels import TOKEN                             # noqa: E402

sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio                                    # noqa: E402


def main():
    args = sys.argv[1:]
    if '--' in args:
        i = args.index('--')
        shots, question = args[:i], ' '.join(args[i + 1:])
    else:
        shots, question = args, 'Critique these game screenshots.'
    s = Studio(TOKEN)
    attach = []
    for p in shots:
        attach.append(s.upload(p))
        print('attached', os.path.basename(p))
    before = {j['id'] for j in s.state()['jobs']}
    s.generate(question, mode='chat', runs=1, model='Pro', attach=attach)
    end = time.time() + 420
    while time.time() < end:
        for j in s.state()['jobs']:
            if j['id'] in before:
                continue
            if j.get('status') in ('done', 'failed'):
                txt = (j.get('responseText') or '').strip()
                print('\n--- status: %s ---\n' % j.get('status'))
                print(txt if txt else '(no text came back; error: %s)' % j.get('error'))
                try:
                    busy = [x for x in s.state()['jobs']
                            if x.get('status') in ('queued', 'running')]
                    if busy:
                        print('(tabs left open: %d other job(s) in the studio)'
                              % len(busy))
                    else:
                        s.close_thread(all=True)
                except Exception:
                    pass
                return 0
        time.sleep(6)
    print('timed out waiting for a reply')
    return 1


if __name__ == '__main__':
    sys.exit(main())
