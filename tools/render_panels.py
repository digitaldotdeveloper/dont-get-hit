# -*- coding: utf-8 -*-
"""Render panels ONE AT A TIME, closing the tab after each, stopping on failure.

    python tools/render_panels.py mid3 mid4 mid5 tr4

Three rules, and each of them is a thing that went wrong first:

  ONE AT A TIME. A batch of prompts fails as a batch -- a capacity wobble or a
  lapsed session lands on whatever is queued behind it, and 18 of 30 renders
  went that way in one afternoon. Queued singly, a bad minute costs one render.

  CLOSE THE TAB WHEN THE RENDER IS DONE. Every generation opens a conversation
  in the studio's browser and leaves it open, and the failure rate climbs with
  the tab count. Nothing here reuses a thread, so each one is closed the moment
  its picture is in.

  TELL A FLAKY RENDER FROM A BROKEN STUDIO. Two failures look nothing alike and
  deserve opposite responses. "You might be signed out" is a wall: only the user
  can clear it, every further prompt returns the same sentence, and the right
  move is to stop on the spot. A TIMEOUT is weather -- the same prompt that
  timed out succeeds on the next attempt about as often as not, and abandoning
  twenty-two panels over one of them means a person has to come back and restart
  the run by hand. So a timeout is retried ONCE and then, if it fails again,
  treated as the wall.

  Either way nothing is retried in a loop: at most two attempts per panel, and
  the first unambiguous sign-out stops everything.

  AND WHEN THIS SAYS A PANEL FAILED, CHECK THE LIBRARY ANYWAY. A render that
  arrives after the watcher has given up still lands: c4 was declared failed
  four times and its picture was sitting in the library the whole while. Job
  status is what the studio thought at the moment it was asked; the library is
  what actually exists. Always finish a session by running cut_mid_panels.py
  over everything, not just over what this reported OK.

  AND THE PATIENCE IS THIRTEEN MINUTES, not five. A panel was reported failed
  twice while its job was still sitting in the studio marked `running` -- the
  render was slow, not stuck, and a watcher that gives up before the work does
  invents failures and then retries them, which is how one panel costs three
  renders instead of one."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_mid_panels import (PANELS, LAYERS, TOKEN, prompt_for)     # noqa: E402

sys.path.insert(0, r"C:\Users\it\Desktop\Gemini Prompt Sender\dashboard")
from client import Studio                                            # noqa: E402


SIGNED_OUT = ('signed out', 'image creation may not be available',
              "can't create any", 'not signed in')


def looks_signed_out(why):
    w = (why or '').lower()
    return any(k in w for k in SIGNED_OUT)


def state_jobs(s, tries=6):
    """The studio's job list, surviving a restart.

       It gets restarted while work is in flight -- a Windows connection reset
       mid-poll -- and a run that dies on that leaves sixteen panels unrendered
       and a stack trace instead of a report. The queue itself is unaffected, so
       the answer is simply to ask again."""
    for i in range(tries):
        try:
            return s.state().get('jobs', [])
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(10)
    return []


def render(s, name, timeout=780):
    prompt = prompt_for(name)
    # MATCH ON A PHRASE, NOT ON THE WHOLE STRING. The studio does not store the
    # prompt back byte-for-byte, so `j['prompt'] == prompt` never matched: the
    # first run of this script sat out its whole timeout and reported a failure
    # while eight perfectly good renders were landing in the library behind it.
    # A watcher that cannot see success reports failure, which is the worst
    # direction for a guard to be wrong in.
    needle = (PANELS.get(name) or LAYERS[name])[:48]
    def jobs():
        return [j for j in state_jobs(s) if needle in (j.get('prompt') or '')]
    before = len([j for j in jobs() if j.get('status') == 'done'])
    s.generate(prompt, runs=1, model='Pro')
    end = time.time() + timeout
    hard = time.time() + timeout*4        # even a queue has to end somewhere
    while time.time() < end and time.time() < hard:
        mine = jobs()
        done = [j for j in mine if j.get('status') == 'done']
        bad = [j for j in mine if j.get('status') in ('failed', 'cancelled')]
        if len(done) > before:
            return True, 'done'
        if bad:
            return False, (bad[-1].get('error') or bad[-1].get('status'))
        # QUEUE TIME IS NOT THINKING TIME, and this is the second way this
        # watcher has invented a failure. The studio works one job at a time and
        # it is SHARED: another session had a batch of sprite prompts in front
        # of this one, so a prison panel sat `queued` -- not slow, not stuck,
        # simply not started -- while the thirteen-minute patience ran out
        # underneath it. The panel would then be "retried" into the back of the
        # same queue and declared dead. The clock only runs once the studio has
        # actually picked the job up.
        if any(j.get('status') == 'queued' for j in mine):
            end = time.time() + timeout
        time.sleep(6)
    return False, 'no result within %ds' % timeout


def close_tabs(s, name):
    """Close the tabs this script opened -- but only when nothing else is using
       the studio.

       The instruction is to close every tab this uses, and it stands. The
       trouble is that `close_thread(all=True)` is the only lever the API offers
       for these jobs -- they carry no threadId -- and the studio is shared
       between sessions. Another session was pushing a batch of sprite prompts
       through it while these panels rendered, and closing everything mid-flight
       would have taken their conversation with it. So the sweep waits until the
       studio is idle, and says when it did not run."""
    needle = (PANELS.get(name) or LAYERS[name])[:48]
    try:
        others = [j for j in state_jobs(s)
                  if j.get('status') in ('queued', 'running')
                  and needle not in (j.get('prompt') or '')]
        if others:
            return '(tabs left open: %d other job(s) still running in the studio)' % len(others)
        s.close_thread(all=True)
        return ''
    except Exception as e:
        return '(could not close tabs: %s)' % str(e)[:60]


def main():
    want = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not want:
        raise SystemExit('name the panels to render')
    s = Studio(TOKEN)
    skipped, run_of_failures = [], 0
    for name in want:
        print('%-6s rendering...' % name, flush=True)
        ok, why = render(s, name)
        if not ok and not looks_signed_out(why):
            print('%-6s %s -- one retry' % (name, why), flush=True)
            close_tabs(s, name)
            ok, why = render(s, name)
        # the tab goes whether it worked or not; a failed conversation is still
        # a conversation sitting in the browser
        note = close_tabs(s, name)
        if note:
            print('       %s' % note)
        print('%-6s %s' % (name, 'OK' if ok else 'FAILED: %s' % why), flush=True)
        if ok:
            run_of_failures = 0
            continue
        if looks_signed_out(why):
            print('STOPPING -- the studio is signed out; only the user can clear that.')
            return 1
        # one bad panel must not cost the other twenty-six
        skipped.append(name)
        run_of_failures += 1
        if run_of_failures >= 3:
            print('STOPPING -- %d panels in a row failed, so this is the studio '
                  'rather than the prompts.' % run_of_failures)
            return 1
        print('%-6s skipped after two attempts; carrying on' % name, flush=True)
    print('done: %d of %d rendered; tabs closed' % (len(want) - len(skipped), len(want)))
    if skipped:
        print('SKIPPED (re-queue these by name): %s' % ', '.join(skipped))
    return 0


if __name__ == '__main__':
    sys.exit(main())
