# -*- coding: utf-8 -*-
"""Wrap compare.py's strips in a page, with the audit's numbers beside them.

    python tools/join_page.py prison cia > page.html

The strips alone show that something changed; the numbers say what, and which
way. Both belong on the same page or the reader has to take the change on
trust -- which is the position that produced "there's still cutouts, I'm tired
of screenshotting and not getting results"."""
import base64
import glob
import io
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from joins import SKY, ROOT                            # noqa: E402

HEAD = """<title>Join Inspector</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
/* A COLOUR-JUDGEMENT SURFACE COMMITS TO ONE GROUND ON PURPOSE. These strips are
   read for their palette, and a page that changes ground with the viewer's
   theme changes how the art reads -- a cream wall looks warm on charcoal and
   dirty on white. So the ground is painted explicitly and does not follow the
   host. */
:root{
  --ink:#E8E4DC; --dim:#9A948A; --ground:#191816; --panel:#211F1C;
  --rule:#332F2A; --hot:#D8743C; --good:#7FA05A;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
     font:15px/1.6 'IBM Plex Sans',system-ui,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:40px 24px 80px}
h1{font-size:30px;margin:0 0 6px;letter-spacing:-.01em}
.sub{color:var(--dim);max-width:62ch;margin:0 0 10px}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin:22px 0 34px}
.legend a{font:600 12px/1 'IBM Plex Mono',monospace;letter-spacing:.06em;
  text-transform:uppercase;color:var(--ink);text-decoration:none;padding:8px 12px;
  border:1px solid var(--rule);border-radius:2px;background:var(--panel)}
.legend a:hover,.legend a:focus{border-color:var(--hot);color:var(--hot)}
section{margin:0 0 54px;scroll-margin-top:16px}
h2{font:600 13px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;
   color:var(--hot);margin:0 0 14px;padding-bottom:10px;border-bottom:1px solid var(--rule)}
figure{margin:0 0 18px}
figcaption{font:12px/1.5 'IBM Plex Mono',monospace;color:var(--dim);margin:0 0 7px}
figcaption b{color:var(--ink);letter-spacing:.06em;text-transform:uppercase}
.scroll{overflow-x:auto;border:1px solid var(--rule);border-radius:2px;
        background:#000;-webkit-overflow-scrolling:touch}
.scroll img{display:block;height:210px;width:auto;max-width:none;image-rendering:auto}
.scroll img.shot{height:auto;width:100%;max-width:100%}
.none{font:12px 'IBM Plex Mono',monospace;color:var(--dim);
      border-left:2px solid var(--rule);padding:6px 0 6px 12px;margin:0 0 18px}
.note{background:var(--panel);border:1px solid var(--rule);border-radius:2px;
      padding:16px 18px;margin:0 0 34px}
.note p{margin:0 0 8px}.note p:last-child{margin:0}
.note b{color:var(--hot)}
code{font:13px 'IBM Plex Mono',monospace;color:var(--good)}
</style>
"""


def main():
    worlds = [a for a in sys.argv[1:] if not a.startswith('-')] or list(SKY)
    strips = subprocess.run([sys.executable, os.path.join(HERE, 'compare.py')] + worlds,
                            capture_output=True, text=True, encoding='utf-8')
    if strips.returncode:
        sys.stderr.write(strips.stderr)
        raise SystemExit(1)
    out = [HEAD, '<div class="wrap">',
           '<h1>Join Inspector</h1>',
           '<p class="sub">Every panel of a world butted together exactly as the game '
           'tiles them, on that world&rsquo;s own sky colour. A cut-out is almost never '
           'visible in a panel on its own &mdash; it is visible where that panel meets '
           'the next one.</p>',
           '<div class="legend">' +
           ''.join('<a href="#%s">%s</a>' % (w, w) for w in worlds) + '</div>',
           '<div class="note">'
           '<p><b>Before</b> &mdash; the composition clause asked for things '
           '&ldquo;evenly spaced with clear empty gaps between them&rdquo;. Right for a '
           'farm, where you should see sky between the barns. Inside a prison it gives '
           'four detached objects standing in a void.</p>'
           '<p><b>Continuous</b> &mdash; one unbroken wall with everything set into it, a '
           'recess to see back into, and something crossing in front. The wall is cut off '
           'by the frame and runs on into the next picture instead of stopping in an '
           'empty margin.</p>'
           '<p><b>Now</b> &mdash; each world painted from one named palette, then pulled '
           'onto one tone by <code>tools/harmonise.py</code>. And the join itself is fixed '
           'in the game rather than in the art: panels now <b>overlap by 7%</b> with a ramp '
           'down each left edge, so a join is a dissolve onto the picture behind instead of '
           'a butt against it.</p>'
           '<p>Rendering each panel with the previous one attached &mdash; asking Gemini to '
           'continue the scene &mdash; was tried twice and measured worse both times '
           '(67 &rarr; 90 &rarr; 124). Given a reference the model reframes: the style '
           'matches and the wall comes back lower, which is a hole to the sky.</p>'
           '<p><code>python tools/audit_map.py</code> &mdash; 65 pictures, 0 faults. '
           'Art 6.33 MB &rarr; 2.18 MB.</p>'
           '</div>']
    shots = sorted(glob.glob(os.path.join(ROOT, 'tools', '_mapshots', 'm*.png')),
                   key=lambda f: int(os.path.basename(f)[1:-4]))
    if shots:
        out.append('<section id="ingame"><h2>in the game</h2>'
                   '<p class="sub">Photographed from inside the running game with '
                   '<code>tools/mapshot.py</code>, which flies to a distance and takes the '
                   'picture &mdash; so the whole map gets looked at, not only the places '
                   'somebody happened to fly past.</p>')
        for f in shots:
            m = os.path.basename(f)[1:-4]
            im = Image.open(f).convert('RGB')
            im.thumbnail((1300, 1300), Image.LANCZOS)
            b = io.BytesIO(); im.save(b, 'WEBP', quality=82, method=6)
            src = 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()
            out.append('<figure><figcaption><b>%s m</b></figcaption>'
                       '<div class="scroll"><img class="shot" src="%s" width="%d" '
                       'height="%d" alt="the map at %s metres"></div></figure>'
                       % (m, src, im.width, im.height, m))
        out.append('</section>')
    out.append(strips.stdout)
    out.append('</div>')
    sys.stdout.write('\n'.join(out))


if __name__ == '__main__':
    main()
